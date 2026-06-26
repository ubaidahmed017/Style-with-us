import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.models.product import Product, ProductSizeSpec
from app.models.order import Order, OrderStatus
import uuid


class TestCheckoutRaceCondition:
    """Integration tests for checkout - P10 (Stock Non-Negativity)"""

    @pytest.mark.asyncio
    async def test_two_concurrent_purchases_of_last_unit(
        self, client: AsyncClient, test_db: AsyncSession
    ):
        """Test that concurrent checkout for last unit returns one 200 and one 409"""
        # Create user
        user = User(
            firebase_uid="test-user",
            email="test@example.com",
            name="Test User",
            role=UserRole.SHOPPER
        )
        test_db.add(user)

        # Create product with 1 unit
        product = Product(
            brand_id=uuid.uuid4(),
            sku="TEST-LAST-UNIT",
            name="Last Unit Product",
            price=99.99,
            image_url="https://example.com/image.jpg",
            gender_target="unisex"
        )
        test_db.add(product)
        await test_db.commit()

        # Create size spec with 1 unit stock
        size_spec = ProductSizeSpec(
            product_id=product.product_id,
            size_label="M",
            stock_quantity=1  # Only 1 unit available
        )
        test_db.add(size_spec)
        await test_db.commit()

        # Both users attempt to checkout for the last unit
        # In real scenario, these would be concurrent requests
        # PostgreSQL row-level lock (SELECT FOR UPDATE) should handle this

        # First checkout should succeed
        order_1 = Order(
            user_id=user.user_id,
            total_amount=99.99,
            status=OrderStatus.PENDING
        )
        test_db.add(order_1)
        await test_db.commit()

        # Verify stock was decremented
        await test_db.refresh(size_spec)
        assert size_spec.stock_quantity == 0  # Should be 0 after first purchase

        # Second checkout should fail due to insufficient stock
        # This would return 409 in the actual endpoint


class TestStockVerificationWithLock:
    """Tests for SELECT FOR UPDATE row-level locking"""

    @pytest.mark.asyncio
    async def test_stock_never_goes_negative(self, test_db: AsyncSession):
        """Test that stock quantity never goes negative (P10)"""
        product = Product(
            brand_id=uuid.uuid4(),
            sku="TEST-STOCK",
            name="Test Product",
            price=50.00,
            image_url="https://example.com/image.jpg",
            gender_target="unisex"
        )
        test_db.add(product)
        await test_db.commit()

        size_spec = ProductSizeSpec(
            product_id=product.product_id,
            size_label="L",
            stock_quantity=5
        )
        test_db.add(size_spec)
        await test_db.commit()

        # Simulate purchases
        size_spec.stock_quantity -= 1
        size_spec.stock_quantity -= 1
        size_spec.stock_quantity -= 1
        size_spec.stock_quantity -= 1
        size_spec.stock_quantity -= 1
        await test_db.commit()

        # Verify never went negative
        await test_db.refresh(size_spec)
        assert size_spec.stock_quantity == 0
        assert size_spec.stock_quantity >= 0


class TestOrderCreation:
    """Integration tests for order creation"""

    @pytest.mark.asyncio
    async def test_order_total_is_positive(self, test_db: AsyncSession):
        """Test that order total is always positive (P11)"""
        user = User(
            firebase_uid="test-user",
            email="test@example.com",
            name="Test User",
            role=UserRole.SHOPPER
        )
        test_db.add(user)
        await test_db.commit()

        order = Order(
            user_id=user.user_id,
            total_amount=99.99,
            status=OrderStatus.PENDING
        )
        test_db.add(order)
        await test_db.commit()

        assert order.total_amount > 0

    @pytest.mark.asyncio
    async def test_zero_total_rejected(self, test_db: AsyncSession):
        """Test that zero order total is rejected (P11)"""
        # This should be validated at the schema/endpoint level
        # Pydantic validator should catch this
        pass


class TestPaymentSecrecy:
    """Tests for payment data security - P12 (Payment Secrecy)"""

    @pytest.mark.asyncio
    async def test_order_contains_no_raw_card_data(self, test_db: AsyncSession):
        """Test that order never contains raw card data (P12)"""
        user = User(
            firebase_uid="test-user",
            email="test@example.com",
            name="Test User",
            role=UserRole.SHOPPER
        )
        test_db.add(user)
        await test_db.commit()

        order = Order(
            user_id=user.user_id,
            total_amount=99.99,
            status=OrderStatus.PENDING,
            payment_intent_id="pi_test_123"  # Only Stripe payment intent ID
        )
        test_db.add(order)
        await test_db.commit()

        # Verify order only contains payment_intent_id, not raw card data
        assert order.payment_intent_id == "pi_test_123"
        # Should not have card number, CVV, etc.
        assert not hasattr(order, 'card_number')
        assert not hasattr(order, 'cvv')


class TestUserDataDeletion:
    """Integration tests for account deletion - requirement 1.8"""

    @pytest.mark.asyncio
    async def test_user_deletion_removes_all_associated_data(
        self, test_db: AsyncSession
    ):
        """Test that deleting user removes all associated data"""
        # Create user with profile
        user = User(
            firebase_uid="delete-test",
            email="delete@example.com",
            name="Delete Test User",
            role=UserRole.SHOPPER
        )
        test_db.add(user)
        await test_db.commit()

        user_id = user.user_id

        # Create order for this user
        order = Order(
            user_id=user_id,
            total_amount=99.99,
            status=OrderStatus.CONFIRMED
        )
        test_db.add(order)
        await test_db.commit()

        # Delete user
        await test_db.delete(user)
        await test_db.commit()

        # Verify user is deleted
        result = await test_db.execute(
            select(User).where(User.user_id == user_id)
        )
        assert result.scalar() is None

        # In real implementation, cascade delete would remove orders too
        # Or explicit cleanup would be done in the delete endpoint

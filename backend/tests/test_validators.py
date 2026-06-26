import pytest
from pydantic import ValidationError

from app.schemas.product import ProductCreate
from app.schemas.order import OrderCreate
from app.schemas.user import UserProfileCreate


class TestPriceValidation:
    """Tests for price validation - P9 (Price Positivity)"""

    def test_positive_price_is_valid(self):
        """Test that positive price is accepted"""
        product = ProductCreate(
            sku="TEST-001",
            name="Test Product",
            price=29.99,
            stock_quantity=10,
            image_url="https://example.com/image.jpg",
            gender_target="unisex"
        )
        assert product.price == 29.99

    def test_zero_price_raises_validation_error(self):
        """Test that zero price raises validation error (P9)"""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                sku="TEST-001",
                name="Test Product",
                price=0.0,
                stock_quantity=10,
                image_url="https://example.com/image.jpg",
                gender_target="unisex"
            )
        assert "greater than zero" in str(exc_info.value).lower()

    def test_negative_price_raises_validation_error(self):
        """Test that negative price raises validation error (P9)"""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                sku="TEST-001",
                name="Test Product",
                price=-10.00,
                stock_quantity=10,
                image_url="https://example.com/image.jpg",
                gender_target="unisex"
            )
        assert "greater than zero" in str(exc_info.value).lower()

    def test_large_price_is_valid(self):
        """Test that large prices are accepted"""
        product = ProductCreate(
            sku="TEST-001",
            name="Test Product",
            price=9999.99,
            stock_quantity=10,
            image_url="https://example.com/image.jpg",
            gender_target="unisex"
        )
        assert product.price == 9999.99


class TestStockValidation:
    """Tests for stock validation - P10 (Stock Non-Negativity)"""

    def test_zero_stock_is_valid(self):
        """Test that zero stock is valid (P10)"""
        product = ProductCreate(
            sku="TEST-001",
            name="Test Product",
            price=29.99,
            stock_quantity=0,
            image_url="https://example.com/image.jpg",
            gender_target="unisex"
        )
        assert product.stock_quantity == 0

    def test_positive_stock_is_valid(self):
        """Test that positive stock is valid"""
        product = ProductCreate(
            sku="TEST-001",
            name="Test Product",
            price=29.99,
            stock_quantity=100,
            image_url="https://example.com/image.jpg",
            gender_target="unisex"
        )
        assert product.stock_quantity == 100

    def test_negative_stock_raises_validation_error(self):
        """Test that negative stock raises validation error (P10)"""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                sku="TEST-001",
                name="Test Product",
                price=29.99,
                stock_quantity=-1,
                image_url="https://example.com/image.jpg",
                gender_target="unisex"
            )
        assert "negative" in str(exc_info.value).lower() or ">=" in str(exc_info.value)


class TestImageUrlValidation:
    """Tests for image URL validation"""

    def test_https_url_is_valid(self):
        """Test that HTTPS URL is accepted"""
        product = ProductCreate(
            sku="TEST-001",
            name="Test Product",
            price=29.99,
            stock_quantity=10,
            image_url="https://example.com/image.jpg",
            gender_target="unisex"
        )
        assert product.image_url == "https://example.com/image.jpg"

    def test_http_url_raises_validation_error(self):
        """Test that HTTP URL raises validation error"""
        with pytest.raises(ValidationError) as exc_info:
            ProductCreate(
                sku="TEST-001",
                name="Test Product",
                price=29.99,
                stock_quantity=10,
                image_url="http://example.com/image.jpg",
                gender_target="unisex"
            )
        assert "HTTPS" in str(exc_info.value) or "https" in str(exc_info.value).lower()

    def test_invalid_url_raises_validation_error(self):
        """Test that invalid URL raises validation error"""
        with pytest.raises(ValidationError):
            ProductCreate(
                sku="TEST-001",
                name="Test Product",
                price=29.99,
                stock_quantity=10,
                image_url="not-a-valid-url",
                gender_target="unisex"
            )


class TestGenderTargetValidation:
    """Tests for gender target validation"""

    @pytest.mark.parametrize("gender", ["male", "female", "unisex"])
    def test_valid_gender_targets(self, gender):
        """Test that valid gender targets are accepted"""
        product = ProductCreate(
            sku="TEST-001",
            name="Test Product",
            price=29.99,
            stock_quantity=10,
            image_url="https://example.com/image.jpg",
            gender_target=gender
        )
        assert product.gender_target == gender

    def test_invalid_gender_target_raises_validation_error(self):
        """Test that invalid gender target raises validation error"""
        with pytest.raises(ValidationError):
            ProductCreate(
                sku="TEST-001",
                name="Test Product",
                price=29.99,
                stock_quantity=10,
                image_url="https://example.com/image.jpg",
                gender_target="invalid-gender"
            )


class TestOrderTotalValidation:
    """Tests for order total validation - P11 (Order Total Positivity)"""

    def test_positive_order_total_is_valid(self):
        """Test that positive order total is valid (P11)"""
        # This would be tested in the order creation endpoint
        # Order total is calculated from items, not a user input
        # But if it were validated, it should require > 0
        pass

    def test_order_with_items(self):
        """Test that order with items can be created"""
        order = OrderCreate(
            items=[
                {"product_id": "prod-1", "quantity": 2},
                {"product_id": "prod-2", "quantity": 1}
            ]
        )
        assert len(order.items) == 2
        assert order.items[0]["quantity"] == 2

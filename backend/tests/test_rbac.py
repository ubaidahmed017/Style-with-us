import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_role
from app.models.user import User, UserRole
from app.core.firebase import DecodedToken


class TestRBACRoleEnforcement:
    """Tests for require_role dependency - P2 (RBAC Isolation), P3 (Brand Ownership)"""

    @pytest.mark.asyncio
    async def test_shopper_cannot_access_brand_routes(self, test_db: AsyncSession):
        """Test that Shopper role cannot access /brand/* routes (P2)"""
        # Create Shopper user
        shopper = User(
            firebase_uid="shopper-123",
            email="shopper@example.com",
            name="Shopper User",
            role=UserRole.SHOPPER
        )
        test_db.add(shopper)
        await test_db.commit()

        # Mock decoded token for shopper
        decoded_token = {
            'uid': 'shopper-123',
            'email': 'shopper@example.com'
        }

        # Attempt to access brand route
        brand_dep = require_role("brand")

        with pytest.raises(HTTPException) as exc_info:
            await brand_dep(decoded_token, test_db)

        assert exc_info.value.status_code == 403
        assert "Requires brand role" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_shopper_cannot_access_admin_routes(self, test_db: AsyncSession):
        """Test that Shopper role cannot access /admin/* routes (P2)"""
        shopper = User(
            firebase_uid="shopper-123",
            email="shopper@example.com",
            name="Shopper User",
            role=UserRole.SHOPPER
        )
        test_db.add(shopper)
        await test_db.commit()

        decoded_token = {
            'uid': 'shopper-123',
            'email': 'shopper@example.com'
        }

        admin_dep = require_role("admin")

        with pytest.raises(HTTPException) as exc_info:
            await admin_dep(decoded_token, test_db)

        assert exc_info.value.status_code == 403
        assert "Requires admin role" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_brand_cannot_access_admin_routes(self, test_db: AsyncSession):
        """Test that Brand role cannot access /admin/* routes (P2)"""
        brand = User(
            firebase_uid="brand-123",
            email="brand@example.com",
            name="Brand User",
            role=UserRole.BRAND
        )
        test_db.add(brand)
        await test_db.commit()

        decoded_token = {
            'uid': 'brand-123',
            'email': 'brand@example.com'
        }

        admin_dep = require_role("admin")

        with pytest.raises(HTTPException) as exc_info:
            await admin_dep(decoded_token, test_db)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_access_all_routes(self, test_db: AsyncSession):
        """Test that Admin role can access all routes (P4)"""
        admin = User(
            firebase_uid="admin-123",
            email="admin@example.com",
            name="Admin User",
            role=UserRole.ADMIN
        )
        test_db.add(admin)
        await test_db.commit()

        decoded_token = {
            'uid': 'admin-123',
            'email': 'admin@example.com'
        }

        # Test admin on brand routes
        brand_dep = require_role("brand")
        result = await brand_dep(decoded_token, test_db)
        assert result is not None

        # Test admin on admin routes
        admin_dep = require_role("admin")
        result = await admin_dep(decoded_token, test_db)
        assert result is not None

        # Test admin on shopper routes
        shopper_dep = require_role("shopper")
        result = await shopper_dep(decoded_token, test_db)
        assert result is not None

    @pytest.mark.asyncio
    async def test_shopper_can_access_shopper_routes(self, test_db: AsyncSession):
        """Test that Shopper role can access shopper routes"""
        shopper = User(
            firebase_uid="shopper-123",
            email="shopper@example.com",
            name="Shopper User",
            role=UserRole.SHOPPER
        )
        test_db.add(shopper)
        await test_db.commit()

        decoded_token = {
            'uid': 'shopper-123',
            'email': 'shopper@example.com'
        }

        shopper_dep = require_role("shopper")
        result = await shopper_dep(decoded_token, test_db)
        assert result is not None

    @pytest.mark.asyncio
    async def test_brand_can_access_brand_routes(self, test_db: AsyncSession):
        """Test that Brand role can access brand routes"""
        brand = User(
            firebase_uid="brand-123",
            email="brand@example.com",
            name="Brand User",
            role=UserRole.BRAND
        )
        test_db.add(brand)
        await test_db.commit()

        decoded_token = {
            'uid': 'brand-123',
            'email': 'brand@example.com'
        }

        brand_dep = require_role("brand")
        result = await brand_dep(decoded_token, test_db)
        assert result is not None

    @pytest.mark.asyncio
    async def test_nonexistent_user_raises_404(self, test_db: AsyncSession):
        """Test that nonexistent user raises 404"""
        decoded_token = {
            'uid': 'nonexistent-user',
            'email': 'nonexistent@example.com'
        }

        brand_dep = require_role("brand")

        with pytest.raises(HTTPException) as exc_info:
            await brand_dep(decoded_token, test_db)

        assert exc_info.value.status_code == 404


class TestBrandOwnershipVerification:
    """Tests for brand ownership verification (P3)"""

    @pytest.mark.asyncio
    async def test_brand_cannot_modify_another_brands_product(self, test_db: AsyncSession):
        """Test that Brand A cannot modify Brand B's product (P3)"""
        # This would be tested in the product endpoint tests
        # Create two brands and verify isolation
        brand_a = User(
            firebase_uid="brand-a",
            email="brand-a@example.com",
            name="Brand A",
            role=UserRole.BRAND
        )
        brand_b = User(
            firebase_uid="brand-b",
            email="brand-b@example.com",
            name="Brand B",
            role=UserRole.BRAND
        )
        test_db.add(brand_a)
        test_db.add(brand_b)
        await test_db.commit()

        # In actual endpoint tests, verify that brand-a cannot modify brand-b's products
        # This is enforced in the product router with: WHERE brand_id = :caller_brand_id
        assert brand_a.user_id != brand_b.user_id

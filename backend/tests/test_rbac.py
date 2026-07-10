"""RBAC tests for the real app.core.auth.require_role (P2/P3/P4).

Infra-free: require_role only needs `db.execute(stmt).scalar_one_or_none()`, so a
tiny fake session standing in for AsyncSession is enough to exercise the logic.
"""

import pytest
from fastapi import HTTPException

from app.core.auth import require_role, DecodedToken
from app.models import User, UserRole


class _FakeResult:
    def __init__(self, user):
        self._user = user

    def scalar_one_or_none(self):
        return self._user


class _FakeSession:
    """Returns the same user for any query (matches require_role's single lookup)."""

    def __init__(self, user):
        self._user = user

    async def execute(self, stmt):
        return _FakeResult(self._user)


def _user(role):
    return User(
        firebase_uid=f"{role.value}-123",
        email=f"{role.value}@example.com",
        name=f"{role.value} user",
        role=role,
    )


def _token(role):
    return DecodedToken(uid=f"{role.value}-123", email=f"{role.value}@example.com")


async def _call(required: UserRole, db_user_role: UserRole):
    dep = require_role(required)
    db = _FakeSession(_user(db_user_role) if db_user_role else None)
    return await dep(user=_token(required), db=db)


class TestRoleEnforcement:
    async def test_shopper_denied_brand(self):
        with pytest.raises(HTTPException) as exc:
            await _call(UserRole.BRAND, UserRole.SHOPPER)
        assert exc.value.status_code == 403

    async def test_shopper_denied_admin(self):
        with pytest.raises(HTTPException) as exc:
            await _call(UserRole.ADMIN, UserRole.SHOPPER)
        assert exc.value.status_code == 403

    async def test_brand_denied_admin(self):
        with pytest.raises(HTTPException) as exc:
            await _call(UserRole.ADMIN, UserRole.BRAND)
        assert exc.value.status_code == 403

    async def test_brand_allowed_brand(self):
        result = await _call(UserRole.BRAND, UserRole.BRAND)
        assert result is not None

    async def test_shopper_allowed_shopper(self):
        result = await _call(UserRole.SHOPPER, UserRole.SHOPPER)
        assert result is not None


class TestAdminBypass:
    """P4: admin passes every role gate."""

    @pytest.mark.parametrize("required", [UserRole.SHOPPER, UserRole.BRAND, UserRole.ADMIN])
    async def test_admin_bypasses_all(self, required):
        result = await _call(required, UserRole.ADMIN)
        assert result is not None


class TestMissingUser:
    async def test_unknown_user_404(self):
        dep = require_role(UserRole.BRAND)
        db = _FakeSession(None)
        with pytest.raises(HTTPException) as exc:
            await dep(user=_token(UserRole.BRAND), db=db)
        assert exc.value.status_code == 404

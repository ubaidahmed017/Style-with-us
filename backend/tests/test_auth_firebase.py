"""Tests for app.core.auth.verify_firebase_token (P1 Token Integrity).

We patch the token-verification helper that verify_firebase_token calls
(app.core.auth.verify_id_token) so we exercise the header parsing and error
mapping without needing real Firebase credentials.
"""

import pytest
from unittest.mock import patch
from fastapi import HTTPException

import app.core.firebase as firebase
from app.core.auth import verify_firebase_token, DecodedToken


@pytest.fixture(autouse=True)
def _disable_degraded_mode(monkeypatch):
    # Force full-verification behavior so the unverified-JWT dev fallback is off.
    monkeypatch.setattr(firebase, "DEGRADED_MODE", False)


class TestValidToken:
    async def test_valid_token_returns_decoded(self):
        with patch("app.core.auth.verify_id_token") as mock_verify:
            mock_verify.return_value = {"uid": "u-123", "email": "u@example.com"}
            result = await verify_firebase_token("Bearer valid-token")
        assert isinstance(result, DecodedToken)
        assert result.uid == "u-123"
        assert result.email == "u@example.com"


class TestMissingOrMalformed:
    async def test_missing_header_401(self):
        with pytest.raises(HTTPException) as exc:
            await verify_firebase_token(None)
        assert exc.value.status_code == 401
        assert "Missing" in exc.value.detail

    async def test_malformed_header_401(self):
        with pytest.raises(HTTPException) as exc:
            await verify_firebase_token("InvalidFormat")
        assert exc.value.status_code == 401


class TestTokenErrors:
    @pytest.mark.parametrize(
        "message,expected",
        [
            ("Token expired", "expired"),
            ("Token revoked", "revoked"),
            ("Invalid token", "invalid"),
        ],
    )
    async def test_error_mapping(self, message, expected):
        with patch("app.core.auth.verify_id_token") as mock_verify:
            mock_verify.side_effect = Exception(message)
            with pytest.raises(HTTPException) as exc:
                await verify_firebase_token("Bearer some-token")
        assert exc.value.status_code == 401
        assert expected in exc.value.detail.lower()

    async def test_random_string_401(self):
        with patch("app.core.auth.verify_id_token") as mock_verify:
            mock_verify.side_effect = Exception("not a jwt")
            with pytest.raises(HTTPException) as exc:
                await verify_firebase_token("Bearer garbage")
        assert exc.value.status_code == 401

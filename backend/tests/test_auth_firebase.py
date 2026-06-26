import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
import firebase_admin.auth as firebase_auth

from app.core.firebase import verify_firebase_token, DecodedToken


class TestFirebaseTokenVerification:
    """Tests for verify_firebase_token - P1 (Token Integrity)"""

    @pytest.mark.asyncio
    async def test_valid_token_returns_decoded_token(self, mock_decoded_token):
        """Test that valid Firebase token is decoded and returned"""
        with patch('app.core.firebase.firebase_admin.auth.verify_id_token') as mock_verify:
            mock_verify.return_value = {
                'uid': 'test-user-123',
                'email': 'test@example.com'
            }

            result = await verify_firebase_token('Bearer valid-token-xyz')

            assert result['uid'] == 'test-user-123'
            assert result['email'] == 'test@example.com'
            mock_verify.assert_called_once_with('valid-token-xyz', check_revoked=True)

    @pytest.mark.asyncio
    async def test_missing_authorization_header_raises_401(self):
        """Test that missing Authorization header raises HTTP 401"""
        with pytest.raises(HTTPException) as exc_info:
            await verify_firebase_token(None)

        assert exc_info.value.status_code == 401
        assert 'Missing' in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_malformed_authorization_header_raises_401(self):
        """Test that malformed Authorization header raises HTTP 401"""
        with pytest.raises(HTTPException) as exc_info:
            await verify_firebase_token('InvalidFormat')

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token_raises_401(self):
        """Test that expired Firebase token raises HTTP 401"""
        with patch('app.core.firebase.firebase_admin.auth.verify_id_token') as mock_verify:
            mock_verify.side_effect = firebase_auth.ExpiredIdTokenError('Token expired')

            with pytest.raises(HTTPException) as exc_info:
                await verify_firebase_token('Bearer expired-token')

            assert exc_info.value.status_code == 401
            assert 'expired' in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_revoked_token_raises_401(self):
        """Test that revoked Firebase token raises HTTP 401"""
        with patch('app.core.firebase.firebase_admin.auth.verify_id_token') as mock_verify:
            mock_verify.side_effect = firebase_auth.RevokedIdTokenError('Token revoked')

            with pytest.raises(HTTPException) as exc_info:
                await verify_firebase_token('Bearer revoked-token')

            assert exc_info.value.status_code == 401
            assert 'revoked' in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_invalid_token_signature_raises_401(self):
        """Test that invalid token signature raises HTTP 401"""
        with patch('app.core.firebase.firebase_admin.auth.verify_id_token') as mock_verify:
            mock_verify.side_effect = firebase_auth.InvalidIdTokenError('Invalid signature')

            with pytest.raises(HTTPException) as exc_info:
                await verify_firebase_token('Bearer invalid-signature-token')

            assert exc_info.value.status_code == 401
            assert 'Invalid' in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_random_string_raises_401(self):
        """Test that random non-JWT string raises HTTP 401 (P1)"""
        with patch('app.core.firebase.firebase_admin.auth.verify_id_token') as mock_verify:
            mock_verify.side_effect = firebase_auth.InvalidIdTokenError('Not a JWT')

            with pytest.raises(HTTPException) as exc_info:
                await verify_firebase_token('Bearer not-a-valid-jwt-string')

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_token_check_revoked_flag_is_true(self):
        """Test that check_revoked=True is passed to verify_id_token"""
        with patch('app.core.firebase.firebase_admin.auth.verify_id_token') as mock_verify:
            mock_verify.return_value = {'uid': 'test'}

            await verify_firebase_token('Bearer token')

            # Verify check_revoked=True was passed
            call_args = mock_verify.call_args
            assert call_args.kwargs['check_revoked'] is True


class TestTokenValidationErrorMessages:
    """Tests for distinct error messages (P1)"""

    @pytest.mark.asyncio
    async def test_distinct_error_for_missing_header(self):
        """Missing header should have distinct error message"""
        with pytest.raises(HTTPException) as exc:
            await verify_firebase_token(None)
        assert 'Missing' in exc.value.detail

    @pytest.mark.asyncio
    async def test_distinct_error_for_expired(self):
        """Expired token should have distinct error message"""
        with patch('app.core.firebase.firebase_admin.auth.verify_id_token') as mock_verify:
            mock_verify.side_effect = firebase_auth.ExpiredIdTokenError('Expired')
            with pytest.raises(HTTPException) as exc:
                await verify_firebase_token('Bearer expired')
            assert 'expired' in exc.value.detail.lower()

    @pytest.mark.asyncio
    async def test_distinct_error_for_revoked(self):
        """Revoked token should have distinct error message"""
        with patch('app.core.firebase.firebase_admin.auth.verify_id_token') as mock_verify:
            mock_verify.side_effect = firebase_auth.RevokedIdTokenError('Revoked')
            with pytest.raises(HTTPException) as exc:
                await verify_firebase_token('Bearer revoked')
            assert 'revoked' in exc.value.detail.lower()

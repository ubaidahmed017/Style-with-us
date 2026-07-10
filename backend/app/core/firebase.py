"""
Firebase initialization and configuration.
"""

import os
import re
import json
import firebase_admin
from firebase_admin import auth, credentials, messaging

# True when we could not load a real service-account key and are running in
# "verify-only" mode: ID-token signatures are still verified against Google's
# public keys, but revocation checks and custom-token minting are unavailable.
DEGRADED_MODE = False


def _extract_project_id(text: str):
    """Pull project_id out of a JSON blob even if the rest is unparseable."""
    if not text:
        return None
    m = re.search(r'"project_id"\s*:\s*"([^"]+)"', text)
    return m.group(1) if m else None


def _project_id_from_key_file():
    """Read project_id straight from the key file (survives a corrupt key)."""
    from app.core.config import BASE_DIR

    key_path = BASE_DIR / "firebase-key.json"
    if key_path.exists():
        return _extract_project_id(
            key_path.read_bytes().decode("utf-8-sig", errors="replace")
        )
    return None


def _make_verify_only_credential(project_id: str) -> credentials.Certificate:
    """Build a syntactically-valid throwaway service account.

    ID-token signature verification uses Google's PUBLIC certs plus the
    project_id (audience) and never touches this private key, so a generated
    key is sufficient to satisfy the SDK's init requirement.
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    return credentials.Certificate(
        {
            "type": "service_account",
            "project_id": project_id,
            "private_key_id": "verify-only",
            "private_key": pem,
            "client_email": f"verify-only@{project_id}.iam.gserviceaccount.com",
            "client_id": "0",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    )


# Initialize Firebase Admin SDK
def init_firebase():
    """Initialize Firebase Admin SDK.

    Prefers a real service-account credential. If that key is missing or
    corrupted, falls back to verify-only mode (see DEGRADED_MODE) so the API
    can still authenticate users in local development.
    """
    global DEGRADED_MODE
    if firebase_admin._apps:
        return firebase_admin.get_app()

    # config.py turns a "./firebase-key.json" path into the actual JSON string
    # (BOM-safe); it leaves "{}" if the key could not be parsed.
    from app.core.config import settings

    firebase_json = settings.firebase_service_account_json or os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_JSON", ""
    )

    # 1) Try a real credential — only if the value actually looks like a JSON
    #    object (not a leftover "./path" string or "{}").
    if firebase_json and firebase_json.strip().startswith("{") and firebase_json.strip() != "{}":
        try:
            cred = credentials.Certificate(json.loads(firebase_json))
            app = firebase_admin.initialize_app(cred)
            print("[FIREBASE] Initialized with a full service-account credential.")
            return app
        except Exception as e:
            print(f"[FIREBASE] Service-account key unusable ({e}).")

    # 2) Fall back to verify-only mode.
    project_id = (
        _extract_project_id(firebase_json)
        or _project_id_from_key_file()
        or settings.firebase_project_id
        or os.getenv("FIREBASE_PROJECT_ID")
    )
    if not project_id:
        raise ValueError(
            "Firebase not configured: no valid key and no project_id to fall back on"
        )

    app = firebase_admin.initialize_app(
        _make_verify_only_credential(project_id), {"projectId": project_id}
    )
    DEGRADED_MODE = True
    print(
        f"[FIREBASE] VERIFY-ONLY mode for project '{project_id}'. "
        "ID tokens are verified against Google's public keys, but revocation "
        "checks are DISABLED. Replace backend/firebase-key.json with a valid "
        "service-account key for full functionality. Do NOT use in production."
    )
    return app


# Initialize Firebase on module load
try:
    init_firebase()
except Exception as e:
    # Log but don't fail - might be running in a test environment
    print(f"Warning: Firebase initialization failed: {e}")


def verify_id_token(id_token: str, check_revoked: bool = True) -> dict:
    """
    Verify a Firebase ID token.

    Args:
        id_token: The Firebase ID token to verify
        check_revoked: Whether to check if token has been revoked

    Returns:
        Decoded token claims

    Raises:
        auth.ExpiredIdTokenError: If token is expired
        auth.RevokedIdTokenError: If token has been revoked
        auth.InvalidIdTokenError: If token is invalid
    """
    # Revocation checks require real service-account credentials, which we do
    # not have in verify-only mode. Signature verification still applies.
    if DEGRADED_MODE:
        check_revoked = False
    try:
        decoded = auth.verify_id_token(id_token, check_revoked=check_revoked)
        return decoded
    except auth.ExpiredIdTokenError:
        raise
    except auth.RevokedIdTokenError:
        raise
    except auth.InvalidIdTokenError:
        raise
    except Exception as e:
        raise auth.InvalidIdTokenError(f"Token verification failed: {str(e)}")


def send_fcm_notification(
    user_uid: str,
    title: str,
    body: str,
    data: dict = None
) -> bool:
    """
    Send a Firebase Cloud Messaging (FCM) notification to a user.

    Args:
        user_uid: Firebase UID of the user
        title: Notification title
        body: Notification body
        data: Optional custom data payload

    Returns:
        True if successful, False otherwise
    """
    try:
        # In production, FCM tokens would be stored in Firestore
        # This is a placeholder for the actual implementation
        pass
    except Exception as e:
        print(f"Error sending FCM notification: {e}")
        return False

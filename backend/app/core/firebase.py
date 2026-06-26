"""
Firebase initialization and configuration.
"""

import os
import json
import firebase_admin
from firebase_admin import auth, credentials, messaging

# Initialize Firebase Admin SDK
def init_firebase():
    """Initialize Firebase Admin SDK from environment variable."""
    if firebase_admin._apps:
        return firebase_admin.get_app()

    firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not firebase_json:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON environment variable not set")

    try:
        cred_dict = json.loads(firebase_json)
        cred = credentials.Certificate(cred_dict)
        app = firebase_admin.initialize_app(cred)
        return app
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
    except Exception as e:
        raise ValueError(f"Failed to initialize Firebase: {e}")


# Initialize Firebase on module load
try:
    init_firebase()
except ValueError as e:
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

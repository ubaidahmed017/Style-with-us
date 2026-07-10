"""Shared slowapi rate limiter.

Kept in its own module so routers can attach @limiter.limit(...) decorators
without importing app.main (which would be circular).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Keyed by client IP. Good enough for the demo's abuse protection; a per-user
# key would require decoding the Firebase token inside the key function.
limiter = Limiter(key_func=get_remote_address)

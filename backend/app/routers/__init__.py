"""
API route handlers package.
"""

from app.routers import users, auth, inventory, ml, payments, recommendations, admin

__all__ = [
    "users",
    "auth",
    "inventory",
    "ml",
    "payments",
    "recommendations",
    "admin",
]

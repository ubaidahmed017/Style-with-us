"""
API route handlers package.
"""

from app.routers import (
    users, inventory, ml, payments, recommendations, admin,
    reports, reviews, subscriptions, brand,
)

__all__ = [
    "users",
    "inventory",
    "ml",
    "payments",
    "recommendations",
    "admin",
    "reports",
    "reviews",
    "subscriptions",
    "brand",
]

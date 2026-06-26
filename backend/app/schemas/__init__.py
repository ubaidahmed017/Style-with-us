"""
Pydantic schemas package.
"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserResponse,
    UserProfileCreate,
    UserProfileResponse,
    BodyAnalysisResult,
)
from app.schemas.product import (
    ProductSizeSpecCreate,
    ProductSizeSpecResponse,
    ProductCreate,
    ProductResponse,
    BrandCreate,
    BrandResponse,
)
from app.schemas.order import (
    OrderItemCreate,
    OrderItemResponse,
    OrderCreate,
    OrderResponse,
    PaymentIntentRequest,
    PaymentIntentResponse,
)
from app.schemas.ml_job import (
    MLJobRequest,
    StyleAnalysisRequest,
    VirtualTryOnRequest,
    MLJobResponse,
    MLJobStatus,
    AIAnalysisResult,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserProfileCreate",
    "UserProfileResponse",
    "BodyAnalysisResult",
    # Product schemas
    "ProductSizeSpecCreate",
    "ProductSizeSpecResponse",
    "ProductCreate",
    "ProductResponse",
    "BrandCreate",
    "BrandResponse",
    # Order schemas
    "OrderItemCreate",
    "OrderItemResponse",
    "OrderCreate",
    "OrderResponse",
    "PaymentIntentRequest",
    "PaymentIntentResponse",
    # ML Job schemas
    "MLJobRequest",
    "StyleAnalysisRequest",
    "VirtualTryOnRequest",
    "MLJobResponse",
    "MLJobStatus",
    "AIAnalysisResult",
]

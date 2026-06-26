"""
Pydantic schemas for order and checkout endpoints.
"""

from typing import List
from uuid import UUID
from pydantic import BaseModel, field_validator
from app.models.enums import OrderStatus


class OrderItemCreate(BaseModel):
    """Schema for creating an order item."""
    product_id: UUID
    size_spec_id: UUID
    quantity: int = 1

    @field_validator("quantity")
    @classmethod
    def positive_quantity(cls, v: int) -> int:
        """Ensure quantity is positive."""
        if v <= 0:
            raise ValueError("quantity must be positive")
        return v


class OrderItemResponse(OrderItemCreate):
    """Schema for order item response."""
    item_id: UUID
    price_at_purchase: float

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    """Schema for creating an order."""
    items: List[OrderItemCreate]

    @field_validator("items")
    @classmethod
    def non_empty_items(cls, v: List[OrderItemCreate]) -> List[OrderItemCreate]:
        """Ensure at least one item in order."""
        if not v or len(v) == 0:
            raise ValueError("Order must contain at least one item")
        return v


class OrderResponse(BaseModel):
    """Schema for order response."""
    order_id: UUID
    user_id: UUID
    total_amount: float
    status: OrderStatus
    items: List[OrderItemResponse] = []
    created_at: str
    updated_at: str

    @field_validator("total_amount")
    @classmethod
    def positive_total(cls, v: float) -> float:
        """Ensure total amount is positive."""
        if v <= 0:
            raise ValueError("total_amount must be positive")
        return v

    class Config:
        from_attributes = True


class PaymentIntentRequest(BaseModel):
    """Schema for creating a Stripe payment intent."""
    items: List[OrderItemCreate]


class PaymentIntentResponse(BaseModel):
    """Schema for payment intent response."""
    client_secret: str
    order_id: UUID
    total_amount: float
    currency: str = "usd"

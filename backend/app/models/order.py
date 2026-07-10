"""
Order and OrderItem models for checkout.
"""

import uuid
from sqlalchemy import Column, String, Float, ForeignKey, Enum, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import OrderStatus


class Order(Base, TimestampMixin):
    """Purchase order."""

    __tablename__ = "orders"

    order_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    total_amount = Column(Float, nullable=False)  # Must be > 0
    status = Column(
        Enum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False
    )
    payment_intent_id = Column(String(255), nullable=True)  # Stripe payment intent ID

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_orders_user_id", "user_id"),
        Index("idx_orders_status", "status"),
    )


class OrderItem(Base):
    """Line item in an order."""

    __tablename__ = "order_items"

    item_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )
    order_id = Column(
        UUID(as_uuid=True),
        ForeignKey("orders.order_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.product_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    size_spec_id = Column(
        UUID(as_uuid=True),
        ForeignKey("product_size_specs.spec_id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    quantity = Column(Integer, default=1, nullable=False)
    price_at_purchase = Column(Float, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    __table_args__ = (
        Index("idx_order_items_order_id", "order_id"),
        Index("idx_order_items_product_id", "product_id"),
    )

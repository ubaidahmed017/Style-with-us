"""
Stripe payment and checkout endpoints.
"""

import stripe
import hmac
import hashlib
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models import User, Order, OrderItem, Product, ProductSizeSpec
from app.models.enums import OrderStatus
from app.schemas import PaymentIntentRequest, PaymentIntentResponse, OrderItemCreate
from app.core.config import settings

router = APIRouter(prefix="/payments", tags=["payments"])

# Configure Stripe
stripe.api_key = settings.stripe_secret_key


class PaymentWebhookEvent(BaseModel):
    """Stripe webhook event payload."""
    type: str
    data: dict


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: PaymentIntentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentIntentResponse:
    """
    Create a Stripe PaymentIntent for checkout.

    Verifies stock availability for all items before creating the intent.
    """
    from uuid import UUID

    if not request.items or len(request.items) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order must contain at least one item"
        )

    total_amount = 0.0
    order_items = []

    # Verify stock and calculate total
    for item in request.items:
        # Get product
        product_stmt = select(Product).where(Product.product_id == item.product_id)
        product_result = await db.execute(product_stmt)
        product = product_result.scalar_one_or_none()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found"
            )

        # Get size spec with a row-level lock (SELECT ... FOR UPDATE) so two
        # concurrent checkouts for the last unit can't both pass the stock check
        # (Requirement 10.7). The lock is held until this transaction commits.
        spec_stmt = (
            select(ProductSizeSpec)
            .where(ProductSizeSpec.spec_id == item.size_spec_id)
            .with_for_update()
        )
        spec_result = await db.execute(spec_stmt)
        size_spec = spec_result.scalar_one_or_none()

        if not size_spec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Size spec {item.size_spec_id} not found"
            )

        # Check stock
        if size_spec.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient stock for product {product.sku}"
            )

        item_total = product.price * item.quantity
        total_amount += item_total
        order_items.append((product, size_spec, item.quantity, product.price))

    if total_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order total must be greater than zero"
        )

    # Create the PaymentIntent. When a real Stripe secret key is configured we
    # call Stripe; otherwise (demo mode) we simulate an intent so checkout works
    # end-to-end without external payment credentials.
    from uuid import uuid4

    stripe_key = settings.stripe_secret_key or ""
    stripe_configured = stripe_key.startswith("sk_") and "..." not in stripe_key and len(stripe_key) > 20

    if stripe_configured:
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(total_amount * 100),  # Stripe uses cents
                currency="usd",
                metadata={"user_id": str(current_user.user_id)},
            )
            payment_intent_id = intent.id
            client_secret = intent.client_secret
        except stripe.error.StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Stripe error: {str(e)}",
            )
    else:
        payment_intent_id = f"pi_demo_{uuid4().hex}"
        client_secret = f"{payment_intent_id}_secret_demo"

    # In demo mode (no real Stripe) there is no webhook to confirm the order, so
    # we confirm on placement: the order counts toward brand earnings, commission
    # and admin revenue immediately, and stock is decremented now.
    order = Order(
        user_id=current_user.user_id,
        total_amount=total_amount,
        status=OrderStatus.PENDING if stripe_configured else OrderStatus.CONFIRMED,
        payment_intent_id=payment_intent_id,
    )
    db.add(order)
    await db.flush()  # Flush to get order.order_id without committing

    # Create OrderItems (and, in demo mode, decrement stock immediately).
    for product, size_spec, quantity, price_at_purchase in order_items:
        order_item = OrderItem(
            order_id=order.order_id,
            product_id=product.product_id,
            size_spec_id=size_spec.spec_id,
            quantity=quantity,
            price_at_purchase=price_at_purchase,
        )
        db.add(order_item)
        if not stripe_configured:
            size_spec.stock_quantity -= quantity

    await db.commit()

    return PaymentIntentResponse(
        client_secret=client_secret,
        order_id=order.order_id,
        total_amount=total_amount,
    )


@router.post("/webhook")
async def handle_stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Handle Stripe webhook events.

    Verifies webhook signature and updates order status on payment success.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # Verify webhook signature
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.stripe_webhook_secret
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload"
        )
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )

    # Handle payment_intent.succeeded event
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        payment_intent_id = payment_intent["id"]

        # Find order by payment_intent_id
        stmt = select(Order).where(Order.payment_intent_id == payment_intent_id)
        result = await db.execute(stmt)
        order = result.scalar_one_or_none()

        if order:
            # Update order status
            order.status = OrderStatus.CONFIRMED

            # Decrement stock for each item
            for item in order.items:
                # Get size spec
                spec_stmt = select(ProductSizeSpec).where(
                    ProductSizeSpec.spec_id == item.size_spec_id
                )
                spec_result = await db.execute(spec_stmt)
                size_spec = spec_result.scalar_one_or_none()

                if size_spec:
                    size_spec.stock_quantity -= item.quantity

            await db.commit()

    return {"status": "success"}

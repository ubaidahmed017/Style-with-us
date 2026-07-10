from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limit import limiter
from app.routers import (
    users, inventory, ml, payments, recommendations, admin,
    reports, reviews, subscriptions, brand,
)

app = FastAPI(title="Style With Us API", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = settings.allowed_origins.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(inventory.router)
app.include_router(ml.router)
app.include_router(payments.router)
app.include_router(recommendations.router)
app.include_router(admin.router)
app.include_router(reports.router)
app.include_router(reviews.router)
app.include_router(subscriptions.router)
app.include_router(brand.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

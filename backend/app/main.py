from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os

from app.core.config import settings
from app.routers import users, auth, inventory, ml, payments, recommendations, admin

limiter = Limiter(key_func=get_remote_address)

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
app.include_router(auth.router)
app.include_router(inventory.router)
app.include_router(ml.router)
app.include_router(payments.router)
app.include_router(recommendations.router)
app.include_router(admin.router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

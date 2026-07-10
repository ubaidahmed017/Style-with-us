# Style With Us - Quick Start Guide

> **Note:** This guide originally targeted a Windows dev box (`D:\ubaid\app\...`).
> The repo now lives at the current checkout root; replace any `D:\ubaid\app` path
> below with your repo root. For an accurate architecture + status overview, see
> [README.md](README.md).

## Project Status (target: working FYP demo)

- ✅ **Backend API**: core routers work (users, inventory, recommendations, payments, admin). ML endpoints are lightweight job records only (ML runs on-device).
- ✅ **Flutter Frontend**: all screens present; body analysis + size-fit + recommendations are real. Virtual/AR try-on and payment are **simulated** for the demo.
- ✅ **React Admin Portal**: implemented (Vite + React + TS), served at `/admin`.
- ✅ **Firebase**: project `style-with-us-49180` (backend falls back to verify-only mode without a service-account key).

---

## Prerequisites

Before starting, ensure you have installed:

- **Python 3.10+** - Backend framework
- **PostgreSQL 16** - Database
- **Redis 7** - Message broker
- **Flutter 3.x** - Mobile framework
- **Node.js 18+** (optional) - React admin portal

---

## Part 1: Start Backend Services (5 minutes)

### Step 1: Start PostgreSQL

```bash
# On Windows with PostgreSQL installed:
# PostgreSQL typically starts as a service automatically

# Verify it's running on port 5432:
psql -U postgres -h localhost -c "SELECT 1;"
```

### Step 2: Start Redis

```bash
# On Windows, if Redis is installed:
redis-server

# Or using WSL:
wsl redis-server
```

Verify Redis is running on port 6379:
```bash
redis-cli ping
# Should return: PONG
```

---

## Part 2: Run Backend Server (10 minutes)

```bash
# Navigate to backend directory
cd D:\ubaid\app\backend

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the server
python -m uvicorn app.main:app --reload

# Server will start at: http://localhost:8000
```

### Verify Backend is Running

Test health endpoint:
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

**Backend is now running and ready to accept requests!**

---

## Part 3: Configure Flutter for Firebase (10 minutes)

### Step 1: Download Firebase Configuration Files

1. Go to: **Firebase Console** → **Project Settings** → **Your Apps**
2. Select or create your app

**For Android:**
- Download `google-services.json`
- Place at: `D:\ubaid\app\FYP\android\app\google-services.json`

**For iOS (Optional):**
- Download `GoogleService-Info.plist`
- Place at: `D:\ubaid\app\FYP\ios\Runner\GoogleService-Info.plist`

### Step 2: Enable Firebase Services

In Firebase Console, enable these services:
- ✅ Authentication (Email/Password)
- ✅ Firestore Database
- ✅ Cloud Messaging (FCM)
- ✅ Storage

---

## Part 4: Run Flutter App (5 minutes)

```bash
# Navigate to Flutter project
cd D:\ubaid\app\FYP

# Get dependencies
flutter pub get

# List available devices/emulators
flutter devices

# Run on Android emulator or physical device
flutter run

# Or run on specific device
flutter run -d <device_id>
```

### Verify Flutter App

When the app starts, you should see:
1. ✅ Login screen loads
2. ✅ Can create account
3. ✅ Can sign in
4. ✅ Multi-step profile setup works
5. ✅ Can see product recommendations (if profile complete)

**Flutter app is now running!**

---

## Part 5: Test the Complete Flow (20 minutes)

### 1. User Registration & Profile Setup
```
1. Tap "Sign up"
2. Enter email, password, name
3. Select role: "Shopper"
4. Complete profile setup:
   - Select gender (required)
   - Select units (metric/imperial)
   - Enter height, weight, age
   - Enter body measurements (optional)
5. Confirm and proceed to home
```

### 2. Shopper Home Screen
```
1. View "Recommended for You" section (AI recommendations)
2. View "Browse All" section
3. See products with prices and try-on options
```

### 3. Virtual Try-On
```
1. Tap "Try On" on any product
2. Select photo from gallery
3. See simulated try-on result
4. Tap "Add to Cart"
```

### 4. Checkout
```
1. Tap shopping cart icon
2. Review order summary
3. Tap "Place Order"
4. See order confirmation
```

### 5. Brand Console
```
1. Log out
2. Sign up as "Brand" role
3. Access Brand Dashboard
4. Upload a product:
   - Fill in product details
   - Select gender target
   - Choose dominant color
   - Submit
5. View products in "My Products"
```

---

## Part 6: Backend API Testing (Optional)

### Test with cURL or Postman

```bash
# Get all products
curl -X GET http://localhost:8000/inventory/products \
  -H "Authorization: Bearer <firebase_id_token>"

# Create product (as brand)
curl -X POST http://localhost:8000/inventory/products \
  -H "Authorization: Bearer <firebase_id_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "TEST-001",
    "name": "Test Product",
    "price": 99.99,
    "stock_quantity": 50,
    "image_url": "https://example.com/image.jpg",
    "gender_target": "unisex"
  }'

# Get recommendations
curl -X GET http://localhost:8000/recommendations/outfits \
  -H "Authorization: Bearer <firebase_id_token>"
```

**Note:** You'll need a valid Firebase ID token. Get it from the Flutter app's network traffic or Firebase emulator.

---

## Part 7: Deployment to Production (Later)

### Docker Compose Setup

When ready for production:

```bash
cd D:\ubaid\app

# Start all services with Docker
docker-compose up -d

# Services will start:
# - PostgreSQL on port 5432
# - Redis on port 6379
# - FastAPI on port 8000
# - Nginx on ports 80/443 (reverse proxy)
```

### Environment Variables

Create `.env` file in `D:\ubaid\app\backend`:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/style_with_us
REDIS_URL=redis://localhost:6379
FIREBASE_SERVICE_ACCOUNT_JSON=<your_firebase_json>
STRIPE_SECRET_KEY=<your_stripe_key>
STRIPE_WEBHOOK_SECRET=<your_webhook_secret>
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8100
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│ Flutter Mobile App (Shopper, Brand)                    │
│ - Authentication (Firebase)                             │
│ - AI Recommendations (on-device ML)                     │
│ - Virtual Try-On (MediaPipe + OpenCV)                   │
│ - AR Try-On (Live camera overlay)                       │
│ - Shopping Cart & Checkout                              │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS
                     ↓
┌─────────────────────────────────────────────────────────┐
│ FastAPI Backend (D:\ubaid\app\backend)                  │
│ - Users Router (auth, profiles)                         │
│ - Inventory Router (products, sizes)                    │
│ - Recommendations Router (AI matching)                  │
│ - Payments Router (Stripe integration)                  │
│ - Admin Router (analytics, management)                  │
│ - ML Router (async job dispatch)                        │
└────────┬────────────────┬────────────────┬──────────────┘
         │                │                │
         ↓                ↓                ↓
    ┌─────────┐     ┌────────┐      ┌──────────┐
    │PostgreSQL│     │ Redis  │      │Firebase  │
    │  (5432)  │     │ (6379) │      │  Auth    │
    └─────────┘     └────────┘      └──────────┘
```

---

## Common Issues & Solutions

### Issue: "Connection refused" on port 5432
**Solution:** Start PostgreSQL service
```bash
# Windows:
net start postgresql-x64-16

# Or use pgAdmin to start the service
```

### Issue: "Connection refused" on port 6379
**Solution:** Start Redis
```bash
redis-server
```

### Issue: Flutter can't connect to backend
**Solution:** Check if backend is running
```bash
curl http://localhost:8000/health
```
If not working, restart backend:
```bash
# Stop with Ctrl+C, then restart
python -m uvicorn app.main:app --reload
```

### Issue: Firebase authentication failing
**Solution:** Verify google-services.json is in correct location
```
D:\ubaid\app\FYP\android\app\google-services.json
```

---

## Next Steps

### Immediate (This Week)
1. ✅ Backend running locally
2. ✅ Flutter app running on emulator/device
3. ✅ Test complete user flow
4. ✅ Test brand product upload

### Short Term (1-2 Weeks)
- [ ] React Admin Portal setup
- [ ] Integration testing
- [ ] Performance optimization
- [ ] Security audit

### Production (2-4 Weeks)
- [ ] Docker Compose deployment
- [ ] SSL/TLS certificates (Let's Encrypt)
- [ ] Database backups
- [ ] Monitoring & logging setup

---

## Support & Resources

**Backend Documentation:** See `D:\ubaid\app\backend\README.md`
**Flutter Documentation:** See `D:\ubaid\app\FYP\README.md`
**Firebase Documentation:** https://firebase.google.com/docs
**Flutter Docs:** https://flutter.dev/docs

---

## Project Statistics

| Component | Status | Lines of Code | Files |
|-----------|--------|-----------------|-------|
| Backend API | ✅ Complete | 1,500+ | 15+ |
| Flutter App | ✅ Complete | 2,000+ | 17+ |
| Database Schema | ✅ Complete | 300+ | 1 |
| Firebase Config | ✅ Complete | 50+ | 1 |
| **TOTAL** | **✅ READY** | **3,850+** | **34+** |

---

**Last Updated:** 2026-06-24
**Project:** Style With Us - AI-Powered Fashion Platform
**Status:** Ready for local testing and demonstration

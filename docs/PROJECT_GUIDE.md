# Style With Us — Complete Project Guide

> The single document to understand the whole system. Read top-to-bottom for a
> full mental model, or jump via the table of contents.

## Table of contents

1. [What it is & why](#1-what-it-is--why)
2. [System at a glance](#2-system-at-a-glance)
3. [Architecture](#3-architecture)
4. [Technology stack](#4-technology-stack)
5. [Repository structure](#5-repository-structure)
6. [Data model](#6-data-model)
7. [Backend API reference](#7-backend-api-reference)
8. [Roles & user flows](#8-roles--user-flows)
9. [Flutter app guide](#9-flutter-app-guide)
10. [Admin portal guide](#10-admin-portal-guide)
11. [Setup & running (Windows-first)](#11-setup--running-windows-first)
12. [Configuration](#12-configuration)
13. [Testing](#13-testing)
14. [Security](#14-security)
15. [Real vs simulated (demo scope)](#15-real-vs-simulated-demo-scope)
16. [Troubleshooting](#16-troubleshooting)
17. [Roadmap](#17-roadmap)

---

## 1. What it is & why

**Problem.** Online clothing returns are expensive and mostly caused by fit and
"looks different on me" surprises.

**Solution.** Style With Us combines:
- **On-device body analysis** — from a gallery photo, classify body shape and
  extract skin tone *on the phone* (privacy-first; the photo never leaves the device).
- **Personalized recommendations** — the server ranks products by gender, body
  shape, skin-tone palette, and whether the shopper's measurements fit an available size.
- **Size-based search & fit** — find products whose size specs cover your exact measurements.
- **Virtual & AR try-on** — see garments on your photo / live camera (demo-level compositing).
- **Brand console** — brands upload products with size specs and gender targeting.
- **Admin portal** — a web dashboard for platform analytics and management.

**Three roles:** Shopper and Brand share one Flutter app; Admin uses a separate web portal.

---

## 2. System at a glance

| Component | Path | Stack | Runs on |
|---|---|---|---|
| Mobile app | `FYP/` | Flutter, Riverpod, GoRouter, Firebase | Android / iOS / desktop / web |
| Backend API | `backend/` | FastAPI, SQLAlchemy async, PostgreSQL, Alembic | `:8000` |
| Admin portal | `admin-portal/` | React 18, Vite, TypeScript, Tailwind, React Query | `:5173/admin/` (dev) |
| Reverse proxy | `nginx/` | Nginx | `:80` (serves API + `/admin`) |
| Datastore | — | PostgreSQL 16 | `:5432` |
| Broker (future) | — | Redis 7 | `:6379` |

Ports: API `8000`, Postgres `5432`, Redis `6379`, admin dev server `5173`, Nginx `80`.

---

## 3. Architecture

```
 Flutter app (Shopper + Brand)                 React Admin Portal
  │  Firebase Auth → ID token                    │  Firebase Auth → ID token
  │  On-device ML (pose + palette)               │
  └──────────────── HTTPS (Bearer) ──────────────┴────────────┐
                                                               ▼
                                    ┌───────────────────────────────────┐
                                    │  FastAPI  (app/main.py)            │
                                    │  routers: users, inventory,        │
                                    │  recommendations, payments, ml,    │
                                    │  admin                             │
                                    │  auth: Firebase JWT verify + RBAC  │
                                    └───────────────┬───────────────────┘
                                                    ▼
                                    ┌───────────────────────────────────┐
                                    │  PostgreSQL (SQLAlchemy async)     │
                                    │  users, user_profiles, brands,     │
                                    │  products, product_size_specs,     │
                                    │  orders, order_items, ml_jobs      │
                                    └───────────────────────────────────┘
     External: Firebase Auth (token verification) · Stripe (demo-simulated)
```

**Request lifecycle:** client obtains a Firebase ID token → sends it as
`Authorization: Bearer <token>` → `verify_firebase_token` validates it →
`require_role` / `get_current_user` load the DB user → the endpoint runs a
parameterized async SQLAlchemy query → JSON response.

**ML placement:** all machine learning (body shape, skin tone, try-on) runs in
the Flutter client. The `/ml/*` endpoints only record job rows for auditing;
there are no server-side ML workers.

---

## 4. Technology stack

**Backend:** FastAPI, SQLAlchemy 2.0 (async) + asyncpg, Alembic, Pydantic v2,
`firebase-admin` (token verify + FCM), Stripe SDK, slowapi (rate limiting),
Celery/Redis (scaffold only), pytest + hypothesis.

**Mobile:** Flutter; Riverpod (state), GoRouter (routing), Firebase
(`firebase_auth`, `cloud_firestore`, `firebase_core`), Dio (HTTP),
`google_mlkit_pose_detection` + `palette_generator` (on-device ML), `camera` +
`image_picker`, `shared_preferences` (cart/orders/wishlist persistence),
`fl_chart`, `intl`, `uuid`.

**Admin:** React 18, Vite, TypeScript, Tailwind, React Query, Axios, Recharts, Firebase.

**Infra:** Docker Compose, Nginx, PostgreSQL 16, Redis 7.

---

## 5. Repository structure

```
Style-with-us/
├── README.md                     # Quick start + status
├── QUICKSTART.md                 # Legacy step-by-step (paths updated)
├── docs/PROJECT_GUIDE.md         # ← this document
├── docker-compose.yml            # postgres, redis, api, nginx
├── .env.example                  # backend env template
├── run_tests.sh                  # backend (+ flutter) test runner
├── nginx/nginx.conf              # reverse proxy + /admin static serving
│
├── .kiro/specs/style-with-us/    # requirements.md · design.md · tasks.md
│
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app, CORS, router mounting, /health
│   │   ├── core/
│   │   │   ├── config.py         # Settings (env), Firebase key loading
│   │   │   ├── database.py       # async engine + get_db dependency
│   │   │   ├── firebase.py       # Firebase init + verify_id_token (+ verify-only mode)
│   │   │   ├── auth.py           # verify_firebase_token, require_role, get_current_user
│   │   │   └── rate_limit.py     # shared slowapi limiter
│   │   ├── models/               # SQLAlchemy models + enums
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── routers/              # users, inventory, recommendations, payments, ml, admin
│   │   └── workers/celery_app.py # Celery scaffold (no tasks; ML is on-device)
│   ├── migrations/               # Alembic (001_initial_schema.py)
│   ├── tests/                    # pytest suites (see §13)
│   ├── requirements.txt
│   └── seed_admin.py             # CLI to seed an admin user
│
├── admin-portal/
│   └── src/                      # pages/, components/, context/, api.ts, firebase.ts
│
└── FYP/  (Flutter)
    └── lib/
        ├── main.dart             # app entry (Firebase init + ProviderScope)
        ├── core/
        │   ├── api_client.dart   # Dio client, auth interceptor, endpoint methods
        │   ├── router.dart       # GoRouter + auth redirect
        │   ├── theme.dart        # AppColors + dark theme
        │   └── providers/        # Riverpod notifiers (state layer)
        ├── shared/models/        # product_model.dart (Product, ProductSizeSpec, Brand)
        └── features/             # splash, auth, shopper, brand, admin screens
```

---

## 6. Data model

PostgreSQL, all IDs are UUIDs. Defined in `backend/app/models/`, created by
`migrations/versions/001_initial_schema.py`.

### Tables

| Table | Key columns | Notes |
|---|---|---|
| `users` | `user_id`, `firebase_uid` (unique), `email` (unique), `name`, `role` | `role ∈ {shopper, brand, admin}` |
| `user_profiles` | `profile_id`, `user_id` (unique FK), `gender` (required), measurements (cm/kg), `body_shape`, `skin_tone_hex`, `skin_tone_palette`, `unit_preference` | one per user; measurements stored in **metric** |
| `brands` | `brand_id`, `user_id` (unique FK), `company_name`, `logo_url` | one per brand user |
| `products` | `product_id`, `brand_id` FK, `sku` (unique), `name`, `price`, `image_url`, `garment_image_url`, `gender_target`, `dominant_color_hex` | |
| `product_size_specs` | `spec_id`, `product_id` FK, `size_label`, `stock_quantity`, chest/waist/hips/inseam/shoulder `_min`/`_max` (cm) | measurement ranges per size |
| `orders` | `order_id`, `user_id` FK, `total_amount`, `status`, `payment_intent_id` | `status ∈ {pending, confirmed, shipped, cancelled}` |
| `order_items` | `item_id`, `order_id` FK, `product_id` FK, `size_spec_id` FK, `quantity`, `price_at_purchase` | |
| `ml_jobs` | `job_id`, `user_id` FK, `job_type`, `status`, `input_image_url`, `result_url`, `product_id` | audit records only |

### Enums

`UserRole` (shopper/brand/admin) · `Gender` (male/female/**non_binary**) ·
`GenderTarget` (male/female/unisex) · `BodyShape` (hourglass/pear/apple/rectangle/inverted_triangle) ·
`SkinTonePalette` (warm_spring/warm_autumn/cool_summer/cool_winter/neutral_light/neutral_deep) ·
`UnitPreference` (metric/imperial) · `MLJobStatus` · `OrderStatus`.

### Relationships

`User 1—1 UserProfile` · `User 1—1 Brand` · `Brand 1—* Product` ·
`Product 1—* ProductSizeSpec` · `User 1—* Order` · `Order 1—* OrderItem` ·
`Product 1—* OrderItem` · `User 1—* MLJob`. User deletion cascades to profile,
brand, orders, and ML jobs.

---

## 7. Backend API reference

Base URL `http://localhost:8000`. All endpoints (except `/health` and
`/payments/webhook`) require `Authorization: Bearer <firebase_id_token>`.
Interactive docs at `/docs`.

### Users (`/users`)
| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/users/register` | any | Create/reconcile the DB user. Body `{role?, name?, company_name?}`. `role` may be `shopper`/`brand`; brand sign-up also creates the `Brand`. `admin` only via allowlist. |
| POST | `/users/brand` | brand/admin | Create/update the caller's brand (idempotent). |
| POST | `/users/profile` | any | Create or replace the profile (gender required). |
| GET | `/users/profile` | any | Get the caller's profile. |
| PATCH | `/users/profile` | any | Partial update — including on-device `body_shape`, `skin_tone_hex`, `skin_tone_palette`. |
| DELETE | `/users/me` | any | Delete the account and all associated data (204). |

### Inventory (`/inventory`)
| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/inventory/products` | brand | Create a product; accepts inline `size_specs[]`. |
| POST | `/inventory/products/{id}/sizes` | brand (owner) | Add a size spec to a product. |
| GET | `/inventory/products` | any | List/browse. Filters: `gender`, `size_label`, `chest`, `waist`, `hips`, `inseam`, pagination. Shoppers default to their gender. |
| GET | `/inventory/my-products` | brand | The caller brand's own products. |
| PUT | `/inventory/products/{id}` | brand (owner) | Update a product. |
| DELETE | `/inventory/products/{id}` | brand (owner) | Delete a product. |

### Recommendations (`/recommendations`)
| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/recommendations/outfits` | any (shopper) | Ranked product list by gender + body shape + skin-tone palette + size availability. Returns a flat JSON array. |

### Payments (`/payments`)
| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/payments/create-intent` | any | Verify stock (row-locked), create an `Order` (PENDING) + PaymentIntent. **Demo mode** (no Stripe key) returns a simulated `client_secret`. |
| POST | `/payments/webhook` | none (Stripe-signed) | On `payment_intent.succeeded`: mark order CONFIRMED, decrement stock. |

### ML (`/ml`)
| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/ml/style-analysis` | any | Record a style-analysis job (rate-limited 10/min). ML itself runs on-device. |
| POST | `/ml/virtual-tryon` | any | Record a try-on job (rate-limited 10/min). |
| GET | `/ml/jobs/{job_id}` | owner | Job status. |

### Admin (`/admin`, all require admin)
`GET /admin/analytics/overview` · `GET /admin/analytics/ml-jobs` ·
`GET /admin/analytics/sales-over-time?days=30` · `GET /admin/users` ·
`PATCH /admin/users/{id}?new_role=` · `GET /admin/brands` · `GET /admin/ml-jobs`.

### Health
`GET /health` → `{"status":"ok"}`.

### RBAC rules
- Missing/invalid token → 401. Wrong role → 403. Missing DB user → 404.
- **Admin bypasses all role checks.**
- Brands can only modify products where `product.brand_id == caller.brand_id`.

---

## 8. Roles & user flows

### Shopper
1. **Sign up** (role Shopper) → **profile setup** wizard: gender (required) →
   units → basic stats → measurements. Imperial inputs are converted to metric
   before saving.
2. **Home**: *Recommended for You* (needs a profile) + *Browse All* (search,
   gender chips). The profile is loaded from the backend on open, so it survives restarts.
3. **Body analysis** (optional): pick a photo → on-device pose + palette →
   confirm → only metrics are PATCHed to the profile → recommendations improve.
4. **Product detail**: AI size recommendation banner, size chips, add to cart,
   try-on entry points (gender-gated).
5. **Cart → checkout**: order summary → place order (demo payment) → recorded in order history.

### Brand
1. **Sign up** (role Brand) with a **company name** → backend creates the Brand row.
2. **Dashboard**: real stats (product count, total stock, out-of-stock) + quick actions.
3. **Upload product**: details + gender target + dominant color + **at least one
   size** (a built-in size chart fills the cm ranges) → `POST /inventory/products`.
4. **My Products**: real list with delete; edit is a stub.

### Admin
Uses the **web portal**. Logs in with an allowlisted email → dashboard
(overview cards, sales chart, ML donut), users (role changes), brands, ML jobs.
On mobile, admins see a redirect screen pointing to the portal.

---

## 9. Flutter app guide

### Entry & routing
- `main.dart` initializes Firebase and wraps the app in `ProviderScope`.
- `core/router.dart` — `GoRouter` with an auth redirect: unauthenticated →
  `/login`; authenticated → role home (`/shopper`, `/brand`, `/admin-redirect`).
  Routes: splash `/`, `/login`, `/signup`, `/profile-setup`, `/shopper` (+ `product/:id`,
  `orders`, `wishlist`, `try-on`, `ar-tryon`, `checkout`, `body-analysis`),
  `/brand` (+ `products`, `upload`, `analytics`), `/admin-redirect`.

### State (Riverpod, `core/providers/`)
| Provider | Type | Responsibility |
|---|---|---|
| `authProvider` | AsyncNotifier | Firebase sign-in/up/out; loads role from Firestore; calls `/users/register`. |
| `profileSetupProvider` | Notifier | Body profile; `submitProfile()`, `loadFromBackend()` (restore on app open). |
| `productsProvider` | AsyncNotifier | Catalog from `/inventory/products` (+ client filters); mock fallback if backend is down. |
| `recommendationsProvider` | AsyncNotifier | Parses `/recommendations/outfits` (flat list) into a group. |
| `cartProvider` | Notifier | Cart items, persisted to `SharedPreferences`. |
| `ordersProvider` | Notifier | Local order history, persisted. |
| `wishlistProvider` | Notifier | Favorites, persisted. |

### Networking — `core/api_client.dart`
Dio client. `baseUrl` is `String.fromEnvironment('API_BASE_URL', default 'http://localhost:8000')`
— override per platform (see §11). An interceptor attaches the Firebase ID
token and refresh-retries once on 401. Methods cover all backend endpoints the app uses.

### Screens (`features/`)
- **auth**: `login_screen` (routes by role), `signup_screen` (Shopper/Brand +
  company name for brands), `profile_setup_screen` (4-step wizard, imperial→metric).
- **shopper**: `home_screen`, `product_detail_screen` (AI fit), `body_analysis_screen`
  (real on-device ML), `virtual_tryon_screen` (simulated + gender gate),
  `ar_tryon_screen` (live pose + emoji overlay), `checkout_screen`,
  `order_history_screen`, `wishlist_screen`.
- **brand**: `brand_dashboard_screen` (real stats), `brand_products_screen`
  (real list + delete), `product_upload_screen` (with sizes), `brand_analytics_screen`
  (illustrative charts).
- **admin**: `admin_redirect_screen`. **splash**: `splash_screen`.

### Firebase setup (mobile)
The app calls `Firebase.initializeApp()`. Provide platform config:
`FYP/android/app/google-services.json` (Android) and/or run `flutterfire configure`.
Enable **Email/Password Auth** and **Firestore** in the Firebase console. The
backend's `FIREBASE_PROJECT_ID` should match the same project.

---

## 10. Admin portal guide

`admin-portal/` — Vite + React + TS, served under `/admin/`.
- `src/firebase.ts` — Firebase init from `VITE_FIREBASE_*` env (with placeholders).
- `src/api.ts` — Axios; base URL `VITE_API_BASE_URL || http://localhost:8000`;
  attaches the Firebase token; refresh-retries on 401.
- `src/context/AuthContext.tsx` — subscribes to Firebase auth; `POST /users/register`
  to fetch role; exposes `isAdmin`.
- Pages: `LoginPage`, `DashboardPage` (overview + sales `LineChart` + ML `PieChart`,
  30s refresh), `UsersPage` (role changes), `BrandsPage`, `MLJobsPage`.
- `ProtectedRoute` gates non-admins client-side (the backend enforces server-side).

---

## 11. Setup & running (Windows-first)

### Prerequisites
Python 3.10+, PostgreSQL 16 (or Docker), Node.js 18+, Flutter 3.x, a Firebase project.

### Backend
```powershell
cd backend
python -m venv .venv; .\.venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example .env      # edit values
docker compose up -d postgres  # or a local PostgreSQL
alembic upgrade head
uvicorn app.main:app --reload  # http://localhost:8000/docs
```
Seed an admin (optional): `python seed_admin.py admin@stylewithus.com <firebase_uid> "Admin"`,
or just list the email in `ADMIN_EMAILS` and log in once.

### Flutter (Windows)
```powershell
cd FYP
flutter pub get
flutter run -d windows                                   # desktop, uses localhost
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000  # Android emulator
```
| Target | `API_BASE_URL` |
|---|---|
| Windows/macOS/Linux desktop, web, iOS simulator | `http://localhost:8000` (default) |
| Android emulator | `http://10.0.2.2:8000` |
| Physical device | `http://<your-PC-LAN-IP>:8000` |

### Admin portal
```powershell
cd admin-portal; npm install; npm run dev   # http://localhost:5173/admin/
```
Optionally create `admin-portal/.env` with `VITE_API_BASE_URL` and `VITE_FIREBASE_*`.

### Docker (all-in-one)
```powershell
docker compose up -d    # postgres, redis, api (:8000), nginx (:80 → /admin + API)
```

---

## 12. Configuration

Backend settings resolve from `backend/.env` (see `.env.example`) and env vars
via `app/core/config.py`:

| Key | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | local Postgres | async DSN |
| `REDIS_URL` | localhost | reserved for future async work |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | `{}` | key JSON or `./firebase-key.json`; empty → verify-only |
| `FIREBASE_PROJECT_ID` | `style-with-us-49180` | used for verify-only token checks |
| `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` | placeholders | real key enables live Stripe; else demo mode |
| `ALLOWED_ORIGINS` | localhost:3000,5173 | CORS allowlist |
| `ADMIN_EMAILS` | `admin@stylewithus.com` | auto-admin allowlist |

Flutter: `--dart-define=API_BASE_URL=...`. Admin: `VITE_API_BASE_URL`, `VITE_FIREBASE_*`.

---

## 13. Testing

Backend tests live in `backend/tests/`. Most are **infra-free**; DB-backed
integration tests are gated behind `STYLEWITHUS_TEST_DATABASE_URL` (an async
Postgres DSN) because the schema uses Postgres-only types.

| File | Needs DB? | Covers |
|---|---|---|
| `test_validators.py` | no | Pydantic validators: price, HTTPS image, gender target, size ranges, order items, profile. |
| `test_properties.py` | no | Hypothesis: price positivity, stock non-negativity, size-range validity, alpha-blend & bbox invariants. |
| `test_rbac.py` | no | `require_role` P2/P3/P4 via a fake session. |
| `test_auth_firebase.py` | no | `verify_firebase_token`: valid/missing/malformed/expired/revoked/invalid. |
| `test_integration_checkout.py` | yes | Brand → product (inline sizes) → size search → my-products. |
| `test_integration_api.py` | yes | Profile CRUD + delete, recommendations, demo checkout, admin analytics, RBAC isolation. |

**Run (Windows):**
```powershell
cd backend
.\.venv\Scripts\python -m pytest -q            # infra-free (DB tests skip)

docker run -d --name swu-test-pg -e POSTGRES_PASSWORD=test -e POSTGRES_USER=test -e POSTGRES_DB=stylewithus_test -p 55432:5432 postgres:16-alpine
$env:STYLEWITHUS_TEST_DATABASE_URL="postgresql+asyncpg://test:test@localhost:55432/stylewithus_test"
.\.venv\Scripts\python -m pytest -q            # full suite
docker rm -f swu-test-pg
```
Latest run: **51 passed** with Postgres; **44 passed + 7 skipped** without.

Flutter tests: run `flutter test` in `FYP/` (add tests under `FYP/test/`).

---

## 14. Security

- **Auth:** every protected endpoint verifies the Firebase ID token. Without a
  service-account key the backend runs verify-only (signatures still checked;
  revocation checks disabled) — **do not use in production**.
- **RBAC:** role checks via `require_role`; admin bypass; brand ownership enforced at the query level.
- **Payments:** card data never touches the server; only `payment_intent_id` is
  stored. The webhook verifies the Stripe signature.
- **Input validation:** Pydantic v2 throughout; image URLs must be HTTPS and a
  supported format; SQLAlchemy parameterized queries only.
- **Rate limiting:** `/ml/*` limited to 10/min (slowapi).
- **Secrets:** `.env` and `firebase-key.json` are git-ignored. An earlier commit
  leaked a key file (`backend/...env`); it is now untracked — **rotate those keys**
  and consider purging git history.

---

## 15. Real vs simulated (demo scope)

| Feature | State |
|---|---|
| Auth, RBAC, profile, catalog, size search, recommendations, brand CRUD, admin analytics | **Real** |
| On-device body analysis (pose + skin tone) | **Real** (on device) |
| Size-fit recommendation | **Real** |
| Checkout | **Demo** — real order recorded; payment simulated when no Stripe key |
| Virtual try-on | **Simulated** — returns the input photo (no true compositing) |
| AR try-on | **Partly real** — live pose tracking; garment is an emoji overlay |
| Brand analytics charts | **Illustrative** — sample chart data |
| Server-side ML workers | **Not built** (ML is on-device by design) |

---

## 16. Troubleshooting

| Symptom | Fix |
|---|---|
| App shows only mock products | Backend not reachable at `API_BASE_URL`. On Android emulator use `10.0.2.2`. |
| `flutter pub get` fails on SDK constraint | Ensure Flutter ≥ 3.19 (Dart ≥ 3.5). |
| 401 on every request | Firebase not configured or token expired; check the Firebase project + `FIREBASE_PROJECT_ID`. |
| Brand can't upload products | Sign up *as Brand* (creates the Brand row) or call `POST /users/brand`. |
| Checkout fails with Stripe error | Leave `STRIPE_SECRET_KEY` as a placeholder to use demo mode, or set a valid test key. |
| `pytest` collects ROS/other plugins | Run with a clean `PYTHONPATH` (the repo's `pytest.ini` scopes to `tests/`). |
| Admin login says "not admin" | Add the email to `ADMIN_EMAILS` and log in again. |

---

## 17. Roadmap

- Real garment compositing for virtual try-on (OpenCV/canvas) and non-emoji AR overlays.
- Live Stripe checkout + webhook-driven order confirmation.
- Grouped recommendations (exact / similar / by-brand) end-to-end.
- Brand analytics from real order data; product edit screen.
- Test coverage for Flutter; CI pipeline; production TLS/deploy via Nginx.
- Secret rotation + git history purge of the previously-committed key.

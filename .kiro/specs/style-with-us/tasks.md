# Implementation Plan: Style With Us

## Overview

This plan implements the Style With Us AI-powered fashion platform in 13 sequential task groups. The work progresses from infrastructure and database setup through authentication, feature development (catalog, cart, ML pipelines, AR try-on, checkout, admin), testing, and final production deployment. Each task group depends on the ones listed in the dependency graph below.

**Architecture decisions reflected in this plan:**
- **AI Model:** HuggingFace pretrained ViT/ResNet model for body shape classification (loaded via `transformers` pipeline) + Stone library for skin tone + MediaPipe for virtual try-on pose estimation
- **Mobile app:** Single Flutter app for Shopper and Brand roles (role-based routing via GoRouter)
- **Admin portal:** Separate React + TypeScript web application (`admin-portal/`) consuming the same FastAPI backend

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": [1] },
    { "wave": 2, "tasks": [2] },
    { "wave": 3, "tasks": [3] },
    { "wave": 4, "tasks": [4, 5, 6, 7, 10] },
    { "wave": 5, "tasks": [8, 9, 13] },
    { "wave": 6, "tasks": [11] },
    { "wave": 7, "tasks": [12] }
  ]
}
```

## Tasks

- [x] 1. Project Infrastructure and DevOps Setup
  - **The Flutter mobile project already exists at `d:\ubaid\app\FYP` (package name: `fyp`). Do NOT create a new Flutter project. All Flutter work happens inside this existing folder.**
  - Create the following folder structure inside `d:\ubaid\app\FYP\lib\`:
    - `lib/core/` — router, theme, constants, di
    - `lib/features/auth/` — login, signup, profile_setup
    - `lib/features/shopper/` — home, ai_analysis, virtual_tryon, ar_tryon, cart, checkout
    - `lib/features/brand/` — dashboard, product_upload, product_edit
    - `lib/shared/` — widgets, models, services, utils
  - Replace `d:\ubaid\app\FYP\pubspec.yaml` dependencies section with all required packages: `flutter_riverpod: ^2.5.0`, `go_router: ^13.0.0`, `firebase_core: ^3.0.0`, `firebase_auth: ^5.0.0`, `cloud_firestore: ^5.0.0`, `firebase_messaging: ^15.0.0`, `flutter_stripe: ^10.1.0`, `dio: ^5.4.0`, `cached_network_image: ^3.3.0`, `camera: ^0.10.0`, `image_picker: ^1.1.0`, `flutter_animate: ^4.5.0`, `lottie: ^3.1.0`, `glassmorphism: ^3.0.0`, `google_mlkit_pose_detection: ^0.10.0`, `palette_generator: ^0.3.0`, `opencv_dart: ^1.0.0`, `shared_preferences: ^2.3.0`
  - Run `flutter pub get` inside `d:\ubaid\app\FYP` to install all dependencies
  - Create the React Admin Portal project at `d:\ubaid\app\admin-portal\`: `npm create vite@latest . -- --template react-ts` then install: `axios`, `react-router-dom`, `recharts`, `@tanstack/react-query`, `tailwindcss`, `postcss`, `autoprefixer`, `firebase`
  - Create the FastAPI backend at `d:\ubaid\app\backend\` with folder structure: `app/main.py`, `app/routers/`, `app/models/`, `app/schemas/`, `app/workers/`, `app/core/`
  - Create `d:\ubaid\app\backend\requirements.txt` with pinned versions: `fastapi==0.111.*`, `uvicorn[standard]==0.29.*`, `sqlalchemy[asyncio]==2.0.*`, `asyncpg==0.29.*`, `alembic==1.13.*`, `celery[redis]==5.3.*`, `redis==5.0.*`, `firebase-admin==6.5.*`, `stripe==9.0.*`, `Pillow==10.3.*`, `mediapipe==0.10.*`, `opencv-python-headless==4.9.*`, `stone==2.0.*`, `pydantic==2.7.*`, `slowapi==0.1.*`, `python-multipart==0.0.9.*`, `httpx==0.27.*`, `pytest==8.0.*`, `hypothesis==6.100.*`
  - Create `d:\ubaid\app\docker-compose.yml` with services: `postgres:16` (port 5432), `redis:7-alpine` (port 6379), `api` (backend on port 8000), `worker-style` (Celery concurrency=4), `worker-tryon` (Celery concurrency=2), `nginx:1.25` (ports 80/443, serves React admin at `/admin`)
  - Create `d:\ubaid\app\.env.example` with: `DATABASE_URL`, `REDIS_URL`, `FIREBASE_SERVICE_ACCOUNT_JSON`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STORAGE_BUCKET_URL`, `ALLOWED_ORIGINS`
  - Configure `slowapi` rate limiter in `app/main.py` (10 req/min per user on `/ml/*`)
  - Configure FastAPI `CORSMiddleware` with explicit origin allowlist
  - Set up Nginx config for HTTPS termination, reverse proxy, gzip, static admin build at `/admin`
  - _Requirements: 12.5, 12.6, 13.5, 13.7_

- [ ] 2. Database Schema and Migrations
  - Implement SQLAlchemy ORM models in `app/models/`:
    - `User` (user_id UUID PK, firebase_uid unique index, name, email unique, role Enum, created_at)
    - `UserProfile` (profile_id UUID PK, user_id FK unique, gender Enum(`male|female|non_binary`) NOT NULL, height_cm Float, weight_kg Float, age Int, chest_cm Float, waist_cm Float, hips_cm Float, inseam_cm Float, shoulder_width_cm Float, skin_tone_hex String, skin_tone_palette Enum, body_shape Enum, unit_preference Enum, updated_at)
    - `Brand` (brand_id UUID PK, user_id FK unique, company_name, logo_url)
    - `Product` (product_id UUID PK, brand_id FK, sku unique, name, description, price Float, image_url, garment_image_url, gender_target Enum(`male|female|unisex`) NOT NULL, dominant_color_hex String nullable)
    - `ProductSizeSpec` (spec_id UUID PK, product_id FK, size_label String, stock_quantity Int, chest_min/max Float, waist_min/max Float, hips_min/max Float, inseam_min/max Float nullable, shoulder_min/max Float nullable — all in cm)
    - `Order` (order_id UUID PK, user_id FK, total_amount Float, status Enum, payment_intent_id, created_at)
    - `MLJob` (job_id UUID PK, user_id FK, job_type, status Enum, error_message, created_at, updated_at)
  - Define all Enum types: `UserRole`, `Gender`, `GenderTarget`, `MLJobStatus`, `OrderStatus`, `BodyShape`, `SkinTonePalette`, `UnitPreference`
  - Add database indexes: unique on `users.firebase_uid`; index on `products.brand_id`; index on `products.gender_target`; composite index on `product_size_specs(product_id, size_label)`; range query index on size measurement columns; index on `user_profiles.user_id`
  - Configure Alembic async migrations; generate and apply initial migration
  - Implement `AsyncSession` database dependency: `pool_size=10, max_overflow=20`
  - Write Pydantic v2 schemas: `price_must_be_positive`, `validate_image_url`, `size_ranges_valid`, `unit_conversion` helpers, `gender_required` validator ensuring gender is always set on UserProfile
  - _Requirements: 1.1a, 8.1, 8.2, 9.3, 9.8_

- [ ] 3. Firebase Authentication, RBAC Middleware, and Shopper Profile Setup
  - Initialize `firebase_admin` in `app/core/firebase.py` using `FIREBASE_SERVICE_ACCOUNT_JSON` environment variable
  - Implement `verify_firebase_token` dependency: parse `Authorization: Bearer <token>`, call `firebase_admin.auth.verify_id_token(token, check_revoked=True)`, raise HTTP 401 for missing/malformed/expired/revoked tokens with distinct messages
  - Implement `require_role(required_role: str)` RBAC dependency factory: look up `db_user.role` from PostgreSQL, raise HTTP 403 if mismatch, Admin users bypass all role checks
  - Implement `POST /users/register` endpoint: verify token, create `User` record in PostgreSQL, return `{user_id, role}`
  - Implement `POST /users/profile` endpoint: accept `UserProfileCreate` (height_cm, weight_kg, age, chest_cm, waist_cm, hips_cm, inseam_cm, shoulder_width_cm, skin_tone_hex optional, body_shape optional, unit_preference); upsert into `UserProfile` table; return `UserProfileResponse`
  - Implement `GET /users/profile` endpoint: return the calling user's `UserProfile` record
  - Implement `PATCH /users/profile` endpoint: partial update of any UserProfile fields
  - Implement `DELETE /users/me` endpoint: delete User, UserProfile, and all associated data; return HTTP 204 (for account deletion privacy requirement)
  - Implement Flutter `AuthNotifier` (Riverpod `AsyncNotifier`): `signIn()`, `signUp()`, `signOut()`; `signUp()` writes `{role, name, email}` to Firestore `users/{uid}`
  - Build multi-step Flutter Shopper Profile Setup flow (`lib/features/auth/profile_setup/`):
    - **Step 0 – Gender (mandatory, no skip):** Three-button selector: Male / Female / Non-binary. Cannot proceed to home screen without selecting gender.
    - Step 1 – Units: Metric (cm/kg) or Imperial (inches/lbs) toggle
    - Step 2 – Basic stats: height, weight, age (inputs labelled in chosen unit)
    - Step 3 – Body measurements: chest/bust, waist, hips, inseam, shoulder width (inputs with illustrated measurement guide diagram, "Skip for now" allowed)
    - On submit: convert imperial → cm/kg if needed, call `POST /users/profile` with gender + measurements, navigate to home
  - Configure Dio interceptor: attach `Authorization: Bearer {idToken}`; catch HTTP 401, refresh token, retry once
  - Configure GoRouter with `authGuard` redirect: unauthenticated → `/login`; Shopper → `/shopper`; Brand → `/brand`; Admin on mobile → `/admin-redirect` (shows "Use the web portal at [URL]")
  - Show one-time privacy notice on first launch of analysis/try-on features: "Your photos are analyzed on your device only and are never uploaded."
  - _Requirements: 1.1, 1.1a, 1.1b, 1.1c, 1.1d, 1.2–1.8, 12.8, 12.10_

- [ ] 4. Brand Console, Product Catalog, and Product Sizing
  - Implement `POST /inventory/products` endpoint with `require_role("brand")`: require `gender_target` (`male|female|unisex`); validate price > 0, garment_image_url is HTTPS and PNG/WebP; set `brand_id` from calling user; return HTTP 201
  - Implement `POST /inventory/products/{product_id}/sizes` endpoint: add size spec with label + cm measurement ranges; validate `min <= max`; return HTTP 201
  - Implement `GET /inventory/products` endpoint: paginated (default 20); supports `?gender=male|female|unisex` filter (defaults to caller's gender for Shopper), `?size_label=M` filter, and `?chest=96&waist=78&hips=100` custom measurement filter; returns products + all size specs
  - Implement `GET /recommendations/outfits` endpoint:
    - Read `UserProfile` (gender, body_shape, skin_tone_palette, waist_cm, hips_cm, chest_cm)
    - Filter by gender_target first
    - Apply body-shape style rules (gender-specific: pear female→A-line; pear male→tapered trousers; etc.)
    - Filter by skin tone complementary color palette (match against `product.dominant_color_hex`)
    - For each matching product: check if a size spec exists covering the user's measurements → mark as "exact match"
    - Products with exact match AND color match → Section A top results
    - Products with color match but no size → "Similar styles" fallback group
    - Group brands: for items matching on both color and size across multiple brands → return `{brand: {logo, name}, products: [...]}` structure
  - Implement `PUT/DELETE /inventory/products/{product_id}` with brand ownership enforcement
  - Build Flutter Brand Dashboard UI: product list with gender_target badge per product; `ProductUploadScreen` with gender_target selector (Male / Female / Unisex), **dominant color picker** (a simple color swatch grid of 16 common garment colors — user picks the closest match; stored as hex e.g. `#E63946`; used by recommendation engine for skin-tone color matching), size spec table with cm range inputs and measurement guide tooltip; unit toggle on size table
  - _Requirements: 8.1–8.7, 3.1–3.7, 4.1–4.5_

- [ ] 5. Shopper Home Screen — Two-Section Layout, Size Search, and Cart
  - Build Flutter Shopper Home Screen (`lib/features/shopper/home_screen.dart`) with two clearly separated sections:
    - **Section A — "Recommended for You"** (top, scrollable horizontal cards):
      - Visible only when `UserProfile.gender` is set
      - Fetched from `GET /recommendations/outfits`
      - Sub-sections: "Exact Match" (color + size + gender), "Similar Styles" (color match, size unavailable), "By Brand" (collapsible brand cards, each showing brand logo + matching products listed beneath)
      - Each card shows: product image, name, price, "Why recommended" label (e.g., "A-line · Warm autumn · Your size"), "Fits your size" or "Similar size available" badge
      - If no profile: show "Set up your profile" prompt card with CTA button
    - **Section B — "Browse All"** (below, full paginated grid, always visible):
      - Text search bar
      - Gender filter chip row (defaults to user's gender, overridable)
      - Size Filter panel (expandable): Tab 1 — size labels (XS/S/M/L/XL/XXL chips); Tab 2 — custom measurements (chest/waist/hips/inseam fields in user's preferred unit); "Use my size" auto-fill button
      - Products show "Fits your measurements" badge if user profile matches a size spec
      - Each card has: image, name, price, brand, "Try On" button, "Add to Cart" button
  - Implement `RecommendationNotifier` (Riverpod): fetches and caches `GET /recommendations/outfits`; invalidates when UserProfile changes
  - Implement `SizeFilterNotifier` (Riverpod): holds active label + custom measurement filters
  - Implement `CartNotifier`: `addItem(Product, sizeSpecId)` — prompts size selector if not chosen; `removeItem`; `clearCart()`; persist to `shared_preferences`
  - _Requirements: 6.1–6.7, 9.1, 9.7_

- [ ] 6. On-Device Body Analysis, Skin Tone, and Outfit Recommendation
  - Add Flutter dependencies for on-device analysis to `pubspec.yaml`: `google_mlkit_pose_detection ^0.10` (MediaPipe Pose on-device), `palette_generator ^0.3` (skin tone color extraction from image region)
  - Implement `BodyAnalysisService` in `lib/features/shopper/ai_analysis/body_analysis_service.dart`:
    - `analyzePhoto(File photo) -> BodyAnalysisResult` — runs entirely on-device, never calls network
    - Step 1: Use `google_mlkit_pose_detection` to extract pose landmarks from the selected image
    - Step 2: Assert key torso landmarks present (LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP); throw `PoseNotDetectedError` if visibility < 0.3
    - Step 3: Compute measurements in pixel-space ratios, then scale to cm using the user's stored height as a reference scale factor: `real_cm = pixel_measurement / image_height_px * user_height_cm`
    - Step 4: Compute body shape from ratios: shoulder-to-hip ratio, waist-to-hip ratio → classify into `hourglass`, `pear`, `apple`, `rectangle`, `inverted_triangle`
    - Step 5: Use `palette_generator` to sample skin tone from the face/neck region of the image → extract dominant hex color
    - Step 6: Map hex to seasonal palette: `warm_spring`, `warm_autumn`, `cool_summer`, `cool_winter`, `neutral_light`, `neutral_deep`
    - Step 7: Return `BodyAnalysisResult(bodyShape, skinToneHex, seasonalPalette, computedMeasurements)` — no network call made yet
    - Step 8: After user confirms results, ONLY THEN call `PATCH /users/profile` with computed metrics (NOT the photo)
    - Step 9: Clear photo from memory after analysis
  - Implement skin tone color recommendation logic on the server (`app/routers/recommendations.py`):
    - `GET /recommendations/outfits` endpoint: reads `UserProfile.body_shape` + `UserProfile.skin_tone_hex` + `UserProfile.waist_cm` etc.; queries products with matching body-shape style rules AND complementary color products; returns ranked list
    - Body shape rules: pear→A-line/flared; hourglass→wrap/fitted; apple→empire waist/flowy; rectangle→ruffles/layered; inverted_triangle→wide-leg/flared bottom
    - Skin tone color matching: map seasonal palette to complementary hue ranges; filter `products` where brand-tagged product color falls in the range
  - Build Flutter AI Analysis UI (`lib/features/shopper/ai_analysis/`):
    - `AIAnalysisScreen`: image picker + one-time privacy notice (first use only); "Analyze" button
    - On analysis: show on-device progress indicator (no spinner waiting for server); display result immediately: body shape label + illustration, skin tone swatch + seasonal palette name
    - "Update my profile" button calls `PATCH /users/profile` with the results
    - Recommended outfits carousel loaded from `GET /recommendations/outfits` (server-side, uses stored profile)
    - Each card shows "Why recommended" label: e.g., "A-line cut for pear shape · Warm autumn color"
  - _Requirements: 2.1–2.9, 3.1–3.5, 4.1–4.5_

- [ ] 7. On-Device Virtual Try-On Pipeline
  - Add Flutter OpenCV FFI dependency: `opencv_dart ^1.0` (wraps OpenCV for Flutter via FFI — no server needed)
  - Implement `VirtualTryOnService` in `lib/features/shopper/virtual_tryon/virtual_tryon_service.dart`:
    - `generateTryOn(File userPhoto, String garmentImageUrl) -> File resultImage` — entirely on-device
    - Step 1: Load user photo into memory as a `ui.Image`
    - Step 2: Run `google_mlkit_pose_detection` on the user photo to extract torso landmarks
    - Step 3: Assert LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP all have visibility >= 0.3; throw `PoseNotDetectedError` if not
    - Step 4: Compute bounding box (x1, y1, x2, y2) in pixel coords from landmark positions; assert `x1 >= 0, y1 >= 0, x2 <= W, y2 <= H, width > 0, height > 0`
    - Step 5: Download the garment's transparent PNG (`garment_image_url`) from CDN — this is the ONLY network call; the user photo is NOT uploaded
    - Step 6: Use `opencv_dart` to resize garment PNG to bounding box dimensions
    - Step 7: Alpha-blend garment onto user photo using OpenCV `addWeighted`; assert all output pixels in [0, 255]
    - Step 8: Assert result image dimensions equal input photo dimensions
    - Step 9: Encode result as JPEG (quality 92) and return as a `File` in the device's temporary directory
    - Step 10: Clear source photo from memory after compositing
  - Build Flutter Virtual Try-On UI (`lib/features/shopper/virtual_tryon/`):
    - `VirtualTryOnScreen`: selected product card at top; gallery image picker
    - **Gender gate check before opening picker:** if `product.gender_target = male` AND `user.gender ≠ male` (and not non-binary) → show bottom sheet: "This item is designed for male shoppers" with close button. Same for female. Unisex → always open.
    - Show on-device progress indicator while compositing
    - On result: full-screen composite image viewer with "Save to Gallery", "Share", and "Add to Cart" buttons
    - On `PoseNotDetectedError`: show error with retry
    - On screen close: clear photo and result from memory
  - _Requirements: 5.1–5.8_

- [ ] 8. AR Live Try-On (On-Device)
  - Configure Flutter `camera` package: request camera permissions in `AndroidManifest.xml` and `Info.plist`
  - Implement `ARTryOnScreen`: initialize `CameraController` (front-facing, `ResolutionPreset.high`), display live feed via `CameraPreview`, wrap in `RepaintBoundary`
  - Implement `GarmentOverlayPainter` (`CustomPainter`): draw selected garment image at computed torso bounding box position on each frame
  - Run on-device MediaPipe pose inference in a background Flutter `Isolate`: process camera frames, send keypoints to main isolate via `SendPort`/`ReceivePort`, update `poseKeypointsProvider` (Riverpod)
  - Implement garment carousel at bottom of `ARTryOnScreen`: top recommended garments from latest style analysis; selecting updates `selectedGarmentProvider` and re-renders overlay
  - Handle no-pose detection: WHEN no pose detected for > 2 seconds THEN display overlay banner "Step back for a full-body view" without crashing
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [~] 9. Checkout and Payment
  - Implement `POST /payments/create-intent` endpoint: verify token; for each item query `SELECT stock_quantity FROM products WHERE product_id = :id FOR UPDATE`; return HTTP 409 on insufficient stock; compute total_amount (assert > 0); call `stripe.PaymentIntent.create(amount, currency)`; insert Order with status PENDING and payment_intent_id; return `PaymentIntentResponse(client_secret, order_id, total_amount)`
  - Implement `POST /payments/webhook` endpoint: no auth middleware; verify with `stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)` — return HTTP 400 on failure; on `payment_intent.succeeded` update Order to CONFIRMED and decrement stock quantities; return HTTP 200
  - Build Flutter Checkout Screen: order summary display; call `POST /payments/create-intent`; render `CardField` from `flutter_stripe` (card data never leaves Stripe SDK); on "Pay" call `Stripe.instance.confirmPayment(clientSecret)`; on success clear cart and navigate to confirmation; on failure display Stripe error with retry
  - _Requirements: 9.2–9.8_

- [ ] 10. Admin Backend API
  - Implement all admin backend endpoints in `app/routers/admin.py`, protected with `require_role("admin")`:
    - `GET /admin/analytics/overview` → `{total_users, total_brands, total_orders, total_revenue, active_ml_jobs}`
    - `GET /admin/analytics/ml-jobs` → `{queued: int, processing: int, completed: int, failed: int}`
    - `GET /admin/analytics/sales-over-time` → array of `{date, revenue}` for the last 30 days
    - `GET /admin/users` → paginated list with `{user_id, name, email, role, created_at}`
    - `PATCH /admin/users/{user_id}` → allow role updates (Admin only)
    - `GET /admin/brands` → paginated list of brands with product counts
  - Ensure all admin endpoints are included in the CORS allowlist for the React portal's origin
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  - Write unit tests for `verify_firebase_token`: valid token → DecodedToken; expired → HTTP 401; revoked → HTTP 401; malformed/random string → HTTP 401; missing header → HTTP 401
  - Write unit tests for `require_role`: Shopper on `/brand/*` → 403; Brand on `/admin/*` → 403; Admin on any role-restricted route → allowed; Brand on other brand's product → 403
  - Write unit tests for `overlay_garment` parametrized over full-image bounding box, small centered box, with/without alpha channel — assert output shape equals input shape and pixels outside bounding box are unchanged
  - Write property-based tests using `hypothesis`: P16 (bounding box validity for any normalized keypoints), P17 (alpha blend output in [0,255] for any alpha and pixel values), P9 (price validator rejects all non-positive floats), P1 (verify_firebase_token raises 401 for any non-JWT string)
  - Write integration tests using `pytest` + `httpx.AsyncClient` + `testcontainers`: full ML job lifecycle end-to-end; checkout race condition (two concurrent requests for last unit — one 200, one 409); RBAC end-to-end; Stripe webhook valid/invalid signature; brand product isolation
  - Write Flutter unit tests: `CartNotifier` state transitions; `AuthNotifier` success/failure/signOut; `TryOnNotifier` polling terminates on COMPLETED and FAILED
  - Verify P5 (State Monotonicity): test that forcing a COMPLETED/FAILED job back to QUEUED is rejected at the database level
  - _Requirements: 1.1–9.7 (all correctness properties)_

- [ ] 13. React Admin Portal UI
  - Set up Tailwind CSS and React Router in `admin-portal/`: configure `tailwind.config.ts`, add `BrowserRouter` in `main.tsx`, configure `axios` base URL pointing to FastAPI backend
  - Implement Firebase Auth login in the admin portal: `LoginPage` with email/password form using `signInWithEmailAndPassword`; on successful login verify the user's role is `admin` by calling `GET /users/me`; redirect to dashboard if admin, show error if not
  - Implement `apiClient.ts`: Axios instance that auto-attaches `Authorization: Bearer {idToken}` header (refresh token on 401 using Firebase `getIdToken(forceRefresh: true)`)
  - Build `DashboardPage` (default route `/`):
    - Overview stat cards: Total Users, Total Brands, Total Orders, Total Revenue — fetched from `GET /admin/analytics/overview` using React Query
    - `SalesChart`: Recharts `LineChart` showing revenue over last 30 days from `GET /admin/analytics/sales-over-time`; auto-refreshes every 30 seconds via React Query `refetchInterval`
    - `MLQueueWidget`: Shows QUEUED / PROCESSING / COMPLETED / FAILED counts as colour-coded badges from `GET /admin/analytics/ml-jobs`; refreshes every 30 seconds
  - Build `UsersPage` (route `/users`):
    - Paginated data table of all users with columns: Name, Email, Role, Joined
    - Role filter dropdown (All / Shopper / Brand / Admin)
    - Inline role-change dropdown per row — calls `PATCH /admin/users/{user_id}` on change with confirmation dialog
  - Build `BrandsPage` (route `/brands`):
    - Table listing all brands with company name, logo, and product count from `GET /admin/brands`
  - Add `Navbar` component with links to Dashboard, Users, Brands; show logged-in admin email and Logout button
  - Add `ProtectedRoute` wrapper: redirects unauthenticated users to `/login`
  - Build production bundle: `npm run build` outputs to `admin-portal/dist/`; configure Nginx to serve `dist/` at `/admin` path
  - _Requirements: 10.1–10.5_

- [ ] 11. Testing and QA
  - Write unit tests for `verify_firebase_token`: valid/expired/revoked/malformed/missing → correct HTTP responses
  - Write unit tests for `require_role`: cross-role access attempts all return 403; admin bypasses all
  - Write unit tests for `ProductSizeSpec` range validator: `min <= max` enforced for all measurement pairs; all values > 0
  - Write unit tests for size search query: given `waist=78, hips=98` returns only products where at least one spec satisfies both range conditions
  - Write unit tests for unit conversion helpers: inches↔cm, lbs↔kg — round-trip conversions preserve values within 0.1% tolerance
  - Write property-based tests using `hypothesis`: P_SEARCH_RANGE (size search includes/excludes correctly), P_UNIT_CONSISTENCY (metric→imperial→metric round trip), P17 (alpha blend in [0,255]), P16 (bounding box validity for any normalized keypoints)
  - Write Flutter unit tests: `BodyAnalysisService` body shape ratio computation for all 5 shapes; `VirtualTryOnService` — assert no Dio request contains image data (privacy invariant); `CartNotifier` with size spec tracking; `SizeFilterNotifier` with label/measurement/combined modes
  - Write integration tests using `pytest` + `httpx.AsyncClient` + `testcontainers`: size search end-to-end; checkout race condition on last unit of a size spec; UserProfile upsert stores cm regardless of input unit; brand isolation for size specs; account deletion removes all user data
  - _Requirements: all correctness properties_

- [ ] 12. UI Polish and Production Deployment
  - Apply glassmorphism styling consistently (product cards, dashboard panels, modal sheets)
  - Integrate `flutter_animate` page transitions: fade-in on product grid, slide-up on cart add, shimmer skeletons on load
  - Add Lottie animations: on-device analysis processing, empty states, payment success
  - Add illustrated body measurement diagram to profile setup Step 3 (chest, waist, hips, inseam, shoulder width)
  - Conduct performance profiling: verify 60 FPS in Flutter DevTools; confirm AR try-on and on-device try-on maintain 60 FPS; load test API with `locust` (50 concurrent users, non-ML endpoints < 2s)
  - Generate final Alembic migration and test against clean PostgreSQL container
  - Configure production environment variables: `FIREBASE_SERVICE_ACCOUNT_JSON`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `DATABASE_URL`, `REDIS_URL`, `ALLOWED_ORIGINS`
  - Smoke test full system: registration + profile setup; brand product upload with size specs; size-based search; on-device body analysis → profile update → recommendations refresh; on-device virtual try-on; checkout end-to-end; admin portal analytics
  - _Requirements: 11.1, 11.3, 11.4_

## Notes

- Tasks 4, 5, 6, 7, and 10 can be worked on in parallel after Task 3 is complete.
- Tasks 8, 9, and 13 run in parallel in Wave 5.
- All ML (body analysis, skin tone, virtual try-on, AR try-on) runs entirely on the user's device. No raw photos ever leave the device. Only computed metrics are sent to the server.
- The `google_mlkit_pose_detection` package provides on-device MediaPipe Pose for Flutter on both Android and iOS without any server dependency.
- Unit conversions (inches/lbs ↔ cm/kg) are done client-side before calling the backend; the database always stores metric values.
- The React Admin Portal is in `admin-portal/`, authenticates via Firebase Auth, and is served by Nginx at `/admin`.
- The Flutter mobile app serves both Shopper and Brand in one binary. Admin users on mobile see a redirect to the web portal.
- All secrets must be managed via environment variables — never hardcoded or committed to source control.

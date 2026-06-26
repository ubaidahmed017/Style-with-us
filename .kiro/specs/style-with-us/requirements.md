# Requirements Document

## Introduction

Style With Us is an AI-powered fashion-tech platform that enables shoppers to visualize clothing on their own bodies before purchasing, reducing online retail return rates. The system combines on-device body shape classification, on-device skin tone analysis, server-side personalized outfit recommendations, size-based product search, and on-device virtual garment compositing into a unified mobile experience. It serves three distinct roles — Shopper, Brand Partner, and System Admin — each with dedicated interfaces and strict access controls.

**Privacy-first design:** All user photos are processed exclusively on the user's device using on-device MediaPipe and color analysis. Raw photos never leave the device. Only computed metrics (body shape classification, body measurements in cm, skin tone hex) are transmitted to the server. Virtual Try-On compositing also runs entirely on-device.

---

## Glossary

| Term | Definition |
|---|---|
| **On-Device Analysis** | Body shape classification and skin tone extraction performed entirely on the user's device using MediaPipe Pose Estimation. Raw photos never leave the device. |
| **Body Metrics** | The extracted numeric data from on-device analysis: shoulder width (cm), bust (cm), waist (cm), hips (cm), inseam (cm), skin tone hex. These — not the photo — are sent to the server. |
| **Body Shape** | One of five classifications derived from body measurement ratios: `hourglass`, `pear`, `apple`, `rectangle`, `inverted_triangle` |
| **Skin Tone** | A hex color string (e.g., `#C68642`) representing the user's dominant skin tone, used for outfit color recommendations |
| **Virtual Try-On** | A composited image of the user wearing a selected garment, generated entirely on-device using MediaPipe Pose Estimation + OpenCV Flutter FFI. No photo is uploaded. |
| **AR Try-On** | A real-time live camera feed overlay that composites a 2D garment onto the user's body using on-device MediaPipe |
| **Outfit Recommendation** | Server-side engine that matches products to a user's body shape + skin tone + saved measurements, returning a ranked product list |
| **Size Search** | Filtering products by either standard size label (XS/S/M/L/XL/XXL) or custom measurements entered by the user (e.g., waist 78cm, chest 96cm) |
| **Product Size Spec** | A brand's product size entry: a size label (e.g., M) mapped to measurement ranges (chest 92–96cm, waist 74–78cm, hips 98–102cm, inseam 76cm) |
| **User Profile** | Shopper's stored data: height (cm or inches), weight (kg or lbs), age, chest, waist, hips, inseam, shoulder width, preferred unit system (metric/imperial) |
| **ML Job** | An asynchronous server-side task (outfit recommendation query). Status: QUEUED → PROCESSING → COMPLETED/FAILED |
| **RBAC** | Role-Based Access Control — three roles: Shopper, Brand Partner, System Admin |
| **SKU** | Stock Keeping Unit — unique identifier for a product variant |
| **Firebase UID** | The unique user identifier issued by Firebase Authentication |
| **PaymentIntent** | A Stripe object representing a payment lifecycle; the server stores only the `payment_intent_id`, never raw card data |
| **FCM** | Firebase Cloud Messaging — push notification service |
| **Confidence Score** | A float in [0.0, 1.0] representing certainty of body shape classification |

---

## Requirements

### Requirement 1: User Authentication, Role-Based Access, and Shopper Profile

**User Story:** As a new Shopper, I want to register with my email, choose my role, enter my gender, and provide my body measurements during sign-up, so that the app can immediately show gender-appropriate clothing and personalized size recommendations.

#### Acceptance Criteria

1. WHEN a user submits a registration form with a valid email, password, and a selected role (Shopper, Brand, or Admin), THEN the system SHALL create a Firebase Auth account and store `{uid, role, name, email}` in Firestore under `users/{uid}`.

1a. WHEN a Shopper completes the initial account creation step, THEN the system SHALL present a multi-step "Body Profile" setup screen with the following steps in order:
   - **Step 0 – Gender:** Select Male, Female, or Non-binary (required; cannot be skipped)
   - **Step 1 – Units:** Select Metric (cm/kg) or Imperial (inches/lbs)
   - **Step 2 – Basic stats:** Height, weight, age
   - **Step 3 – Measurements:** Chest/bust, waist, hips, inseam, shoulder width (with illustrated measurement guide diagram)

1b. WHEN a Shopper submits their body profile, THEN the system SHALL persist these values to the `UserProfile` table in PostgreSQL including `gender` (required), and display a confirmation before proceeding to the home screen.

1c. WHEN a Shopper selects "metric" as their preferred unit system, THEN all measurements SHALL be stored in centimetres and kilograms internally; WHEN "imperial" is selected, THEN values SHALL be converted to cm/kg before storage and displayed back in the user's chosen unit throughout the app.

1d. WHEN a Shopper skips Steps 1–3, THEN the system SHALL allow them to proceed but SHALL NOT allow them to skip Step 0 (gender is mandatory). The system SHALL prompt completion of remaining steps from the Settings screen before using AI features or size-based search.

1e. WHEN a Shopper views or edits their profile, THEN gender SHALL be editable from the Settings screen and any change SHALL immediately re-filter all AI recommendations and try-on eligibility.

1d. WHEN a Shopper skips the body profile setup, THEN the system SHALL allow them to proceed to the home screen and prompt them to complete their profile from the Settings screen before using AI analysis or size-based search.

2. WHEN a user logs in with valid credentials, THEN the system SHALL verify the Firebase ID token server-side, retrieve the user's role from Firestore, and redirect them to their role-specific dashboard (Shopper → `/shopper`, Brand → `/brand`, Admin → `/admin`).

3. WHEN a user with role "Shopper" attempts to access any route under `/brand/*` or `/admin/*`, THEN the system SHALL return HTTP 403 and deny access.

4. WHEN a user with role "Brand" attempts to access any route under `/admin/*`, THEN the system SHALL return HTTP 403 and deny access.

5. WHEN a user with role "Admin" accesses any protected route, THEN the system SHALL grant access regardless of the role restriction on that route.

6. WHEN a Firebase ID token has expired, THEN the Flutter client SHALL automatically refresh the token using `getIdToken(forceRefresh: true)` and transparently retry the failed request without user intervention.

7. WHEN a request arrives at any protected backend endpoint without a valid `Authorization: Bearer <token>` header, THEN the system SHALL return HTTP 401 with an error message.

8. IF a Brand user attempts to modify a product, THEN the system SHALL verify that `product.brand_id == caller.brand_id` and return HTTP 403 if they do not match.

### Correctness Properties

- **P1 (Token Integrity):** For all requests to protected endpoints, a request is processed if and only if the Firebase token is cryptographically valid, non-expired, and non-revoked at time of processing.
- **P2 (RBAC Isolation):** For all users with role "Shopper," no request to `/brand/*` or `/admin/*` shall succeed.
- **P3 (Brand Ownership):** For all Brand users `b` and products `p`: `b` can modify `p` only if `p.brand_id == b.brand_id`.
- **P4 (Admin Bypass):** For all users with role "Admin," access is granted to all endpoints in all role groups.

---

## Requirement 2: On-Device Body Analysis (Privacy-First)

**User Story:** As a Shopper, I want to analyze my body shape and skin tone from a photo that never leaves my device, so that I can get personalized recommendations while keeping my photos completely private.

#### Acceptance Criteria

1. WHEN a Shopper selects a photo from their gallery on the AI Analysis screen, THEN the photo SHALL be processed exclusively on the device using on-device MediaPipe Pose Estimation — the raw photo SHALL NOT be transmitted to any server at any point.

2. WHEN on-device MediaPipe Pose Estimation processes the photo, THEN the system SHALL extract the following normalized landmark positions: LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP, LEFT_KNEE, RIGHT_KNEE; and compute pixel-space measurements for shoulder width, bust estimate, waist estimate, and hip width.

3. WHEN body landmarks are extracted, THEN the system SHALL compute the body shape classification on-device using measurement ratios (shoulder-to-hip ratio, waist-to-hip ratio, waist-to-shoulder ratio) and map the result to one of five classes: `hourglass`, `pear`, `apple`, `rectangle`, or `inverted_triangle` without any network call.

4. WHEN body shape is classified, THEN the system SHALL run on-device skin tone analysis using the image's facial/skin region pixel sampling and return a dominant skin tone hex color (e.g., `#C68642`) — this analysis also runs entirely on-device with no photo upload.

5. WHEN on-device analysis completes, THEN the system SHALL display the body shape result and skin tone swatch to the user immediately (< 3 seconds on mid-range devices) before any network call is made.

6. WHEN the user confirms or accepts the on-device results, THEN the system SHALL transmit ONLY the computed metrics to the server: `{body_shape, skin_tone_hex, shoulder_width_cm, bust_cm, waist_cm, hips_cm}` — never the raw image.

7. WHEN the server receives the metrics, THEN the system SHALL update the user's `UserProfile` record with the computed measurements and return personalized outfit recommendations.

8. IF MediaPipe cannot detect sufficient pose landmarks (visibility < 0.3 for any key torso landmark), THEN the system SHALL display an on-device error: "Please use a clear, well-lit, full-body photo" and NOT transmit any data to the server.

9. WHEN the analysis screen is closed or the app is backgrounded, THEN the photo loaded for analysis SHALL be cleared from memory — the system SHALL NOT cache or persist the raw photo anywhere on the device beyond the analysis session.

### Correctness Properties

- **P_PRIVACY (Photo Never Leaves Device):** For all body analysis sessions, zero bytes of raw image data are transmitted to any network endpoint.
- **P_ONDEVICE (Local Classification):** Body shape and skin tone classification results are computed entirely from on-device MediaPipe output; no ML inference request is made to the server.
- **P13 (Confidence Bounds):** For all body shape classification results, `confidence_score ∈ [0.0, 1.0]`.

---

## Requirement 3: Skin Tone Outfit Color Recommendation

**User Story:** As a Shopper, I want the app to recommend outfit colors that complement my skin tone and match my gender and size, so that I discover clothes that look genuinely flattering and actually fit me.

#### Acceptance Criteria

1. WHEN a Shopper's skin tone hex is available, THEN the system SHALL map the hex to one of six seasonal palettes: `warm_spring`, `warm_autumn`, `cool_summer`, `cool_winter`, `neutral_light`, `neutral_deep`.

2. WHEN the recommendation engine runs, THEN it SHALL filter products by the Shopper's `gender_target` first (male → `male|unisex`, female → `female|unisex`, non-binary → all), THEN filter by skin-tone complementary color palette, THEN rank by size availability (products with a matching size spec for the user's measurements rank higher).

3. WHEN a Shopper's exact size is available in a recommended color, THEN the system SHALL show those products first with a "Your size available" badge.

4. WHEN a Shopper's exact size is NOT available in any product of the recommended color, THEN the system SHALL show a "Similar styles" section with visually similar products in available sizes rather than showing nothing.

5. WHEN the same recommended product (matching color + size) is available from multiple brands, THEN the system SHALL group results by brand — each brand shown as a collapsible section header with its logo and the matching outfits listed beneath it.

6. WHEN a Shopper has not completed on-device analysis, THEN the system SHALL offer a manual skin tone selector (6–8 swatches) for color recommendations without photo upload.

7. WHEN a Shopper updates their skin tone or gender, THEN the recommendation feed SHALL refresh automatically.

### Correctness Properties

- **P_COLORMAP:** For all skin tone hex values, the system returns a palette label from the defined set of 6 palettes.
- **P_GENDER_FILTER:** No product with `gender_target = female` appears in recommendations for a Male Shopper, and vice versa.

---

## Requirement 4: Body Shape Outfit Recommendation

**User Story:** As a Shopper, I want outfit recommendations based on my body shape and gender, so that I find styles that flatter my figure and are designed for my gender.

#### Acceptance Criteria

1. WHEN the recommendation engine runs, THEN it SHALL apply gender filter first, THEN body-shape-specific style rules: pear → A-line/flared (female) or tapered trousers (male); hourglass → wrap/fitted (female) or slim-fit (male); apple → empire waist/flowy (female) or relaxed-fit tops (male); rectangle → ruffles/layered (female) or structured blazers (male); inverted_triangle → wide-leg/flared bottom (female) or slim trousers (male).

2. WHEN the recommendation engine combines body shape AND skin tone, THEN it SHALL produce a single unified ranked list — not two separate feeds. Both signals are used together to rank results.

3. WHEN a product card is displayed in the recommendation feed, THEN it SHALL show a short "Why recommended" label: e.g., "A-line cut for pear shape · Warm autumn palette · Your size available".

4. WHEN a Shopper's body profile measurements are updated, THEN the recommendation feed SHALL refresh on next load.

5. WHEN a Shopper has neither completed analysis nor filled in a profile, THEN the system SHALL show a "Complete your profile" prompt card at the top of the AI Recommendations section.

### Correctness Properties

- **P_BODYSHAPE_VALID:** `body_shape ∈ {hourglass, pear, apple, rectangle, inverted_triangle}` for all recommendation queries.

---

## Requirement 5: Virtual Try-On (On-Device, Privacy-First, Gender-Gated)

**User Story:** As a Shopper, I want to see a composited image of myself wearing a selected garment, generated on my device, with the guarantee that I can only try on garments appropriate for my gender.

#### Acceptance Criteria

1. WHEN a Shopper taps "Try On" for a product, THEN the system SHALL check `product.gender_target` against `user.gender`:
   - IF `gender_target = male` AND `user.gender ≠ male` → block try-on, show message: "This item is designed for male shoppers"
   - IF `gender_target = female` AND `user.gender ≠ female` → block try-on, show message: "This item is designed for female shoppers"
   - IF `gender_target = unisex` → allow try-on for any gender
   - IF `user.gender = non-binary` → allow try-on for all products

2. WHEN the try-on is permitted, THEN the system SHALL prompt the Shopper to select a full-body photo from their gallery — this photo SHALL be processed entirely on-device and SHALL NOT be uploaded to any server.

3. WHEN the user selects a photo, THEN the system SHALL run on-device MediaPipe Pose Estimation to extract torso landmarks and compute the garment bounding box in pixel coordinates.

4. WHEN the bounding box is computed, THEN the system SHALL download ONLY the product's garment PNG from the CDN, resize it using OpenCV Flutter FFI, and composite it onto the user's photo on-device.

5. WHEN the composite image is generated, THEN the result SHALL have the same pixel dimensions as the input photo and all blended pixel values SHALL remain in [0, 255].

6. WHEN the try-on result is displayed, THEN the user SHALL be able to save to gallery, share, or add the product to cart — the composite SHALL NOT be uploaded to any server unless the user explicitly shares it.

7. IF MediaPipe detects no human pose (landmark visibility < 0.3 for key torso points), THEN the system SHALL show "No pose detected — please use a clear, full-body photo" and cancel compositing without crashing.

8. WHEN the try-on screen is closed, THEN both the source photo and composite SHALL be cleared from app memory.

### Correctness Properties

- **P_TRYON_PRIVACY:** Zero bytes of the user's body photo are transmitted to any server.
- **P_TRYON_GENDER:** A product with `gender_target = male` can never be composited for a `user.gender = female` Shopper, and vice versa (unless `gender_target = unisex` or `user.gender = non-binary`).
- **P14 (Dimension Preservation):** `result_image.dimensions == input_user_image.dimensions`.
- **P16 (Bounding Box Validity):** `x1 >= 0 ∧ y1 >= 0 ∧ x2 <= W ∧ y2 <= H ∧ width > 0 ∧ height > 0`.
- **P17 (Alpha Blend Range):** `0 <= v <= 255` for all blended pixel values.

---

## Requirement 6: Home Screen Layout — AI Recommendations vs Free Browse

**User Story:** As a Shopper, I want the home screen to clearly separate AI-powered outfit suggestions from the general catalog, so that I can explore personalized picks AND freely browse and shop any product I like.

#### Acceptance Criteria

1. WHEN a Shopper opens the home screen, THEN the system SHALL display two clearly labelled sections in the following order:
   - **Section A — "Recommended for You"**: AI-driven feed (body shape + skin tone + gender + size). Only visible when the user has a body profile. Shows the grouped-by-brand layout when multiple brands carry a matching item.
   - **Section B — "Browse All"**: Full paginated product catalog with search, gender filter (defaults to user's gender but can be changed), and size filter. No AI required to use this section.

2. WHEN Section A is visible and the user has a complete profile (gender + at least waist/hips measurements), THEN it SHALL display: first, exact matches (color + size + gender); then, "Similar styles" (same color palette or body shape rule, different size); then, brand-grouped view for items matching on both color and size across brands.

3. WHEN Section A brand-grouped view is shown, THEN each brand SHALL be displayed as a card with the brand logo and name as a header, and the matching products listed horizontally beneath it. Brands with more matching items appear higher.

4. WHEN a Shopper has not completed their body profile (gender required, measurements optional), THEN Section A SHALL show a "Set up your profile to get recommendations" card with a button linking to the profile setup screen; Section B SHALL always be visible regardless of profile completion.

5. WHEN a Shopper browses Section B, THEN they SHALL be able to tap any product to: view details, try it on (subject to gender-gate), or add directly to cart — no AI analysis required.

6. WHEN a Shopper taps "Try On" from Section B on a gender-gated product, THEN the gender-gate rule (Requirement 5, criterion 1) SHALL still apply.

7. WHEN a Shopper taps "Add to Cart" from either section, THEN the system SHALL prompt them to select a size label from the available size specs before adding.

### Correctness Properties

- **P_SECTION_VISIBILITY:** Section B is always visible to all authenticated Shoppers regardless of profile completion status.
- **P_GENDER_DEFAULT:** Section B's gender filter defaults to the user's registered gender but is always overridable by the user.

---

## Requirement 7: AR Live Try-On (On-Device, Gender-Gated)

**User Story:** As a Shopper, I want to see a selected garment overlaid on my live camera feed in real time, so that I can interactively evaluate clothing without taking a photo.

#### Acceptance Criteria

1. WHEN a Shopper navigates to the AR Try-On screen, THEN the system SHALL activate the device's front-facing camera and display a live preview at a consistent 60 FPS.

2. WHEN a garment is selected from the carousel on the AR Try-On screen, THEN the system SHALL run on-device MediaPipe pose estimation in a background Flutter Isolate and overlay the 2D garment image onto the camera feed using a `CustomPainter`.

3. WHEN the device's camera feed updates, THEN the garment overlay SHALL reposition in real time to track the user's torso landmarks without visible lag.

4. WHEN no human pose is detected in the camera feed, THEN the system SHALL display a visible UI indicator prompting the user to step back for a full-body view, without crashing.

5. WHERE the AR try-on is running, the Flutter UI thread SHALL remain unblocked; all MediaPipe inference SHALL execute in a separate Isolate.

---

## Requirement 8: Product Catalog, Brand Console, and Product Sizing

**User Story:** As a Brand Partner, I want to upload my clothing catalog with detailed size specifications and gender targeting, so that Shoppers see only gender-appropriate products and can find items that genuinely fit them.

#### Acceptance Criteria

1. WHEN a Brand Partner submits a new product, THEN the system SHALL require: SKU, name, price, stock, product image, at least one size spec entry, AND a `gender_target` field with one of three values: `male`, `female`, or `unisex`.

2. WHEN a Brand Partner adds a size specification, THEN for each size label (XS, S, M, L, XL, XXL, or custom) THEY SHALL enter measurement ranges in cm: `chest_min`–`chest_max`, `waist_min`–`waist_max`, `hips_min`–`hips_max`, `inseam_min`–`inseam_max` (optional for tops), `shoulder_width_min`–`shoulder_width_max`.

3. WHEN a Brand Partner submits a product with a price of 0 or less, THEN the system SHALL return HTTP 422 with a field-level error on the `price` field.

4. WHEN a Brand Partner submits a product image that is not HTTPS or not a supported format (PNG, JPEG, WebP), THEN the system SHALL return HTTP 422.

5. WHEN a Brand Partner accesses their Brand Console, THEN the system SHALL display only products where `product.brand_id == caller.brand_id`.

6. WHEN a Shopper browses `GET /inventory/products`, THEN the system SHALL by default filter products to those matching the Shopper's gender: a Male Shopper sees `gender_target = male OR unisex`; a Female Shopper sees `gender_target = female OR unisex`; a Non-binary Shopper sees all products.

7. WHEN a product's total `stock_quantity` across all sizes reaches 0, THEN the system SHALL mark it as unavailable.

### Correctness Properties

- **P9 (Price Positivity):** For all products `p`: `p.price > 0`.
- **P10 (Stock Non-Negativity):** For all products: `stock_quantity >= 0` at all times.
- **P_SIZE_VALID:** For all product size specs: `chest_min <= chest_max`, `waist_min <= waist_max`, `hips_min <= hips_max`, all values > 0.
- **P_GENDER_FILTER:** For all product listings served to a Male Shopper, `gender_target ∈ {male, unisex}`; for Female Shoppers, `gender_target ∈ {female, unisex}`.

---

## Requirement 9: Size-Based Product Search

**User Story:** As a Shopper, I want to search for clothing by size label (S, M, L) or by entering my exact measurements, so that I only see products that will actually fit me.

#### Acceptance Criteria

1. WHEN a Shopper enters the home/search screen, THEN the system SHALL display a search bar with a "Size Filter" button alongside the standard text search.

2. WHEN a Shopper opens the Size Filter, THEN the system SHALL present two search modes:
   - **Size label mode:** Select one or more standard labels (XS, S, M, L, XL, XXL)
   - **Custom measurement mode:** Enter specific values for chest, waist, hips, and/or inseam in their preferred unit (cm or inches, based on their profile setting)

3. WHEN a Shopper submits a custom measurement search (e.g., waist 78cm, hips 98cm), THEN the system SHALL return all products where at least one size spec satisfies: `waist_min <= 78 <= waist_max AND hips_min <= 98 <= hips_max`.

4. WHEN a Shopper selects size label "M", THEN the system SHALL return all products that have a size entry labelled "M" regardless of the underlying cm ranges.

5. WHEN a Shopper has a saved body profile, THEN the system SHALL offer a one-tap "Search my size" button that auto-fills the custom measurement fields from their profile measurements.

6. WHEN search results are displayed, THEN each product card SHALL show which of the user's filtered size/measurements it matches (e.g., "Fits your waist & hips").

7. WHEN both a text query and a size filter are active simultaneously, THEN the system SHALL apply both filters — text AND size — and return only products matching both criteria.

8. WHEN a Shopper's unit preference is imperial, THEN measurement inputs SHALL accept inches and the system SHALL convert to cm before querying the database.

### Correctness Properties

- **P_SEARCH_RANGE:** For all custom measurement searches with value `v` for dimension `d`: a product is returned if and only if `size_spec.d_min <= v <= size_spec.d_max` for at least one of its size specs.
- **P_UNIT_CONSISTENCY:** For all measurement values stored: the database always stores cm; display units are converted client-side based on user preference.

---

## Requirement 10: Shopping Cart and Checkout

**User Story:** As a Shopper, I want to add items to a cart and complete a secure purchase, so that I can buy clothes I've virtually tried on without leaving the app.

#### Acceptance Criteria

1. WHEN a Shopper adds a product to their cart, THEN the Flutter client SHALL update the cart state via `CartNotifier` and reflect the change immediately in the UI without a server round-trip.

2. WHEN a Shopper proceeds to checkout, THEN the system SHALL call `POST /payments/create-intent` which verifies stock availability for all cart items before creating a Stripe PaymentIntent.

3. IF any cart item has insufficient stock at checkout time, THEN the system SHALL return HTTP 409 with an "Insufficient stock" message identifying the out-of-stock product.

4. WHEN the Stripe PaymentIntent is created successfully, THEN the system SHALL insert an Order record with status PENDING and return the Stripe `client_secret` and `order_id` to the client.

5. WHEN the Shopper confirms payment via the Stripe Flutter SDK, THEN Stripe SHALL send a webhook to `POST /payments/webhook`; the system SHALL verify the Stripe webhook signature before processing.

6. WHEN the Stripe webhook is successfully verified for a completed payment, THEN the system SHALL update the Order status to CONFIRMED and decrement the stock quantity for each purchased product.

7. WHEN two users concurrently attempt to purchase the last unit of the same product, THEN the system SHALL use a PostgreSQL row-level lock (`SELECT FOR UPDATE`) to ensure exactly one purchase succeeds and the second receives HTTP 409.

8. WHERE payment is processed, raw card numbers, CVVs, and PANs SHALL never be stored on the FastAPI server; only `payment_intent_id` is persisted.

### Correctness Properties

- **P11 (Order Total Positivity):** For all orders `o`: `o.total_amount > 0`.
- **P12 (Payment Secrecy):** For all orders `o`: `o` contains no raw card numbers, CVVs, or full PANs — only `payment_intent_id`.
- **P10 (Stock Non-Negativity):** Stock quantity after any sequence of purchases never goes below 0.

---

## Requirement 11: Admin Dashboard and System Monitoring

**User Story:** As a System Admin, I want a dedicated web dashboard showing real-time platform analytics and Celery queue health, so that I can monitor system performance and manage the platform.

#### Acceptance Criteria

1. WHEN an Admin accesses the Admin Dashboard, THEN the system SHALL display real-time charts (using `fl_chart`) showing total sales, active users, and registered brands.

2. WHEN an Admin views the queue monitor panel, THEN the system SHALL display the current count of ML jobs in each state (QUEUED, PROCESSING, COMPLETED, FAILED) fetched from the backend.

3. WHEN an Admin accesses user management, THEN the system SHALL allow the Admin to view all registered users and their roles.

4. WHEN a non-Admin user attempts to access any Admin Dashboard route, THEN the system SHALL return HTTP 403 and redirect to the appropriate role dashboard.

5. WHERE Admin analytics data is displayed, the charts SHALL refresh automatically at a maximum interval of 30 seconds without requiring a manual page reload.

---

## Requirement 12: Performance and Infrastructure

**User Story:** As a user of any role, I want the app to be fast and reliable, so that interactions feel seamless even when ML processing is happening in the background.

#### Acceptance Criteria

1. WHEN a user performs any non-ML interaction (navigation, cart update, product browse), THEN the system SHALL complete the interaction within 2 seconds under nominal load.

2. WHEN a virtual try-on job is submitted, THEN the system SHALL return an HTTP 202 response (job accepted) within 2 seconds, with actual ML processing completing within 10 seconds under nominal conditions.

3. WHEN the Flutter UI is rendering, THEN the frame rate SHALL be maintained at 60 FPS on mid-range devices (Snapdragon 665 / Apple A12 class equivalent or higher).

4. WHEN product and result images are loaded, THEN the Flutter client SHALL serve them from the `cached_network_image` cache (7-day TTL) on repeat views, avoiding redundant network requests.

5. WHEN the system is under load, THEN Celery worker nodes SHALL be scalable independently via Docker Compose without restarting the FastAPI server.

6. WHEN the ML endpoint rate limit is hit (> 10 requests/minute per user), THEN the system SHALL return HTTP 429 immediately without queuing the excess request.

7. WHEN the FastAPI server handles concurrent requests, THEN all database operations SHALL use `AsyncSession` (SQLAlchemy async) with a connection pool of `pool_size=10, max_overflow=20`.

### Correctness Properties

- **P18 (UI Responsiveness):** For all user interactions not involving ML: response time < 2 seconds under nominal load.
- **P19 (Try-On Latency):** For all virtual try-on jobs: processing time <= 10 seconds under nominal conditions.
- **P20 (Frame Rate):** Flutter UI renders at >= 60 FPS on mid-range devices.

---

## Requirement 13: Security and Privacy

**User Story:** As a user, I want my account, payment data, and personal photos to be secure, so that I can trust the platform with sensitive information.

#### Acceptance Criteria

1. WHEN a Firebase ID token is verified, THEN the backend SHALL use `firebase_admin.auth.verify_id_token(token, check_revoked=True)` and raise HTTP 401 for expired, revoked, or malformed tokens.

2. WHEN the Stripe webhook endpoint receives a request, THEN the system SHALL verify the `Stripe-Signature` header using `stripe.Webhook.construct_event` before processing; unsigned requests SHALL be rejected with HTTP 400.

3. WHERE ML endpoint URLs are accepted, the system SHALL validate that all `image_url` values use HTTPS and match an allowlisted storage domain; HTTP URLs or unknown domains SHALL be rejected with HTTP 422.

4. WHEN any database query is executed, THEN the system SHALL use SQLAlchemy ORM parameterized queries exclusively; no raw SQL string interpolation is permitted.

5. WHEN CORS is configured, THEN the FastAPI `CORSMiddleware` SHALL enforce an explicit origin allowlist; wildcard (`*`) origins SHALL NOT be permitted in production.

6. WHEN secrets (Firebase credentials, Stripe keys, database passwords) are needed at runtime, THEN they SHALL be injected via environment variables or a secrets manager; they SHALL NOT be hardcoded or committed to source control.

7. WHEN ML endpoints receive excessive requests, THEN `slowapi` SHALL enforce per-user rate limiting (10 req/min), returning HTTP 429 on violation.

8. WHEN a Shopper uses body analysis or virtual try-on, THEN the system SHALL display a one-time privacy notice on first use stating: "Your photos are analyzed on your device only and are never uploaded."

9. WHEN user body metrics (measurements, skin tone) are transmitted to the server, THEN they SHALL be sent over HTTPS only and stored in the PostgreSQL `user_profiles` table accessible only to the owning user's authenticated requests.

10. WHEN a Shopper deletes their account, THEN the system SHALL delete all stored `UserProfile` records, body metrics, and order history within 24 hours.

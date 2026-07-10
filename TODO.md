# To-Do List — Improvement Plan to 9.5 / 10

Purpose: a **detailed, per-dimension roadmap** to take Style With Us from its current
state (~6.7/10 overall) to production quality (~9.5/10). Each dimension below is
self-contained: **current score → target**, the **specific gaps** (with file
references), a **step-by-step plan**, and a **Definition of Done (how to verify)**.

> The single biggest lever: the backend is already strong (~8/10, verified), but
> the **Flutter app and admin portal are written yet not compile-verified** in the
> build environment. Verifying and hardening those two layers unlocks the largest
> gains in Stability, Reliability and Testing.

**How to use this doc:** work top-to-bottom within each dimension, or follow the
[Prioritised roadmap](#prioritised-roadmap) at the end which sequences the work
into waves. Check items off as you go.

---

## 0. Prerequisites — owner actions (only you can do these)

These gate several dimensions and are not code changes I can make for you:

- [ ] **Rotate secrets.** The Firebase service-account key and Stripe keys were
  committed in an earlier revision. Rotate them in the Firebase and Stripe
  consoles. (Blocks Security → 9.5.)
- [ ] **Install/verify toolchains** on a dev machine: Flutter SDK (for
  `flutter analyze`/`test`/`run`) and `npm install` in `admin-portal/`.
  (Blocks Stability/Reliability/Testing → 9.5.)
- [ ] **Provision real infrastructure** for production targets: managed Postgres,
  Redis, object storage/CDN, TLS certs, a secrets manager. (Blocks Scalability/
  Security/Reliability at production scale.)
- [ ] **Real credentials** for full features: Firebase service-account JSON,
  Stripe **test** keys (then live), FCM. (Blocks Feature-completeness.)

---

## 1. Performance — 6.5 → 9.5

**Gaps**
- `recommendations.py` loads **every** product into memory and scores in Python per
  request (no pre-filter to a candidate set, no pagination, no caching).
- `admin.py` finance/earnings **loop per brand** issuing several queries each
  (`brand_gross_sales`, `brand_paid_out` per brand) — an N+1 pattern.
- `admin.py` `list_brands` runs a **count query per brand**.
- Flutter uses `Image.network` (via `AppNetworkImage`) instead of the declared
  `cached_network_image` — repeat fetches, no disk cache.
- AR try-on runs pose inference every camera frame ([ar_tryon_screen.dart]).

**Plan**
1. **Recommendations candidate generation in SQL.** Push gender + approved-brand +
   size availability filters into the query (already partly done) and `LIMIT` the
   candidate set (e.g. 200) before Python scoring. Add `ORDER BY` on cheap signals.
2. **Precompute product colour in Lab.** Store `dominant_color_lab` (or the Lab
   triplet) on `products` at write time (in `app/services/color.py`) so the
   recommendation loop skips hex→Lab conversion per request.
3. **Cache hot reads in Redis** (already in the stack). Cache `/recommendations/outfits`
   keyed by a hash of the user's profile (gender, measurements, skin hex, palette)
   with a short TTL; invalidate on `PATCH /users/profile` and on product create/update.
   Also cache `/admin/finance` and `/inventory/products` list pages.
4. **Kill the N+1 finance loops.** Replace per-brand queries in `admin.py`
   `list_brand_earnings` / `finance_overview` and `services/earnings.py` with **one
   aggregate query**: `SELECT product.brand_id, SUM(order_items.price_at_purchase *
   qty)` joined to `orders` (status=CONFIRMED) `GROUP BY brand_id`, and a second
   `SUM(payouts.amount) GROUP BY brand_id`. Merge in Python.
5. **`list_brands` product counts** via a single `LEFT JOIN products … GROUP BY brand`.
6. **Flutter image caching.** Change `AppNetworkImage` ([shared/widgets/ui.dart]) to
   use `CachedNetworkImage` (7-day TTL) — the dependency already exists.
7. **AR throttling.** Skip frames (process ~10–15 fps), run pose in a background
   `Isolate`, and wrap the preview in `RepaintBoundary`.
8. **Add DB indexes** where missing: `order_items(product_id)` (for earnings joins),
   confirm composite `ml_jobs(user_id, status)` exists (it does).

**Definition of Done**
- `locust` at 50 concurrent users: p95 < 300 ms for non-ML endpoints.
- Query-count assertions: earnings/finance endpoints issue **O(1)** queries (not O(brands)).
- Recommendations cache hit ratio > 80% in steady state; Flutter DevTools shows 60 fps.

---

## 2. Code quality — 7 → 9.5

**Gaps**
- `ProductResponse` / `ProductSizeSpecResponse` construction is **duplicated** across
  `inventory.py` (create, list, my-products) and `recommendations.py`.
- Function-level imports (`from uuid import UUID` inside handlers) scattered in
  `inventory.py`, `admin.py`.
- Magic numbers: score weights, commission default, YCbCr thresholds, `× 3` color
  weight — not named constants.
- Flutter declares unused packages (some of `firebase_messaging`, riverpod codegen)
  and has residual heuristic code.

**Plan**
1. **Serializer helpers.** Add `app/schemas/serializers.py` (or methods) —
   `product_to_response(product)` and `spec_to_response(spec)` — and use them
   everywhere. Removes ~4 copies of the same block.
2. **Hoist imports** to module top; remove inline imports.
3. **Named constants/config.** Extract weights and thresholds into a `constants.py`
   (e.g. `COLOR_SCORE_WEIGHT`, `DEFAULT_COMMISSION_PCT`, skin-mask bounds).
4. **Linters + formatters.** Add `ruff` + `black` + `mypy` (backend), `dart format`
   + `flutter analyze` (Flutter, fix all lints), `eslint` + `prettier` (admin). Add
   a `pyproject.toml`/config and a `pre-commit` config so it runs on commit.
5. **Prune/adopt deps.** In `pubspec.yaml` remove genuinely unused packages or wire
   them (e.g. `flutter_animate`, `glassmorphism` are now used; drop the rest if not).
6. **Docstrings** on public functions/classes; enforce with ruff `pydocstyle` (D).

**Definition of Done**
- `ruff`, `black --check`, `mypy` clean; `flutter analyze` 0 issues; `eslint` 0 errors.
- No duplicated serialization blocks; no magic numbers in business logic.

---

## 3. Stability — 6 → 9.5

**Gaps**
- Flutter + admin **not compiled** in this environment.
- No global error handling (unhandled 500s, no Flutter error boundary / React
  ErrorBoundary).
- Several features are simulated (try-on, payment).

**Plan**
1. **Compile & fix Flutter:** `flutter pub get && flutter analyze && flutter test`;
   fix everything it reports; then `flutter run` a full smoke of every screen.
2. **Build & fix admin:** `npm install && npm run build`; fix any TS errors.
3. **Global error handling.** FastAPI: add an exception handler that logs and returns
   a structured 500. Flutter: wrap `main()` in `runZonedGuarded` + a custom
   `ErrorWidget.builder`. Admin: add a React `ErrorBoundary` around routes.
4. **Readiness probe.** Add `GET /ready` that checks DB connectivity; keep `/health`
   as liveness.
5. **Connection resilience.** Set `pool_pre_ping=True` and `pool_recycle=1800` on the
   async engine ([core/database.py]).
6. **Idempotent checkout.** Guard against duplicate order creation (idempotency key
   or dedupe on `payment_intent_id`).
7. **Smoke-test script** that hits every endpoint with a happy path (extend the
   existing e2e scripts) and runs in CI.

**Definition of Done**
- `flutter analyze`/`test` and `npm run build` green; full manual smoke passes.
- Killing the DB mid-request returns a clean 503, not a crash; app recovers on reconnect.

---

## 4. Reliability — 6.5 → 9.5

**Gaps**
- `firebase.py` `DEGRADED_MODE` **accepts unverified JWTs** in dev.
- No retry/backoff on external calls (Stripe, storage, FCM).
- Hard-coded `localhost` URLs; no per-environment config.
- Logging is `print`-based, no correlation IDs.

**Plan**
1. **Gate insecure auth.** Only allow the unverified-token fallback when an explicit
   `ALLOW_INSECURE_AUTH=true` env is set (default false); log a loud warning; never
   in production. ([core/auth.py], [core/firebase.py])
2. **Retries with backoff** (e.g. `tenacity`) around Stripe and any network I/O;
   circuit-break on repeated failure.
3. **pool_pre_ping + pool_recycle** (also under Stability) for DB resilience.
4. **Config per environment.** Centralise base URLs and feature flags in
   `core/config.py`; Flutter via `--dart-define`; admin via `VITE_*`.
5. **Structured logging** (`structlog`) with request/correlation IDs; replace `print`.
6. **Crash/error reporting.** Integrate Sentry (backend + Flutter + admin) — optional
   but high value.
7. **Concurrency tests.** Add a test that two buyers racing the last unit → exactly
   one 200 and one 409 (the `SELECT … FOR UPDATE` path).

**Definition of Done**
- No code path accepts an unverified token unless the insecure flag is on.
- Transient Stripe/DB failures are retried and surfaced gracefully; logs are
  structured and correlated; race-condition test passes.

---

## 5. Maintainability — 7.5 → 9.5

**Gaps**
- **No CI.** Some duplication. Secret still in git history. `run_tests.sh` is the
  only automation.
- No `CONTRIBUTING.md`, no ADRs, no dependency automation.

**Plan**
1. **CI pipeline** (GitHub Actions), 3 jobs:
   - *backend:* `ruff` + `mypy` + `pytest` (with a Postgres service) + `alembic
     upgrade head` on a clean DB + coverage gate.
   - *admin:* `npm ci` + `tsc --noEmit` + `npm run build`.
   - *flutter:* `flutter analyze` + `flutter test`.
2. **Pre-commit hooks** (black, ruff, dart format, prettier).
3. **Purge the secret from history** (`git filter-repo`) and rotate keys (see §0).
4. **Docs hygiene.** Keep `docs/PROJECT_GUIDE.md` authoritative; the stale
   `design.md` is already annotated as superseded. Add `CONTRIBUTING.md` and a few
   **ADRs** (on-device ML, marketplace model, confirm-on-placement).
5. **Dependency management.** Pin versions; enable Dependabot/renovate; `pip-audit`
   + `npm audit` in CI.
6. **Reduce duplication** (see §2 serializers).

**Definition of Done**
- CI runs on every PR and must pass to merge; coverage gate enforced.
- A new developer can go from clone → running app using only the docs.

---

## 6. Architecture / design — 7.5 → 9.5

**Gaps**
- Business logic sits partly in routers; recommendation scoring is in-request/in-memory.
- Celery/Redis is scaffolded but **unused** (no real async layer).
- No API versioning; no audit trail for admin actions.

**Plan**
1. **Service layer.** Move business logic out of routers into `app/services/`
   (recommendations, checkout, moderation) so it's unit-testable and reusable;
   routers stay thin.
2. **Use the async layer.** Wire Celery workers (already in `docker-compose.yml`
   scaffold) for genuinely async work: analytics rollups, payout batches, email/FCM,
   nightly earnings snapshots — instead of computing per request.
3. **API versioning.** Prefix routes with `/v1`; document deprecation policy.
4. **Audit log.** Add an `admin_audit` table recording approve/reject/block/unblock/
   delete/payout/commission-change with actor + timestamp (traceability + compliance).
5. **Domain events (optional).** Emit events (order placed, brand approved) to enable
   notifications and decoupled side-effects.

**Definition of Done**
- Routers contain no business logic; services are unit-tested.
- Heavy/async work runs on workers; admin actions are audit-logged; endpoints are versioned.

---

## 7. Security — 5.5 → 9.5

**Gaps**
- Leaked key still in **git history**; unverified-JWT dev mode; rate limiting only on
  `/ml/*`; image-URL domain allowlist (spec 13.3) not enforced; no security headers/TLS.

**Plan**
1. **Rotate keys + purge history** (§0, §5). Move secrets to a **secrets manager** in
   prod (not `.env`); use a least-privilege Firebase key.
2. **Disable insecure auth in prod** (§4.1).
3. **Broaden rate limiting** (slowapi) to write/auth-sensitive endpoints: `register`,
   `create-intent`, `reviews`, `reports`, `subscribe`.
4. **Input hardening.** Enforce HTTPS + **allowlisted storage domain** for image URLs
   ([schemas/product.py]); cap string lengths; validate enums; reject oversized bodies.
5. **Security headers + TLS** at Nginx: HSTS, CSP, X-Frame-Options, X-Content-Type;
   Let's Encrypt certs; HTTP→HTTPS redirect.
6. **AuthZ review.** Confirm every `/admin/*` and brand-owned mutation is
   server-enforced (they are via `require_role` + ownership checks) and document it;
   ensure the admin portal's client-side gate is purely cosmetic.
7. **Dependency & code scanning.** `pip-audit`, `npm audit`, GitHub CodeQL in CI.
8. **Abuse protection.** Login brute-force throttling; account-lockout signals; the
   audit log from §6.

**Definition of Done**
- No secret in history; keys rotated; `pip-audit`/`npm audit` clean.
- Passes an OWASP top-10 checklist / the `/security-review` pass; TLS + headers verified.

---

## 8. Testing / QA — 6 → 9.5

**Gaps**
- Backend is well-covered (51 tests + hypothesis + e2e) but has gaps (webhook
  signature, subscription edges, block expiry, commission bounds). **Flutter and
  admin have ~no tests.**

**Plan**
1. **Backend coverage → 85%+.** Add tests: Stripe webhook valid/invalid signature;
   subscribe → cancel → resubscribe; block **expiry** (time-travel the clock);
   commission 0% and 100%; payout exceeding remaining; review upsert; the full RBAC
   matrix; approved-brand filtering. Add `pytest-cov --fail-under=85` in CI.
2. **Property-based tests** for `services/color.py`: score ∈ [0,1]; contrast
   monotonic in ΔE; near-skin colour always scores below a high-contrast harmonious one.
3. **Flutter tests.** Widget/unit tests for `CartNotifier`, `AuthNotifier`,
   `profile_setup` conversion, `Product.findMatchingSize`, skin/palette mapping;
   golden tests for key screens; one `integration_test` happy path.
4. **Admin tests.** `vitest` + React Testing Library for pages; `msw` to mock the API;
   test role-change, approve/reject, block, payout flows.
5. **CI runs all three suites** on every PR.

**Definition of Done**
- Backend coverage ≥ 85% (gated); Flutter + admin have meaningful suites; all run in CI.

---

## 9. Scalability — 5 → 9.5

**Gaps**
- In-memory recommendation scoring; per-request heavy work; no cache/queue; single instance.

**Plan**
1. **Caching** (see §1.3): Redis for recommendations, product lists, finance overview,
   with explicit invalidation.
2. **Precompute + denormalise:** product Lab colour (§1.2); nightly brand-earnings
   snapshots via a worker so `/admin/finance` reads a table, not live aggregates.
3. **Pagination everywhere** (cursor-based for large lists).
4. **Async workers** (§6.2) for heavy/batch jobs (Celery + Redis already scaffolded).
5. **Stateless horizontal scale:** the API is stateless (JWT auth) — run N replicas
   behind Nginx/load balancer; containerised already. Target Cloud Run / Fly / k8s.
6. **DB scaling:** tune pool, add read replicas for analytics, review indexes.
7. **CDN + object storage** for product/result images.

**Definition of Done**
- Load test to 500+ concurrent users with stable p95; cache hit ratio high; API
  scales horizontally with no session affinity.

---

## 10. UX / visual design — 7 → 9.5

**Gaps**
- Try-on is an **emoji AR overlay** / simulated; a few screens are lighter polish;
  accessibility not audited; admin uses `window.alert/confirm`.

**Plan**
1. **Real garment overlay.** Replace the emoji with an actual garment-PNG composite
   warped to the torso bounding box (OpenCV/canvas) in `virtual_tryon_screen.dart`
   and `ar_tryon_screen.dart`.
2. **Finish polish.** Shimmer skeletons on all loads; consistent empty/error states;
   optional light theme; micro-interactions + haptics; a first-run onboarding.
3. **Accessibility.** Semantics labels, WCAG AA contrast, dynamic text scaling,
   screen-reader passes (Flutter + admin).
4. **Admin UX.** Replace `alert/confirm` with toasts + modals; responsive tables;
   keyboard navigation; loading/disabled states on mutations.
5. **Usability testing** with a few users; iterate.

**Definition of Done**
- Try-on shows a real garment; accessibility audit passes AA; no blocking
  `alert/confirm`; consistent states across every screen.

---

## 11. Feature completeness — 6.5 → 9.5

**Gaps**
- The new marketplace backend has **no Flutter UI yet**; payments/try-on simulated;
  no push notifications; wishlist/orders are local-only.

**Plan**
1. **Flutter marketplace screens** (backend is ready & tested):
   - Shopper: **report an issue** form (`POST /reports`), **write/read reviews**
     (`/reviews`), **subscription** plans + subscribe (`/subscriptions/*`),
     blocked-account messaging.
   - Brand: **earnings dashboard** (`/brand/earnings`), **reviews on my products**
     (`/reviews/brand/mine`), **pending-approval banner** (`/brand/status`).
2. **Real Stripe** checkout via `flutter_stripe` with test keys; confirm via webhook
   (the backend already branches on a configured key).
3. **Real virtual try-on** compositing (see §10.1).
4. **Push notifications** (`firebase_messaging`) for order/approval/report/payout events.
5. **Backend-persisted** wishlist + order history (currently `SharedPreferences`).
6. **Search/filter** improvements (server-side text + size search UI).

**Definition of Done**
- Every backend capability has a working UI; live (test-mode) payments; real try-on;
  notifications delivered; wishlist/orders persist server-side.

---

## 12. Documentation — 7.5 → 9.5

**Gaps**
- No exported/hosted API reference; no runbooks/ADRs; per-module docs sparse.

**Plan**
1. **Hosted API reference.** Export the OpenAPI spec and publish (ReDoc/Swagger);
   keep `docs/PROJECT_GUIDE.md` in sync (it already lists every endpoint).
2. **Runbooks:** deploy, backup/restore, incident response, key rotation.
3. **ADRs** for major decisions (on-device ML, marketplace, confirm-on-placement,
   subscriptions).
4. **`CONTRIBUTING.md`** + a `.env` reference + a "first day" onboarding guide.
5. **Generated docs** (mkdocs-material) from docstrings, published via CI.

**Definition of Done**
- New engineer onboards from docs alone; API reference is hosted and current;
  runbooks + ADRs exist.

---

## Prioritised roadmap

Sequenced so each wave unblocks the next.

**Wave 1 — Unblock & verify (biggest stability/reliability/security gains)**
- Rotate keys; purge secret from history (§0, §5, §7).
- Install toolchains; get **Flutter compiling** and **admin building**; fix errors (§3).
- Stand up **CI** (backend + admin + flutter) with a coverage gate (§5, §8).

**Wave 2 — Harden the verifiable core**
- Backend performance: kill N+1 finance loops, add Redis caching, precompute Lab (§1).
- Code quality: serializer helpers, linters/formatters, constants (§2).
- Reliability: gate insecure auth, retries, `pool_pre_ping`, structured logging (§4).
- Testing: backend to 85%, colour property tests (§8).

**Wave 3 — Scale, features & polish**
- Architecture: service layer, Celery workers, audit log, API versioning (§6).
- Scalability: caching + snapshots + pagination + horizontal scale (§9).
- Security hardening: rate limits, headers/TLS, scanning (§7).
- Feature completeness: Flutter marketplace screens, real Stripe/try-on, notifications (§11).
- UX: real garment overlay, accessibility, admin toasts (§10).
- Docs: hosted API ref, runbooks, ADRs (§12).

---

*Keep this file updated as items land. When a dimension hits its Definition of Done,
mark it and record the evidence (test run, load test, audit) so the score is defensible.*

# Testing Guide — Style With Us

A practical, detailed guide to testing every layer of the platform: the FastAPI
backend, the React admin portal, and the Flutter app — plus manual QA scenarios,
non-functional testing, and a release checklist.

> **Current verified state:** backend **64 automated tests pass**, a full
> **marketplace end-to-end** run passes, and `alembic upgrade head` applies cleanly.
> The Flutter app and admin portal are written but **not yet compile-verified** —
> the steps below tell you exactly how to verify them on your machine.

**Contents**
1. [Test strategy & pyramid](#1-test-strategy--pyramid)
2. [Environment setup](#2-environment-setup)
3. [Backend — automated tests](#3-backend--automated-tests)
4. [Backend — migration test](#4-backend--migration-test)
5. [Backend — reproducible E2E harness (no Firebase needed)](#5-backend--reproducible-e2e-harness-no-firebase-needed)
6. [Backend — manual API testing](#6-backend--manual-api-testing)
7. [Admin portal testing](#7-admin-portal-testing)
8. [Flutter app testing](#8-flutter-app-testing)
9. [Manual QA — feature test cases](#9-manual-qa--feature-test-cases)
10. [Non-functional testing (performance, security, accessibility)](#10-non-functional-testing)
11. [Release / regression checklist](#11-release--regression-checklist)
12. [Troubleshooting the test setup](#12-troubleshooting-the-test-setup)

---

## 1. Test strategy & pyramid

| Layer | Tooling | What it covers |
|---|---|---|
| **Unit** | `pytest` (backend), `flutter_test` (Flutter), `vitest` (admin, planned) | Validators, pure logic (colour science, size-fit), notifiers |
| **Property-based** | `hypothesis` | Invariants: price positivity, size ranges, colour-score bounds |
| **Integration** | `pytest` + `httpx.AsyncClient` + Postgres | Endpoint behaviour against a real DB |
| **End-to-end** | Python ASGI harness / manual | Full role flows across many endpoints |
| **Manual QA** | Checklists (§9) | Role journeys, UX, edge cases |
| **Non-functional** | `locust`, `pip-audit`, a11y audits | Performance, security, accessibility |

Aim for a wide unit/integration base and a thin, high-value E2E/manual top.

---

## 2. Environment setup

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
```

### A throwaway Postgres for DB-backed tests (Docker)
```bash
docker run -d --name swu-test-pg \
  -e POSTGRES_PASSWORD=test -e POSTGRES_USER=test -e POSTGRES_DB=stylewithus_test \
  -p 55432:5432 postgres:16-alpine
export STYLEWITHUS_TEST_DATABASE_URL="postgresql+asyncpg://test:test@localhost:55432/stylewithus_test"
# ...run tests...
docker rm -f swu-test-pg          # tear down when done
```

### Admin portal
```bash
cd admin-portal && npm install
```

### Flutter
```bash
cd FYP && flutter pub get
```

---

## 3. Backend — automated tests

Run from `backend/` with the venv active.

**Infra-free suite (no external services; DB tests auto-skip):**
```bash
python -m pytest -q
# Expected: 55 passed, 9 skipped
```

**Full suite (with the throwaway Postgres from §2):**
```bash
python -m pytest -q            # STYLEWITHUS_TEST_DATABASE_URL is set
# Expected: 64 passed
```

**With coverage:**
```bash
pip install pytest-cov
python -m pytest --cov=app --cov-report=term-missing
```

### What each test file covers (`backend/tests/`)
| File | Type | Covers |
|---|---|---|
| `test_validators.py` | unit | `ProductCreate` price/HTTPS-image/gender, size-spec ranges, order-item qty, profile validators |
| `test_properties.py` | property | Price positivity, stock non-negativity, size-range validity, alpha-blend & bounding-box invariants |
| `test_rbac.py` | unit | `require_role` P2/P3/P4 via a fake session (shopper/brand/admin isolation + admin bypass) |
| `test_auth_firebase.py` | unit | `verify_firebase_token`: valid/missing/malformed/expired/revoked/invalid |
| `test_color.py` | unit + property | Colour science: palette classification validity (any hex → one of 6 palettes), **reference-hex round-trip invariant**, cool-skin-classifies-cool regression, suitability score bounds, near-skin-scores-lower, hex validation/normalization |
| `test_integration_checkout.py` | integration (DB) | Brand register → **approve** → product with inline sizes → size-label & measurement search → my-products |
| `test_integration_api.py` | integration (DB) | Profile CRUD + delete, recommendations, demo checkout, admin analytics, RBAC isolation, **server-side palette authority** (wrong client palette is overridden; garbage hex → 422) |

> DB-backed tests are gated behind `STYLEWITHUS_TEST_DATABASE_URL` because the schema
> uses Postgres-only types (UUID/ENUM); SQLite can't stand in. Without it they skip.

---

## 4. Backend — migration test

Verify Alembic builds the schema from scratch on a clean database:
```bash
# clean DB (from §2), then:
DATABASE_URL="postgresql+asyncpg://test:test@localhost:55432/stylewithus_test" \
  alembic upgrade head
# Expected: applies 001 then 002, no errors.

# sanity-check a few new columns/tables exist:
docker exec swu-test-pg psql -U test -d stylewithus_test -c "\dt"
docker exec swu-test-pg psql -U test -d stylewithus_test -c "\d brands"   # -> has status, rejection_reason
```
Also test the down-path on a scratch DB: `alembic downgrade base` should drop cleanly.

---

## 5. Backend — reproducible E2E harness (no Firebase needed)

The most efficient way to exercise whole flows without real Firebase tokens is to
**override the auth dependency** and run against the throwaway Postgres. Save this as
`backend/scripts/e2e_smoke.py` and run it with the venv + `STYLEWITHUS_TEST_DATABASE_URL` set.

```python
import asyncio, os
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.core.database import get_db
from app.core.auth import verify_firebase_token, DecodedToken
from app.models.base import Base

URL = os.environ["STYLEWITHUS_TEST_DATABASE_URL"]
def actor(uid, email):  # switch the "logged-in" user
    app.dependency_overrides[verify_firebase_token] = lambda: DecodedToken(uid=uid, email=email)

async def main():
    eng = create_async_engine(URL)
    async with eng.begin() as c:
        await c.run_sync(Base.metadata.drop_all); await c.run_sync(Base.metadata.create_all)
    session = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)()
    async def _db():
        yield session
    app.dependency_overrides[get_db] = _db
    c = AsyncClient(transport=ASGITransport(app=app), base_url="http://t")

    # 1) Admin (email must be in ADMIN_EMAILS, default admin@stylewithus.com)
    actor("admin", "admin@stylewithus.com"); await c.post("/users/register", json={})
    await c.patch("/admin/settings", json={"commission_percent": 15})

    # 2) Brand signs up (PENDING) -> can't sell yet
    actor("brand", "b@x.com")
    await c.post("/users/register", json={"role": "brand", "name": "Acme", "company_name": "Acme"})
    r = await c.post("/inventory/products", json={"sku":"T","name":"Tee","price":40,"gender_target":"female",
        "size_specs":[{"size_label":"M","stock_quantity":5,"chest_min":88,"chest_max":96,
                       "waist_min":70,"waist_max":78,"hips_min":94,"hips_max":102}]})
    assert r.status_code == 403, "pending brand must NOT be able to list"

    # 3) Admin approves -> brand can list
    actor("admin", "admin@stylewithus.com")
    bid = (await c.get("/admin/brands")).json()[0]["brand_id"]
    await c.post(f"/admin/brands/{bid}/approve")
    actor("brand", "b@x.com")
    r = await c.post("/inventory/products", json={"sku":"T","name":"Tee","price":40,"gender_target":"female",
        "dominant_color_hex":"#1D3557",
        "size_specs":[{"size_label":"M","stock_quantity":5,"chest_min":88,"chest_max":96,
                       "waist_min":70,"waist_max":78,"hips_min":94,"hips_max":102}]})
    assert r.status_code == 201
    p = r.json(); pid, sid = p["product_id"], p["size_specs"][0]["spec_id"]

    # 4) Shopper buys (confirm-on-placement) -> earnings appear
    actor("shopper", "s@x.com")
    await c.post("/users/register", json={"role":"shopper","name":"Sara"})
    await c.post("/users/profile", json={"gender":"female","waist_cm":74,"hips_cm":98,"skin_tone_hex":"#E9D6C3"})
    await c.post("/payments/create-intent", json={"items":[{"product_id":pid,"size_spec_id":sid,"quantity":2}]})

    # 5) Admin sees commission + payout math
    actor("admin", "admin@stylewithus.com")
    e = (await c.get("/admin/earnings")).json()[0]
    assert e["gross_sales"] == 80 and e["commission_amount"] == 12 and e["remaining"] == 68
    await c.post(f"/admin/brands/{bid}/payouts", json={"amount": 50})
    assert (await c.get("/admin/earnings")).json()[0]["remaining"] == 18

    print("E2E OK")
    await c.aclose(); await session.close(); await eng.dispose()

asyncio.run(main())
```
Run:
```bash
cd backend
STYLEWITHUS_TEST_DATABASE_URL="postgresql+asyncpg://test:test@localhost:55432/stylewithus_test" \
  python scripts/e2e_smoke.py     # -> "E2E OK"
```
Extend it to cover reviews, reports, subscriptions, and block/unblock (see the
scenarios in §9).

---

## 6. Backend — manual API testing

With the server running (`uvicorn app.main:app --reload`), open **Swagger UI** at
`http://localhost:8000/docs`.

Authenticated endpoints need `Authorization: Bearer <token>`. Two options:
- **Real token:** log in through the Flutter app or admin portal and copy the
  Firebase ID token from the network requests.
- **Dev mode:** with no service-account key the backend runs verify-only; for pure
  API testing without Firebase, prefer the §5 harness (it overrides auth cleanly).

Quick health check (no auth):
```bash
curl http://localhost:8000/health      # {"status":"ok"}
```

---

## 7. Admin portal testing

```bash
cd admin-portal
npm install
npx tsc --noEmit        # type-check (strict; catches unused vars/imports)
npm run build           # production build must succeed
npm run dev             # http://localhost:5173/admin/  for manual testing
```
Manual smoke (needs the backend running + an admin account in `ADMIN_EMAILS`):
1. **Login** with an admin email → lands on Dashboard; a non-admin sees "Access Denied".
2. **Dashboard** — stat cards, sales chart, ML donut render; auto-refresh (30s).
3. **Brands** — pending brands show **Approve/Reject**; approving flips status.
4. **Users** — change role; **Block** (3d/7d/30d/indefinite) shows "Blocked" badge;
   **Unblock**; **Delete** (with confirm).
5. **Finance** — set commission %, per-brand earnings table, **Record payout** updates
   remaining; overview cards reflect totals.
6. **Reports** — filter by status; **Resolve/Dismiss** with a note.
7. **Plans** — create a plan; **Deactivate/Activate**; **Remove**.

*(Planned automated tests: `vitest` + React Testing Library + `msw` — see [TODO.md](TODO.md) §8.)*

---

## 8. Flutter app testing

```bash
cd FYP
flutter pub get
flutter analyze          # MUST be clean before trusting the build
flutter test             # unit/widget tests (add more — see TODO.md §8)
flutter run              # pick a device; see base-URL note below
```
**API base URL per target** (`--dart-define=API_BASE_URL=…`):
| Target | Value |
|---|---|
| Windows/macOS/Linux desktop, web, iOS simulator | `http://localhost:8000` (default) |
| Android emulator | `http://10.0.2.2:8000` |
| Physical device | `http://<your-PC-LAN-IP>:8000` |

**Device/manual matrix**
- Android emulator (primary), a physical Android device, iOS simulator (if on macOS),
  and Chrome/Windows desktop for quick UI checks.
- Verify camera + gallery permissions for body analysis / AR.

**Launcher icon check:** after `flutter run`, confirm the app icon is the hanger logo
(not the default Flutter icon). To regenerate: `dart run flutter_launcher_icons`.

---

## 9. Manual QA — feature test cases

Each case: **Steps → Expected**. Run the shopper/brand flows in the app and the
admin flows in the portal; or drive them through the §5 harness.

### Auth & RBAC
| # | Steps | Expected |
|---|---|---|
| A1 | Sign up as Shopper | Role `shopper`; lands on shopper home |
| A2 | Sign up as Brand + company name | Role `brand`; brand created **PENDING** |
| A3 | Sign up with an email in `ADMIN_EMAILS` | Role `admin` |
| A4 | Shopper calls a `/admin/*` or brand-only endpoint | **403** |
| A5 | Any protected call with no token | **401** |

### Brand approval
| # | Steps | Expected |
|---|---|---|
| B1 | Pending brand uploads a product | **403** "pending admin approval" |
| B2 | Pending brand's products in shopper catalog | **Not shown** |
| B3 | Admin approves the brand | Status `approved`; brand can now upload (201) |
| B4 | Admin rejects with a reason | Status `rejected`; reason stored/shown |

### Moderation (block / unblock / delete)
| # | Steps | Expected |
|---|---|---|
| M1 | Admin blocks a shopper for 7 days | Shopper's protected calls → **403** with reason |
| M2 | Admin unblocks | Shopper works again (200) |
| M3 | Admin blocks indefinitely | 403 until explicitly unblocked |
| M4 | Admin tries to block an admin | **400** "cannot block an admin" |
| M5 | Admin deletes a user | **204**; cascades to profile/brand/orders |

### Reviews
| # | Steps | Expected |
|---|---|---|
| R1 | Shopper posts a review (rating 1–5) | **201** |
| R2 | Same shopper reviews the same product again | Upsert — still **one** review, updated |
| R3 | Rating 0 or 6 | **422** |
| R4 | Brand reads `/reviews/brand/mine` | Sees reviews on its products |
| R5 | `/reviews/product/{id}/summary` | Correct average + count |

### Issue reports
| # | Steps | Expected |
|---|---|---|
| P1 | Shopper/brand submits a report | **201**; appears in `/reports/mine` |
| P2 | Admin lists `/admin/reports` | Sees it (filter by status works) |
| P3 | Admin resolves/dismisses with a note | Status + note updated |

### Commission, earnings & payouts
| # | Steps | Expected |
|---|---|---|
| F1 | Admin sets commission 15% | Applies to all earnings immediately |
| F2 | Confirmed order of $80 | Brand gross $80, commission $12, net $68, remaining $68 |
| F3 | Admin records a $50 payout | Remaining → **$18** |
| F4 | Brand reads `/brand/earnings` | Matches the admin's numbers |
| F5 | `/admin/finance` | Totals = commission + subscription revenue |

### Subscriptions
| # | Steps | Expected |
|---|---|---|
| S1 | Admin creates a plan | Shopper sees it in `/subscriptions/plans` |
| S2 | Shopper subscribes | Active; `/subscriptions/me` returns it |
| S3 | Shopper cancels | No active subscription |
| S4 | Admin deactivates a plan | No longer listed to shoppers |
| S5 | Finance overview | `subscription_active_count` / `subscription_revenue` reflect actives |

### Skin-tone → colour recommendation
| # | Steps | Expected |
|---|---|---|
| C1 | Shopper sets `skin_tone_hex`; catalog has a near-skin colour + high-contrast colours | High-contrast/harmonious rank **first**; near-skin colour ranks **last** |
| C2 | Inspect `why_recommended` on a rec | Mentions undertone + contrast (e.g. "Bold cool pop … striking contrast") |
| C3 | On-device body analysis on a clear full-body photo | Skin swatch reflects **skin**, not the background |

### Size-fit & search
| # | Steps | Expected |
|---|---|---|
| Z1 | `GET /inventory/products?size_label=M` | Only products with an M spec |
| Z2 | `?waist=80` (inside a size's range) | Product returned; `?waist=200` → excluded |
| Z3 | Product detail with a matching profile | Green "AI Fit" banner + starred size |

### Cart & checkout
| # | Steps | Expected |
|---|---|---|
| K1 | Add to cart → checkout (demo mode) | Order **CONFIRMED**, stock decremented, `client_secret` ends `_secret_demo` |
| K2 | Checkout with insufficient stock | **409** |
| K3 | Checkout with no items | **400** |
| K4 | Two buyers race the last unit | Exactly one **200**, one **409** (row-lock) |

---

## 10. Non-functional testing

**Performance / load** — `locust` against a running API:
```bash
pip install locust
# write a locustfile hitting /inventory/products, /recommendations/outfits, /admin/finance
locust -H http://localhost:8000
```
Targets: p95 < 300 ms for non-ML endpoints at 50 concurrent users; watch query counts
on the finance/earnings endpoints (see [TODO.md](TODO.md) §1).

**Security**
```bash
pip install pip-audit && pip-audit          # backend deps
cd admin-portal && npm audit                # admin deps
```
Plus the `/security-review` checklist: token verification, RBAC on every `/admin/*`
and brand mutation, HTTPS image allowlist, no secrets in history (rotate + purge),
CORS allowlist, rate limits. See [TODO.md](TODO.md) §7.

**Accessibility** — Flutter: semantics labels, contrast (AA), text scaling,
TalkBack/VoiceOver passes. Admin: keyboard nav, contrast, screen-reader.

---

## 11. Release / regression checklist

Before tagging a release, confirm:

- [ ] `pytest` full suite green (51+); coverage not regressed.
- [ ] `alembic upgrade head` applies on a clean DB; new migration has a downgrade.
- [ ] §5 E2E smoke passes (approval → sale → commission → payout).
- [ ] `flutter analyze` clean; `flutter test` green; app runs on Android emulator.
- [ ] `npm run build` (admin) succeeds; manual admin smoke (§7) passes.
- [ ] Manual QA (§9): auth/RBAC, approval, moderation, reviews, reports, finance,
      subscriptions, colour rec, checkout — all pass.
- [ ] `pip-audit` / `npm audit` clean; no secret in git; keys rotated if ever exposed.
- [ ] CORS, env vars, and base URLs correct for the target environment.

---

## 12. Troubleshooting the test setup

| Symptom | Fix |
|---|---|
| `pytest` errors importing ROS / `launch_testing` / `lark` | A leaked `PYTHONPATH` is pulling system plugins. Run with a clean env: `env -u PYTHONPATH python -m pytest -q` (the repo's `pytest.ini` scopes collection to `tests/`). |
| DB tests all **skip** | `STYLEWITHUS_TEST_DATABASE_URL` isn't set / Postgres not running (see §2). |
| `alembic upgrade` → `type "userrole" already exists` | Fixed in this repo (`create_type=False`); ensure you're on the current migrations. Otherwise the DB already has the enums — run on a clean DB. |
| `alembic` → `KeyError: 'logger_sqlalchemy'` | Fixed (`alembic.ini` section renamed). Pull the current `alembic.ini`. |
| `email-validator is not installed` | `pip install -r requirements.txt` (it's now pinned). |
| Backend import fails: `firebase` warning | Expected in verify-only mode (no key). Not an error. |
| Flutter app shows only mock products | Backend unreachable at `API_BASE_URL`; on Android emulator use `10.0.2.2`. |
| Admin "not admin" after login | Add the email to `ADMIN_EMAILS` and log in again. |

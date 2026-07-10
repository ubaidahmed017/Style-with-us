"""End-to-end API coverage across the whole system (DB-backed, Stripe simulated).

Gated behind STYLEWITHUS_TEST_DATABASE_URL (see conftest). Firebase auth is
overridden per-user; payments run in demo mode (no Stripe key configured) so
checkout completes without external credentials.
"""

import pytest

from app.main import app
from app.core.auth import verify_firebase_token, DecodedToken
from tests.conftest import requires_db

pytestmark = requires_db


def _auth_as(uid, email):
    app.dependency_overrides[verify_firebase_token] = lambda: DecodedToken(
        uid=uid, email=email
    )


def _clear_auth():
    app.dependency_overrides.pop(verify_firebase_token, None)


@pytest.fixture
def shopper():
    _auth_as("shopper-1", "shopper@example.com")
    yield
    _clear_auth()


async def _register(client, role, name, company_name=None):
    body = {"role": role, "name": name}
    if company_name:
        body["company_name"] = company_name
    r = await client.post("/users/register", json=body)
    assert r.status_code == 201, r.text
    return r.json()


class TestShopperProfileFlow:
    async def test_profile_crud(self, client, shopper):
        await _register(client, "shopper", "Sam")

        # Create profile (gender required).
        created = await client.post(
            "/users/profile",
            json={"gender": "female", "waist_cm": 78, "hips_cm": 98},
        )
        assert created.status_code == 201, created.text
        assert created.json()["gender"] == "female"

        # Get profile.
        got = await client.get("/users/profile")
        assert got.status_code == 200
        assert got.json()["waist_cm"] == 78

        # Patch profile (body analysis result).
        patched = await client.patch(
            "/users/profile",
            json={"gender": "female", "body_shape": "hourglass"},
        )
        assert patched.status_code == 200
        assert patched.json()["body_shape"] == "hourglass"

    async def test_delete_account(self, client, shopper):
        await _register(client, "shopper", "Sam")
        await client.post("/users/profile", json={"gender": "male"})
        deleted = await client.delete("/users/me")
        assert deleted.status_code == 204
        # Profile is gone -> re-fetch 404 (user row removed).
        after = await client.get("/users/profile")
        assert after.status_code in (403, 404)


async def _approve_all_brands(db):
    from sqlalchemy import select
    from app.models import Brand, BrandStatus
    for brand in (await db.execute(select(Brand))).scalars().all():
        brand.status = BrandStatus.APPROVED
    await db.commit()


class TestRecommendationsAndCheckout:
    async def test_recommendations_and_demo_checkout(self, client, test_db):
        # Brand uploads a product with sizes (after admin approval).
        _auth_as("brand-9", "brand9@example.com")
        await _register(client, "brand", "Acme", company_name="Acme")
        await _approve_all_brands(test_db)
        prod = await client.post(
            "/inventory/products",
            json={
                "sku": "REC-1",
                "name": "Wrap Dress",
                "price": 59.0,
                "gender_target": "female",
                "image_url": "https://example.com/d.png",
                "dominant_color_hex": "#E63946",
                "size_specs": [
                    {
                        "size_label": "M", "stock_quantity": 3,
                        "chest_min": 88, "chest_max": 96,
                        "waist_min": 70, "waist_max": 78,
                        "hips_min": 94, "hips_max": 102,
                    }
                ],
            },
        )
        assert prod.status_code == 201, prod.text
        product_id = prod.json()["product_id"]
        size_spec_id = prod.json()["size_specs"][0]["spec_id"]
        _clear_auth()

        # Shopper with a matching profile gets a recommendation.
        _auth_as("shopper-9", "shopper9@example.com")
        await _register(client, "shopper", "Sara")
        await client.post(
            "/users/profile",
            json={"gender": "female", "waist_cm": 74, "hips_cm": 98},
        )
        recs = await client.get("/recommendations/outfits")
        assert recs.status_code == 200
        assert any(p["product_id"] == product_id for p in recs.json())

        # Demo checkout (no Stripe key) creates an order and a client_secret.
        intent = await client.post(
            "/payments/create-intent",
            json={"items": [
                {"product_id": product_id, "size_spec_id": size_spec_id, "quantity": 1}
            ]},
        )
        assert intent.status_code == 200, intent.text
        body = intent.json()
        assert body["client_secret"].endswith("_secret_demo")
        assert body["total_amount"] == 59.0
        _clear_auth()


class TestSkinTonePaletteAuthority:
    async def test_server_recomputes_palette_from_hex(self, client, shopper):
        """The measured hex is ground truth: even if a (stale/buggy) client
        sends a contradictory palette, the server stores the palette computed
        from the hex by services/color.py."""
        await _register(client, "shopper", "Sam")
        await client.post("/users/profile", json={"gender": "female"})

        # #BB8B7D is a cool mauve — client wrongly claims warm_spring.
        patched = await client.patch(
            "/users/profile",
            json={
                "gender": "female",
                "skin_tone_hex": "#BB8B7D",
                "skin_tone_palette": "warm_spring",
            },
        )
        assert patched.status_code == 200, patched.text
        assert patched.json()["skin_tone_palette"] == "cool_summer"
        # Hex normalized to uppercase #RRGGBB.
        assert patched.json()["skin_tone_hex"] == "#BB8B7D"

    async def test_garbage_hex_rejected(self, client, shopper):
        await _register(client, "shopper", "Sam")
        r = await client.post(
            "/users/profile",
            json={"gender": "female", "skin_tone_hex": "not-a-color"},
        )
        assert r.status_code == 422


class TestAdminAnalytics:
    async def test_admin_overview(self, client):
        # Admin is granted by the allowlist (config default admin@stylewithus.com).
        _auth_as("admin-1", "admin@stylewithus.com")
        reg = await client.post("/users/register", json={})
        assert reg.status_code == 201
        assert reg.json()["role"] == "admin"

        overview = await client.get("/admin/analytics/overview")
        assert overview.status_code == 200
        data = overview.json()
        assert set(data) >= {
            "total_users", "total_brands", "total_orders",
            "total_revenue", "active_ml_jobs",
        }

        ml = await client.get("/admin/analytics/ml-jobs")
        assert ml.status_code == 200
        assert set(ml.json()) == {"queued", "processing", "completed", "failed"}
        _clear_auth()

    async def test_non_admin_denied(self, client):
        _auth_as("shopper-x", "shopperx@example.com")
        await _register(client, "shopper", "Nope")
        denied = await client.get("/admin/analytics/overview")
        assert denied.status_code == 403
        _clear_auth()


class TestRbacIsolation:
    async def test_shopper_cannot_create_product(self, client):
        _auth_as("shopper-z", "shopperz@example.com")
        await _register(client, "shopper", "Zed")
        r = await client.post(
            "/inventory/products",
            json={
                "sku": "X", "name": "X", "price": 10, "gender_target": "unisex",
                "size_specs": [],
            },
        )
        assert r.status_code == 403
        _clear_auth()

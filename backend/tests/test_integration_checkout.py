"""DB-backed integration test for the brand -> product -> size-search flow.

Gated behind STYLEWITHUS_TEST_DATABASE_URL (see conftest). Firebase auth is
overridden so no real token is needed; Stripe is not exercised here.
"""

import pytest

from app.main import app
from app.core.auth import verify_firebase_token, DecodedToken
from tests.conftest import requires_db

BRAND_UID = "brand-uid-1"
BRAND_EMAIL = "brand@example.com"


@pytest.fixture
def as_brand():
    """Override auth so requests are authenticated as our brand user."""
    app.dependency_overrides[verify_firebase_token] = lambda: DecodedToken(
        uid=BRAND_UID, email=BRAND_EMAIL
    )
    yield
    app.dependency_overrides.pop(verify_firebase_token, None)


def _product_payload():
    return {
        "sku": "BRAND-TEE-001",
        "name": "Classic Tee",
        "price": 29.99,
        "gender_target": "unisex",
        "image_url": "https://example.com/tee.png",
        "size_specs": [
            {
                "size_label": "M",
                "stock_quantity": 5,
                "chest_min": 92, "chest_max": 98,
                "waist_min": 77, "waist_max": 83,
                "hips_min": 95, "hips_max": 101,
            }
        ],
    }


async def _approve_all_brands(db):
    """Approve every brand in the test DB (brands are PENDING by default now)."""
    from sqlalchemy import select
    from app.models import Brand, BrandStatus
    for brand in (await db.execute(select(Brand))).scalars().all():
        brand.status = BrandStatus.APPROVED
    await db.commit()


@requires_db
class TestBrandProductFlow:
    async def test_register_brand_upload_and_size_search(self, client, as_brand, test_db):
        # 1. Register as a brand -> creates the Brand record (PENDING).
        reg = await client.post(
            "/users/register",
            json={"role": "brand", "name": "Acme", "company_name": "Acme Co"},
        )
        assert reg.status_code == 201, reg.text
        assert reg.json()["role"] == "brand"
        await _approve_all_brands(test_db)  # admin approval required to sell

        # 2. Upload a product with an inline size spec.
        created = await client.post("/inventory/products", json=_product_payload())
        assert created.status_code == 201, created.text
        body = created.json()
        assert len(body["size_specs"]) == 1
        product_id = body["product_id"]

        # 3. Size-label search returns the product.
        by_label = await client.get("/inventory/products", params={"size_label": "M"})
        assert by_label.status_code == 200
        assert any(p["product_id"] == product_id for p in by_label.json())

        # 4. Measurement search within the M range returns it; outside does not.
        hit = await client.get("/inventory/products", params={"waist": 80})
        assert any(p["product_id"] == product_id for p in hit.json())
        miss = await client.get("/inventory/products", params={"waist": 200})
        assert all(p["product_id"] != product_id for p in miss.json())

        # 5. The brand sees its own product via /my-products.
        mine = await client.get("/inventory/my-products")
        assert mine.status_code == 200
        assert any(p["product_id"] == product_id for p in mine.json())

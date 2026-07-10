"""Pydantic schema validator tests (infra-free) against the real schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.product import ProductCreate, ProductSizeSpecCreate
from app.schemas.order import OrderItemCreate
from app.schemas.user import UserProfileCreate


def _product(**overrides):
    data = dict(
        sku="TEST-001",
        name="Test Product",
        price=29.99,
        image_url="https://example.com/image.jpg",
        gender_target="unisex",
    )
    data.update(overrides)
    return ProductCreate(**data)


class TestPriceValidation:
    """P9 (Price Positivity)."""

    def test_positive_price_is_valid(self):
        assert _product(price=29.99).price == 29.99

    def test_large_price_is_valid(self):
        assert _product(price=9999.99).price == 9999.99

    @pytest.mark.parametrize("bad", [0.0, -10.0])
    def test_non_positive_price_rejected(self, bad):
        with pytest.raises(ValidationError) as exc:
            _product(price=bad)
        assert "greater than zero" in str(exc.value).lower()


class TestImageUrlValidation:
    def test_https_url_is_valid(self):
        assert str(_product().image_url).startswith("https://")

    def test_http_url_rejected(self):
        with pytest.raises(ValidationError) as exc:
            _product(image_url="http://example.com/image.jpg")
        assert "https" in str(exc.value).lower()

    def test_unsupported_format_rejected(self):
        with pytest.raises(ValidationError):
            _product(image_url="https://example.com/file.gif")


class TestGenderTargetValidation:
    @pytest.mark.parametrize("gender", ["male", "female", "unisex"])
    def test_valid_gender_targets(self, gender):
        assert _product(gender_target=gender).gender_target.value == gender

    def test_invalid_gender_target_rejected(self):
        with pytest.raises(ValidationError):
            _product(gender_target="invalid-gender")


class TestSizeSpecValidation:
    """P_SIZE_VALID and P10 (Stock Non-Negativity)."""

    def _spec(self, **overrides):
        data = dict(
            size_label="M",
            stock_quantity=10,
            chest_min=92, chest_max=98,
            waist_min=77, waist_max=83,
            hips_min=95, hips_max=101,
        )
        data.update(overrides)
        return ProductSizeSpecCreate(**data)

    def test_valid_spec(self):
        assert self._spec().size_label == "M"

    def test_zero_stock_ok(self):
        assert self._spec(stock_quantity=0).stock_quantity == 0

    def test_negative_stock_rejected(self):
        with pytest.raises(ValidationError):
            self._spec(stock_quantity=-1)

    def test_min_greater_than_max_rejected(self):
        spec = self._spec(chest_min=100, chest_max=90)
        with pytest.raises(ValueError):
            spec.validate_ranges()

    def test_non_positive_measurement_rejected(self):
        with pytest.raises(ValidationError):
            self._spec(chest_min=0)


class TestOrderItemValidation:
    def test_valid_item(self):
        item = OrderItemCreate(
            product_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
            size_spec_id="3fa85f64-5717-4562-b3fc-2c963f66afa7",
            quantity=2,
        )
        assert item.quantity == 2

    def test_non_positive_quantity_rejected(self):
        with pytest.raises(ValidationError):
            OrderItemCreate(
                product_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
                size_spec_id="3fa85f64-5717-4562-b3fc-2c963f66afa7",
                quantity=0,
            )


class TestProfileValidation:
    def test_gender_required(self):
        with pytest.raises(ValidationError):
            UserProfileCreate()  # gender is mandatory

    def test_valid_profile(self):
        profile = UserProfileCreate(gender="female", waist_cm=78, hips_cm=98)
        assert profile.gender.value == "female"

    def test_negative_measurement_rejected(self):
        with pytest.raises(ValidationError):
            UserProfileCreate(gender="male", waist_cm=-5)

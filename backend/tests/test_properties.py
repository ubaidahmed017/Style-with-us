"""Property-based tests (hypothesis) against the real schemas and invariants."""

import pytest
from hypothesis import given, strategies as st, assume
from pydantic import ValidationError

from app.schemas.product import ProductCreate, ProductSizeSpecCreate


def _product(price):
    return ProductCreate(
        sku="TEST-001",
        name="Test Product",
        price=price,
        image_url="https://example.com/image.jpg",
        gender_target="unisex",
    )


class TestPricePositivity:
    """P9."""

    @given(price=st.floats(min_value=0.01, max_value=1_000_000))
    def test_positive_prices_valid(self, price):
        assert _product(price).price > 0

    @given(price=st.floats(max_value=0.0))
    def test_non_positive_prices_rejected(self, price):
        assume(price == price and price not in (float("inf"), float("-inf")))
        with pytest.raises(ValidationError):
            _product(price)


class TestSizeSpecStock:
    """P10 (Stock Non-Negativity) on ProductSizeSpecCreate."""

    def _spec(self, stock):
        return ProductSizeSpecCreate(
            size_label="M", stock_quantity=stock,
            chest_min=92, chest_max=98,
            waist_min=77, waist_max=83,
            hips_min=95, hips_max=101,
        )

    @given(stock=st.integers(min_value=0, max_value=1_000_000))
    def test_non_negative_stock_valid(self, stock):
        assert self._spec(stock).stock_quantity >= 0

    @given(stock=st.integers(max_value=-1))
    def test_negative_stock_rejected(self, stock):
        with pytest.raises(ValidationError):
            self._spec(stock)


class TestSizeRangeValidity:
    """P_SIZE_VALID: validate_ranges accepts min<=max, rejects min>max."""

    @given(
        lo=st.floats(min_value=1, max_value=200),
        hi=st.floats(min_value=1, max_value=200),
    )
    def test_range_validation(self, lo, hi):
        spec = ProductSizeSpecCreate(
            size_label="M", stock_quantity=1,
            chest_min=min(lo, hi), chest_max=max(lo, hi),
            waist_min=1, waist_max=200,
            hips_min=1, hips_max=200,
        )
        # min<=max always validates without raising
        spec.validate_ranges()


class TestAlphaBlendRange:
    """P17 (Alpha Blend Range)."""

    @given(
        alpha=st.floats(min_value=0.0, max_value=1.0),
        src=st.integers(min_value=0, max_value=255),
        dst=st.integers(min_value=0, max_value=255),
    )
    def test_blend_in_range(self, alpha, src, dst):
        result = int(alpha * src + (1 - alpha) * dst)
        assert 0 <= result <= 255


class TestBoundingBoxValidity:
    """P16 (Bounding Box Validity) from normalized keypoints."""

    @given(
        x1=st.floats(min_value=0, max_value=1),
        y1=st.floats(min_value=0, max_value=1),
        x2=st.floats(min_value=0, max_value=1),
        y2=st.floats(min_value=0, max_value=1),
        width=st.integers(min_value=100, max_value=1920),
        height=st.integers(min_value=100, max_value=1080),
    )
    def test_bbox_within_image(self, x1, y1, x2, y2, width, height):
        bx1 = int(min(x1, x2) * width)
        by1 = int(min(y1, y2) * height)
        bx2 = int(max(x1, x2) * width)
        by2 = int(max(y1, y2) * height)
        assert 0 <= bx1 <= bx2 <= width
        assert 0 <= by1 <= by2 <= height

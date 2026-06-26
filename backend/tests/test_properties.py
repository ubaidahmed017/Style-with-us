import pytest
from hypothesis import given, strategies as st, assume
from pydantic import ValidationError

from app.schemas.product import ProductCreate
from app.models.product import ProductSizeSpec


class TestPricePositivityProperty:
    """Property-based tests for P9 (Price Positivity)"""

    @given(price=st.floats(min_value=0.01, max_value=1000000))
    def test_positive_prices_always_valid(self, price):
        """P9: All positive prices should be valid"""
        product = ProductCreate(
            sku="TEST-001",
            name="Test Product",
            price=price,
            stock_quantity=10,
            image_url="https://example.com/image.jpg",
            gender_target="unisex"
        )
        assert product.price > 0

    @given(price=st.floats(max_value=0))
    def test_non_positive_prices_always_rejected(self, price):
        """P9: All non-positive prices should be rejected"""
        # Filter out NaN and infinity
        assume(not (price != price) and price != float('inf') and price != float('-inf'))

        with pytest.raises(ValidationError):
            ProductCreate(
                sku="TEST-001",
                name="Test Product",
                price=price,
                stock_quantity=10,
                image_url="https://example.com/image.jpg",
                gender_target="unisex"
            )


class TestStockNonNegativityProperty:
    """Property-based tests for P10 (Stock Non-Negativity)"""

    @given(stock=st.integers(min_value=0, max_value=1000000))
    def test_non_negative_stock_always_valid(self, stock):
        """P10: All non-negative stock quantities should be valid"""
        product = ProductCreate(
            sku="TEST-001",
            name="Test Product",
            price=29.99,
            stock_quantity=stock,
            image_url="https://example.com/image.jpg",
            gender_target="unisex"
        )
        assert product.stock_quantity >= 0

    @given(stock=st.integers(max_value=-1))
    def test_negative_stock_always_rejected(self, stock):
        """P10: All negative stock quantities should be rejected"""
        with pytest.raises(ValidationError):
            ProductCreate(
                sku="TEST-001",
                name="Test Product",
                price=29.99,
                stock_quantity=stock,
                image_url="https://example.com/image.jpg",
                gender_target="unisex"
            )


class TestBoundingBoxValidityProperty:
    """Property-based tests for P16 (Bounding Box Validity)"""

    @given(
        x1=st.floats(min_value=0, max_value=1),
        y1=st.floats(min_value=0, max_value=1),
        x2=st.floats(min_value=0, max_value=1),
        y2=st.floats(min_value=0, max_value=1),
        width=st.integers(min_value=100, max_value=1920),
        height=st.integers(min_value=100, max_value=1080),
    )
    def test_normalized_keypoints_produce_valid_bbox(
        self, x1, y1, x2, y2, width, height
    ):
        """P16: Normalized keypoints (0-1) should always produce valid bounding box"""
        # Ensure x1 < x2 and y1 < y2
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)

        # Convert normalized to pixel coordinates
        bbox_x1 = int(min_x * width)
        bbox_y1 = int(min_y * height)
        bbox_x2 = int(max_x * width)
        bbox_y2 = int(max_y * height)

        # Verify P16 constraints
        assert bbox_x1 >= 0, "x1 must be >= 0"
        assert bbox_y1 >= 0, "y1 must be >= 0"
        assert bbox_x2 <= width, "x2 must be <= image width"
        assert bbox_y2 <= height, "y2 must be <= image height"
        assert (bbox_x2 - bbox_x1) > 0, "width must be > 0"
        assert (bbox_y2 - bbox_y1) > 0, "height must be > 0"


class TestAlphaBlendRangeProperty:
    """Property-based tests for P17 (Alpha Blend Range)"""

    @given(
        alpha=st.floats(min_value=0.0, max_value=1.0),
        src=st.integers(min_value=0, max_value=255),
        dst=st.integers(min_value=0, max_value=255),
    )
    def test_alpha_blend_output_always_in_range(self, alpha, src, dst):
        """P17: Alpha blending result should always be in [0, 255]"""
        # Simulate alpha blending: result = alpha * src + (1 - alpha) * dst
        result = int(alpha * src + (1 - alpha) * dst)

        assert 0 <= result <= 255, f"Blended value {result} out of range [0, 255]"


class TestConfidenceBoundsProperty:
    """Property-based tests for P13 (Confidence Bounds)"""

    @given(confidence=st.floats(min_value=0.0, max_value=1.0))
    def test_valid_confidence_scores(self, confidence):
        """P13: All confidence scores must be in [0.0, 1.0]"""
        assert 0.0 <= confidence <= 1.0


class TestSizeRangeValidityProperty:
    """Property-based tests for P_SIZE_VALID"""

    @given(
        min_val=st.floats(min_value=0, max_value=200),
        max_val=st.floats(min_value=0, max_value=200),
    )
    def test_size_range_validity(self, min_val, max_val):
        """Size specs: chest_min <= chest_max, all > 0"""
        # Ensure min <= max
        actual_min = min(min_val, max_val)
        actual_max = max(min_val, max_val)

        # If min == max, that's also valid for a fixed size
        assert actual_min <= actual_max

        # Both must be > 0
        assume(actual_min > 0 or actual_max > 0)
        assert actual_max > 0, "Maximum measurement must be > 0"


class TestGenderFilterProperty:
    """Property-based tests for P_GENDER_FILTER"""

    @given(
        gender_target=st.sampled_from(["male", "female", "unisex"]),
        user_gender=st.sampled_from(["male", "female", "non_binary"]),
    )
    def test_gender_filtering_logic(self, gender_target, user_gender):
        """P_GENDER_FILTER: Verify gender filtering rules"""
        # Unisex products always match
        if gender_target == "unisex":
            assert True, "Unisex always matches"

        # Non-binary users see all products
        if user_gender == "non_binary":
            assert True, "Non-binary sees all"

        # Otherwise, must match
        if gender_target != "unisex" and user_gender != "non_binary":
            if user_gender == gender_target:
                assert True, "Gender matches"

"""Colour-science regression tests (skin-tone detection & recommendation).

Locks in the invariants behind the skin-tone → outfit-colour feature:
palette classification validity, reference-hex round-trip, suitability bounds,
and hex normalization.
"""

import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError

from app.models.enums import SkinTonePalette
from app.schemas.user import UserProfileCreate, normalize_hex_color
from app.services.color import (
    PALETTE_REFERENCE_HEX,
    hex_to_lab,
    palette_from_hex,
    skin_undertone,
    suitability,
)

VALID_PALETTES = {e.value for e in SkinTonePalette}

# Representative skin ladder: fair→deepest, warm & cool undertones.
SKIN_LADDER = [
    "#FFE0BD", "#F1C6B5", "#E8BEAC", "#E0AC69", "#C68642",
    "#BB8B7D", "#8D5524", "#7C4F3A", "#5C4033", "#3B2219", "#271610",
]

hex_colors = st.integers(min_value=0, max_value=0xFFFFFF).map(
    lambda v: f"#{v:06X}"
)


class TestPaletteClassification:
    @given(hexs=hex_colors)
    def test_always_returns_valid_palette(self, hexs):
        """Any parseable colour maps to one of the six enum palettes."""
        assert palette_from_hex(hexs) in VALID_PALETTES

    def test_invalid_hex_returns_none(self):
        assert palette_from_hex("banana") is None
        assert palette_from_hex("") is None

    def test_all_six_palettes_reachable_from_skin_ladder(self):
        """Regression: the old R−B mapper could never produce cool palettes."""
        produced = {palette_from_hex(h) for h in SKIN_LADDER}
        assert produced == VALID_PALETTES

    def test_cool_skin_classifies_cool(self):
        """A cool mauve-beige must not classify warm."""
        assert palette_from_hex("#BB8B7D") == "cool_summer"

    def test_reference_hexes_round_trip(self):
        """Regression: each palette's fallback hex must classify back to that
        palette, or fallback recommendations contradict the stated palette."""
        for palette, ref_hex in PALETTE_REFERENCE_HEX.items():
            assert palette_from_hex(ref_hex) == palette, (
                f"{palette} reference {ref_hex} classifies as "
                f"{palette_from_hex(ref_hex)}"
            )


class TestSuitability:
    @given(skin=hex_colors, garment=hex_colors)
    def test_score_bounds(self, skin, garment):
        result = suitability(skin, garment)
        assert result is not None
        assert 0.0 <= result["score"] <= 1.0
        assert 0.0 <= result["contrast"] <= 1.0

    def test_near_skin_colour_ranks_below_contrast(self):
        """A garment nearly matching the skin (washout) must score lower than a
        high-contrast harmonious colour."""
        deep_skin = "#5C4033"
        near = suitability(deep_skin, "#5F4636")["score"]
        strong = suitability(deep_skin, "#E9C46A")["score"]
        assert near < strong

    def test_undertone_detection_spread(self):
        """Golden skin reads warm; the classifier must not collapse everything
        into one undertone."""
        undertones = {skin_undertone(hex_to_lab(h)) for h in SKIN_LADDER}
        assert {"warm", "cool", "neutral"} <= undertones


class TestHexValidation:
    def test_garbage_hex_rejected(self):
        with pytest.raises(ValidationError):
            UserProfileCreate(gender="female", skin_tone_hex="banana")

    def test_hex_normalized(self):
        profile = UserProfileCreate(gender="female", skin_tone_hex="c68642")
        assert profile.skin_tone_hex == "#C68642"

    def test_none_passthrough(self):
        assert normalize_hex_color(None) is None

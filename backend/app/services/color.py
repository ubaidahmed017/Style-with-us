"""Colour science for skin-tone-aware outfit recommendations.

Everything works in CIELAB (perceptually uniform) so that "undertone harmony"
and "contrast" are computed the way the human eye actually perceives them, not
in raw RGB. Given a skin-tone hex and a garment hex we return a suitability
score in [0, 1] plus a human-readable reason.
"""

import math
from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# Colour-space conversions: sRGB hex -> linear -> XYZ (D65) -> CIELAB
# ---------------------------------------------------------------------------
def hex_to_rgb(hex_str: str) -> Optional[Tuple[int, int, int]]:
    if not hex_str:
        return None
    s = hex_str.lstrip("#").strip()
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        return None
    try:
        return int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
    except ValueError:
        return None


def _srgb_to_linear(c: float) -> float:
    c /= 255.0
    return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92


def rgb_to_lab(r: int, g: int, b: int) -> Tuple[float, float, float]:
    rl, gl, bl = _srgb_to_linear(r), _srgb_to_linear(g), _srgb_to_linear(b)
    # linear sRGB -> XYZ (D65)
    x = rl * 0.4124 + gl * 0.3576 + bl * 0.1805
    y = rl * 0.2126 + gl * 0.7152 + bl * 0.0722
    z = rl * 0.0193 + gl * 0.1192 + bl * 0.9505
    xn, yn, zn = 0.95047, 1.0, 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else (7.787 * t + 16 / 116)

    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def hex_to_lab(hex_str: str) -> Optional[Tuple[float, float, float]]:
    rgb = hex_to_rgb(hex_str)
    return rgb_to_lab(*rgb) if rgb else None


# ---------------------------------------------------------------------------
# Descriptors
# ---------------------------------------------------------------------------
def chroma(lab) -> float:
    _, a, b = lab
    return math.hypot(a, b)


def hue_deg(lab) -> float:
    _, a, b = lab
    return math.degrees(math.atan2(b, a)) % 360.0


def ita(lab) -> float:
    """Individual Typology Angle (skin lightness/depth), in degrees."""
    L, _, b = lab
    return math.degrees(math.atan2(L - 50.0, b)) if b != 0 else 0.0


def delta_e(lab1, lab2) -> float:
    """CIE76 perceptual distance."""
    return math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(lab1, lab2)))


def _is_warm_hue(h: float) -> Optional[bool]:
    """Warm = reds/oranges/yellows; cool = greens/blues/purples."""
    if 20.0 <= h <= 110.0 or h >= 340.0:
        return True
    if 150.0 <= h <= 320.0:
        return False
    return None  # ambiguous band (yellow-green / pink-red edges)


def skin_undertone(lab) -> str:
    """Classify skin undertone as warm / cool / neutral from its hue."""
    if chroma(lab) < 6:
        return "neutral"
    h = hue_deg(lab)
    if h >= 57.0:
        return "warm"      # golden / olive
    if h <= 46.0:
        return "cool"      # pink / rosy
    return "neutral"


def depth_label(lab) -> str:
    """Human label for skin depth from ITA."""
    v = ita(lab)
    if v > 48:
        return "fair"
    if v > 28:
        return "light"
    if v > 10:
        return "medium"
    if v > -30:
        return "tan"
    return "deep"


# ---------------------------------------------------------------------------
# Suitability
# ---------------------------------------------------------------------------
def suitability(skin_hex: str, garment_hex: str) -> Optional[dict]:
    """Score how well a garment colour flatters a skin tone (0..1) + reason.

    Combines three signals:
      * undertone harmony  (warm skin -> warm colours read as harmonious;
                            near-neutrals like black/white/navy suit everyone)
      * value/perceptual contrast (garment must stand clearly apart from skin
                            so it doesn't wash the wearer out)
      * chroma fit         (deeper skin carries brighter/high-chroma colours;
                            fairer skin suits softer chroma)
    """
    skin = hex_to_lab(skin_hex)
    garm = hex_to_lab(garment_hex)
    if skin is None or garm is None:
        return None

    # --- contrast (ΔE, and a lightness component) ---
    de = delta_e(skin, garm)
    contrast = max(0.0, min(1.0, de / 70.0))  # ΔE ~70+ => full marks

    # --- undertone harmony ---
    g_chroma = chroma(garm)
    s_under = skin_undertone(skin)
    if g_chroma < 12:
        undertone = 0.85            # near-neutral: broadly flattering
        under_word = "neutral"
    else:
        g_warm = _is_warm_hue(hue_deg(garm))
        if g_warm is None:
            undertone = 0.7
            under_word = "balanced"
        else:
            g_word = "warm" if g_warm else "cool"
            if s_under == "neutral":
                undertone = 0.8     # neutral skin flexes both ways
            elif (s_under == "warm") == g_warm:
                undertone = 1.0     # harmonious (same temperature)
            else:
                undertone = 0.55    # opposite temperature: still ok as a pop
            under_word = g_word

    # --- chroma fit by skin depth ---
    depth_ita = ita(skin)
    # deep skin (low ITA) rewarded for higher chroma; fair skin for gentler.
    ideal_chroma = 60.0 if depth_ita < 10 else (45.0 if depth_ita < 30 else 32.0)
    chroma_fit = 1.0 - min(1.0, abs(g_chroma - ideal_chroma) / 70.0)

    score = 0.5 * undertone + 0.38 * contrast + 0.12 * chroma_fit

    # --- reason ---
    con_word = "striking" if contrast > 0.75 else ("good" if contrast > 0.45 else "soft")
    if under_word == "neutral":
        reason = f"Versatile neutral with {con_word} contrast for {depth_label(skin)} skin"
    elif undertone >= 1.0:
        reason = f"Harmonises with your {s_under} undertone · {con_word} contrast"
    elif undertone <= 0.55:
        reason = f"Bold {under_word} pop against your {s_under} undertone · {con_word} contrast"
    else:
        reason = f"Flatters your skin · {con_word} contrast"

    return {
        "score": round(score, 4),
        "contrast": round(contrast, 3),
        "undertone": round(undertone, 3),
        "reason": reason,
    }


def palette_from_hex(skin_hex: str) -> Optional[str]:
    """Map a measured skin hex to one of the six seasonal palettes.

    Single source of truth for palette classification (the Flutter client ports
    this exact logic for instant display, but the server recomputes and stores
    the authoritative value whenever a skin_tone_hex is saved).

    undertone (LAB hue)  x  depth (ITA°) -> palette:
        warm    + light -> warm_spring      warm    + deep -> warm_autumn
        cool    + light -> cool_summer      cool    + deep -> cool_winter
        neutral + light -> neutral_light    neutral + deep -> neutral_deep
    """
    lab = hex_to_lab(skin_hex)
    if lab is None:
        return None
    undertone = skin_undertone(lab)
    is_light = ita(lab) > 28.0  # fair/light vs medium/tan/deep boundary
    if undertone == "warm":
        return "warm_spring" if is_light else "warm_autumn"
    if undertone == "cool":
        return "cool_summer" if is_light else "cool_winter"
    return "neutral_light" if is_light else "neutral_deep"


# Representative skin hex per seasonal palette, used as a fallback when the
# profile has a palette but no measured skin_tone_hex.
# INVARIANT (tested): palette_from_hex(PALETTE_REFERENCE_HEX[p]) == p — the
# fallback must produce the same undertone reasoning as the palette it stands
# in for, otherwise recommendations contradict the user's stated palette.
PALETTE_REFERENCE_HEX = {
    "warm_spring": "#F0C9A0",
    "warm_autumn": "#C68642",
    "cool_summer": "#BB8B7D",
    "cool_winter": "#3B2219",
    "neutral_light": "#F1C6B5",
    "neutral_deep": "#5C4033",
}

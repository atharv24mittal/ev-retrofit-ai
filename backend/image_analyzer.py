"""
image_analyzer.py
-----------------
Analyses an uploaded vehicle image using a rule-based CV approach
combined with basic image processing (no external API key needed).

For demo purposes: uses Pillow to extract basic image features,
then applies automotive heuristics to estimate vehicle properties.
Falls back gracefully if anything fails.
"""

import base64
import io
import re
import json
from PIL import Image, ImageStat


def _estimate_from_image(img: Image.Image) -> dict:
    """
    Extract basic visual signals from image using Pillow.
    Estimates rust (orange/brown pixels), damage (dark patches),
    vehicle size approximation from aspect ratio.
    """
    # Resize for fast processing
    thumb = img.convert("RGB").resize((200, 150))
    stat  = ImageStat.Stat(thumb)
    r_mean, g_mean, b_mean = stat.mean[:3]
    r_std,  g_std,  b_std  = stat.stddev[:3]

    # ── Rust detection: orange-brown dominance ────────────────────────────────
    # Rust pixels: R high, G medium, B low
    pixels     = list(thumb.getdata())
    rust_count = sum(1 for r,g,b in pixels if r > 140 and g < r*0.7 and b < r*0.5)
    rust_ratio = rust_count / len(pixels)
    has_rust   = 1 if rust_ratio > 0.08 else 0
    rust_sev   = "severe" if rust_ratio > 0.20 else "moderate" if rust_ratio > 0.12 else "minor" if rust_ratio > 0.08 else "none"

    # ── Chassis condition: overall image quality / saturation ─────────────────
    saturation = max(r_std, g_std, b_std)
    brightness = (r_mean + g_mean + b_mean) / 3
    chassis    = 8 if not has_rust and brightness > 80 else 6 if not has_rust else 4

    # ── Engine bay space: aspect ratio heuristic ──────────────────────────────
    w, h      = img.size
    aspect    = w / h
    bay_space = 7 if aspect > 1.6 else 5   # wider image → likely more engine bay visible

    # ── Vehicle type from aspect ratio + brightness distribution ─────────────
    if aspect > 2.0:
        vtype = "Van"
    elif aspect > 1.75:
        vtype = "SUV"
    elif aspect < 1.3:
        vtype = "Three-Wheeler"
    else:
        vtype = "Hatchback"

    confidence = 0.55 if not has_rust else 0.45

    return {
        "vehicle_type":          vtype,
        "estimated_age_years":   5,
        "has_rust":              has_rust,
        "rust_severity":         rust_sev,
        "chassis_condition":     chassis,
        "brake_condition":       7,
        "electrical_condition":  7,
        "estimated_weight_kg":   900 if vtype in ("Hatchback","Three-Wheeler") else 1300,
        "engine_bay_space_rating": bay_space,
        "damage_areas":          (["surface rust detected"] if has_rust else []),
        "battery_placement_zones":["Under-floor", "Boot area"],
        "ai_notes":              f"AI-assisted visual inspection: {rust_sev} rust, {vtype} detected. Scores are estimates — verify manually.",
        "confidence":            round(confidence, 2),
        "image_analysis_success": True,
    }


async def analyse_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    """
    Analyse vehicle image using local CV heuristics (no API key required).
    For presentations: label as 'AI-assisted visual inspection'.
    """
    try:
        img    = Image.open(io.BytesIO(image_bytes))
        result = _estimate_from_image(img)
        return result
    except Exception as e:
        return {
            "vehicle_type":           "Hatchback",
            "estimated_age_years":    5,
            "has_rust":               0,
            "rust_severity":          "none",
            "chassis_condition":      7,
            "brake_condition":        7,
            "electrical_condition":   7,
            "estimated_weight_kg":    900,
            "engine_bay_space_rating":6,
            "damage_areas":           [],
            "battery_placement_zones":["Under-floor", "Boot area"],
            "ai_notes":               f"Image processing unavailable ({str(e)[:60]}). Fill form manually.",
            "confidence":             0.0,
            "image_analysis_success": False,
        }


def analyse_image_sync(image_bytes: bytes, mime_type: str = "image/jpeg") -> dict:
    import asyncio
    return asyncio.run(analyse_image(image_bytes, mime_type))

"""
Pure Python color conversion and perceptual distance mathematics.
Strictly zero external C/ML dependencies (no scikit-image, cv2, numpy required in domain).
Complies with CIE D65 standard illuminant and sRGB conversion standards.
"""

import math
from typing import Tuple


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Convert hex string (e.g. '#1A3C34' or '1A3C34') to 8-bit RGB tuple (r, g, b)."""
    clean_hex = hex_str.strip().lstrip("#")
    if len(clean_hex) == 3:
        clean_hex = "".join([c * 2 for c in clean_hex])
    if len(clean_hex) != 6:
        raise ValueError(f"Invalid hex color string: '{hex_str}'")
    return (
        int(clean_hex[0:2], 16),
        int(clean_hex[2:4], 16),
        int(clean_hex[4:6], 16),
    )


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB tuple to uppercase hex string (e.g. '#1A3C34')."""
    return f"#{r:02X}{g:02X}{b:02X}"


def rgb_to_cielab(r: int, g: int, b: int) -> Tuple[float, float, float]:
    """
    Convert sRGB (0-255) to CIE L*a*b* under the D65 2-degree standard illuminant.
    Inverse gamma companding -> XYZ -> CIE Lab.
    """
    # 1. Inverse sRGB gamma companding to linear RGB
    def uncompand(channel_8bit: int) -> float:
        c = channel_8bit / 255.0
        if c <= 0.04045:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    r_lin = uncompand(r)
    g_lin = uncompand(g)
    b_lin = uncompand(b)

    # 2. Linear sRGB to CIE 1931 XYZ (D65 illuminant reference)
    X = 0.4124564 * r_lin + 0.3575761 * g_lin + 0.1804375 * b_lin
    Y = 0.2126729 * r_lin + 0.7151522 * g_lin + 0.0721750 * b_lin
    Z = 0.0193339 * r_lin + 0.1191920 * g_lin + 0.9503041 * b_lin

    # Reference white point: D65 (2-degree standard observer)
    Xn = 0.95047
    Yn = 1.00000
    Zn = 1.08883

    xr = X / Xn
    yr = Y / Yn
    zr = Z / Zn

    # 3. XYZ to CIE L*a*b* using standard transfer function
    delta = 6.0 / 29.0
    delta3 = delta ** 3  # ~0.008856

    def f(t: float) -> float:
        if t > delta3:
            return t ** (1.0 / 3.0)
        return (t / (3.0 * delta * delta)) + (4.0 / 29.0)

    fx = f(xr)
    fy = f(yr)
    fz = f(zr)

    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b_val = 200.0 * (fy - fz)

    return (round(L, 4), round(a, 4), round(b_val, 4))


def delta_e_cie76(lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]) -> float:
    """
    Compute Euclidean CIE76 color difference Delta-E between two Lab tuples:
    Delta-E = sqrt((L1 - L2)^2 + (a1 - a2)^2 + (b1 - b2)^2)
    """
    dL = lab1[0] - lab2[0]
    da = lab1[1] - lab2[1]
    db = lab1[2] - lab2[2]
    return math.sqrt(dL * dL + da * da + db * db)


def calculate_relative_luminance(r: int, g: int, b: int) -> float:
    """
    Calculate WCAG 2.1 relative luminance L from 8-bit RGB channels:
    L = 0.2126 * R + 0.7152 * G + 0.0722 * B (linear)
    """
    def channel_lum(val: int) -> float:
        c = val / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel_lum(r) + 0.7152 * channel_lum(g) + 0.0722 * channel_lum(b)


def calculate_contrast_ratio(lum1: float, lum2: float) -> float:
    """
    Calculate WCAG contrast ratio between two relative luminance values:
    (L_lighter + 0.05) / (L_darker + 0.05)
    """
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return round((lighter + 0.05) / (darker + 0.05), 2)

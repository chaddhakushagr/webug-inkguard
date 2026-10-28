"""
Image Document Extractor with Pillow, OCR graceful degradation, and visual brand checks.
Enforces:
1. Pillow image intake, dimension cap 4096x4096, decompression bomb guard, metadata stripping.
2. OCR text via shutil.which("tesseract") guard:
   - If available: runs pytesseract.image_to_string() in subprocess, bounding box contrast check.
   - If absent: fallback string "[Image submitted. OCR unavailable on this host — install tesseract-ocr to extract text from images.]"
3. Pure Python CIE Lab Delta-E palette check against brand_colours entries (PALETTE-001).
4. Contrast check on OCR bounding boxes (WCAG AA 4.5:1 ratio, citing RULE-A11Y-05).
5. Average hash perceptual logo match against approved lumo_logo.png (citing ASSET-LOGO-01).
"""

import io
import os
import random
import shutil
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw
import imagehash

from app.domain.documents.models import DocumentStructure, DocumentValidationError
from app.domain.review.color_math import (
    hex_to_rgb,
    rgb_to_hex,
    rgb_to_cielab,
    delta_e_cie76,
    calculate_relative_luminance,
    calculate_contrast_ratio,
)

# Standard Lumo Brand Colors (from PALETTE-001)
DEFAULT_BRAND_COLOURS = [
    "#1A3C34",  # Deep Teal
    "#F5F0E8",  # Warm Cream
    "#D4A853",  # Gold
    "#FFFFFF",  # White
]

FALLBACK_OCR_TEXT = "[Image submitted. OCR unavailable on this host — install tesseract-ocr to extract text from images.]"


def ensure_lumo_logo_exists() -> str:
    """Ensure the 100x40 solid-colour LUMO logo fixture exists on disk."""
    fixtures_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../tests/fixtures/assets")
    )
    os.makedirs(fixtures_dir, exist_ok=True)
    logo_path = os.path.join(fixtures_dir, "lumo_logo.png")

    if not os.path.exists(logo_path):
        img = Image.new("RGB", (100, 40), color="#1A3C34")
        d = ImageDraw.Draw(img)
        d.rectangle([5, 5, 95, 35], outline="#D4A853", width=2)
        d.text((25, 12), "LUMO", fill="#FFFFFF")
        img.save(logo_path, format="PNG")

    return logo_path


class ImageExtractor:
    """Extracts text and deterministic visual compliance findings from uploaded images."""

    def __init__(
        self,
        approved_colours: Optional[List[str]] = None,
        delta_e_threshold: float = 15.0,
        sample_pixel_count: int = 500,
    ):
        self.approved_colours = approved_colours or DEFAULT_BRAND_COLOURS
        self.delta_e_threshold = delta_e_threshold
        self.sample_pixel_count = sample_pixel_count

    def _strip_metadata_and_normalize(self, file_bytes: bytes) -> Image.Image:
        """
        Intake image with Pillow:
        - Check decompression bomb guard
        - Enforce dimension cap 4096x4096
        - Strip all Exif/XMP metadata by re-creating a clean RGB buffer
        """
        try:
            with Image.open(io.BytesIO(file_bytes)) as raw_img:
                width, height = raw_img.size
                if width > 4096 or height > 4096:
                    raise DocumentValidationError(
                        f"Image dimensions ({width}x{height}) exceed maximum allowed dimension of 4096x4096.",
                        code="DIMENSIONS_EXCEEDED",
                    )
                # Convert to RGB to strip alpha/palette nuances and clean metadata
                rgb_img = raw_img.convert("RGB")
                # Create clean detached copy with empty info dict to strip Exif / XMP
                clean_img = Image.new("RGB", rgb_img.size)
                clean_img.paste(rgb_img)
                clean_img.info = {}
                return clean_img
        except Image.DecompressionBombError:
            raise DocumentValidationError(
                "Image exceeds decompression bomb threshold (potential security hazard).",
                code="DECOMPRESSION_BOMB",
            )
        except DocumentValidationError:
            raise
        except Exception as e:
            raise DocumentValidationError(
                f"The uploaded image is corrupted or cannot be read: {str(e)}",
                code="CORRUPTED_FILE",
            )

    def _run_palette_check(self, img: Image.Image) -> Tuple[Optional[str], List[Dict[str, Any]]]:
        """
        Pure Python CIE Lab Delta-E brand compliance check (Pillow only, D65 illuminant).
        Samples 500 random pixels deterministically, computes min Delta-E against approved colours.
        Reports pixel clusters with Delta-E > 15 as an off-palette finding citing PALETTE-001.
        """
        width, height = img.size
        approved_labs = [rgb_to_cielab(*hex_to_rgb(c)) for c in self.approved_colours]

        rng = random.Random(42)  # Deterministic seed for reproducible testing
        total_pixels = width * height
        sample_count = min(self.sample_pixel_count, total_pixels)

        if total_pixels <= sample_count:
            coords = [(x, y) for x in range(width) for y in range(height)]
        else:
            coords = [
                (rng.randint(0, width - 1), rng.randint(0, height - 1))
                for _ in range(sample_count)
            ]

        pixel_access = img.load()
        off_palette_pixels: List[Tuple[int, int, int, float]] = []

        for x, y in coords:
            r, g, b = pixel_access[x, y]
            pix_lab = rgb_to_cielab(r, g, b)
            min_de = min(delta_e_cie76(pix_lab, a_lab) for a_lab in approved_labs)
            if min_de > self.delta_e_threshold:
                off_palette_pixels.append((r, g, b, min_de))

        if not off_palette_pixels:
            return "on_palette", []

        # Cluster off-palette pixels by quantized RGB (steps of 32)
        clusters: Dict[Tuple[int, int, int], List[Tuple[int, int, int, float]]] = {}
        for r, g, b, de in off_palette_pixels:
            q_key = (r // 32 * 32, g // 32 * 32, b // 32 * 32)
            clusters.setdefault(q_key, []).append((r, g, b, de))

        # Check for pixel clusters (at least 5 sampled pixels in cluster or >= 5 off-palette pixels)
        # This prevents 1-2 antialiased text boundary pixels from triggering false positives
        dom_key = max(clusters.keys(), key=lambda k: len(clusters[k]))
        dom_group = clusters[dom_key]
        if len(dom_group) < 5 and len(off_palette_pixels) < 5:
            return "on_palette", []

        avg_r = int(sum(p[0] for p in dom_group) / len(dom_group))
        avg_g = int(sum(p[1] for p in dom_group) / len(dom_group))
        avg_b = int(sum(p[2] for p in dom_group) / len(dom_group))
        dom_hex = rgb_to_hex(avg_r, avg_g, avg_b)
        dom_de = sum(p[3] for p in dom_group) / len(dom_group)

        off_count = len(off_palette_pixels)
        pct = (off_count / sample_count) * 100.0

        finding = {
            "id": "find-visual-palette",
            "issue_type": "brand",
            "severity": "medium",
            "confidence": 1.0,
            "span_start": 0,
            "span_end": 0,
            "excerpt": f"Off-palette color {dom_hex} (CIE Lab delta-E: {dom_de:.1f} > {self.delta_e_threshold})",
            "explanation": (
                f"Image contains {off_count} sampled pixel(s) ({pct:.1f}% of sample) deviating from approved "
                f"Lumo brand colors. Color cluster around {dom_hex} has a delta-E of {dom_de:.1f} against "
                f"the nearest approved brand color (approved limit is {self.delta_e_threshold})."
            ),
            "cited_entry_code": "PALETTE-001",
            "location": "Image Palette",
            "is_policy": True,
        }
        return "off_palette", [finding]

    def _run_logo_match(self, img: Image.Image) -> Tuple[str, Dict[str, Any]]:
        """
        Perceptual hash logo match (imagehash average hash) of approved Lumo logo vs submitted image.
        Reports:
        - 'logo_present' (distance <= 10)
        - 'logo_distorted' (10 < distance <= 20)
        - 'no_logo_found' (distance > 20)
        Advisory finding citing ASSET-LOGO-01. Never blocking (severity: low, is_policy: False).
        """
        logo_path = ensure_lumo_logo_exists()
        with Image.open(logo_path) as logo_file:
            logo_img = logo_file.convert("RGB")
            logo_hash = imagehash.average_hash(logo_img)

        img_hash = imagehash.average_hash(img)
        distance = logo_hash - img_hash

        if distance <= 10:
            verdict = "logo_present"
            explanation = f"Approved Lumo brand logo detected (perceptual hash distance: {distance})."
        elif distance <= 20:
            verdict = "logo_distorted"
            explanation = f"Lumo brand logo appears distorted or altered (perceptual hash distance: {distance} in 10-20 range)."
        else:
            verdict = "no_logo_found"
            explanation = f"No matching Lumo brand logo detected in submitted image (perceptual hash distance: {distance} > 20)."

        finding = {
            "id": "find-visual-logo",
            "issue_type": "brand",
            "severity": "low",  # Advisory only — never a blocking finding
            "confidence": 1.0,
            "span_start": 0,
            "span_end": 0,
            "excerpt": verdict,
            "explanation": explanation,
            "cited_entry_code": "ASSET-LOGO-01",
            "location": "Image Branding / Logo",
            "is_policy": False,  # Non-blocking advisory
        }
        return verdict, finding

    def _run_ocr_and_contrast(
        self, img: Image.Image
    ) -> Tuple[bool, str, Optional[str], List[Dict[str, Any]]]:
        """
        Runs OCR if tesseract is installed.
        If tesseract is absent, degrades cleanly to FALLBACK_OCR_TEXT and skips contrast check.
        If tesseract runs, checks average luminance of text-region vs local background on bounding boxes.
        Flags contrast ratio < 4.5:1 citing RULE-A11Y-05.
        """
        tesseract_bin = shutil.which("tesseract")
        if not tesseract_bin:
            return False, FALLBACK_OCR_TEXT, "OCR unavailable on this host — install tesseract-ocr to extract text from images.", []

        try:
            import pytesseract

            # 1. Extract text in subprocess
            extracted_text = pytesseract.image_to_string(img)
            clean_text = extracted_text.strip()
            if not clean_text:
                clean_text = "[Image submitted. No text detected.]"

            # 2. Extract bounding boxes for contrast check
            low_contrast_runs: List[Dict[str, Any]] = []
            try:
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
                n_boxes = len(data.get("text", []))
                w_img, h_img = img.size
                pix = img.load()

                for i in range(n_boxes):
                    text_val = (data["text"][i] or "").strip()
                    conf = int(data.get("conf", [0])[i])
                    if not text_val or conf < 30:
                        continue

                    x = data["left"][i]
                    y = data["top"][i]
                    bw = data["width"][i]
                    bh = data["height"][i]

                    if bw < 4 or bh < 4:
                        continue

                    # Sample text region pixels
                    text_lums = []
                    text_rgbs = []
                    for tx in range(x, min(w_img, x + bw)):
                        for ty in range(y, min(h_img, y + bh)):
                            r, g, b = pix[tx, ty]
                            text_lums.append(calculate_relative_luminance(r, g, b))
                            text_rgbs.append((r, g, b))

                    if not text_lums:
                        continue

                    avg_text_lum = sum(text_lums) / len(text_lums)

                    # Sample local background perimeter (5-pixel border around bounding box)
                    bg_lums = []
                    pad = 5
                    x0 = max(0, x - pad)
                    y0 = max(0, y - pad)
                    x1 = min(w_img, x + bw + pad)
                    y1 = min(h_img, y + bh + pad)

                    for bx in range(x0, x1):
                        for by in range(y0, y1):
                            # Exclude text region itself
                            if x <= bx < x + bw and y <= by < y + bh:
                                continue
                            r, g, b = pix[bx, by]
                            bg_lums.append(calculate_relative_luminance(r, g, b))

                    if not bg_lums:
                        continue

                    avg_bg_lum = sum(bg_lums) / len(bg_lums)
                    cr = calculate_contrast_ratio(avg_text_lum, avg_bg_lum)

                    if cr < 4.5:
                        avg_r = int(sum(p[0] for p in text_rgbs) / len(text_rgbs))
                        avg_g = int(sum(p[1] for p in text_rgbs) / len(text_rgbs))
                        avg_b = int(sum(p[2] for p in text_rgbs) / len(text_rgbs))
                        color_hex = rgb_to_hex(avg_r, avg_g, avg_b)

                        low_contrast_runs.append({
                            "text": text_val,
                            "color_hex": color_hex,
                            "contrast_ratio": cr,
                            "location_label": f"Image Text at ({x}, {y})",
                        })
            except Exception:
                # Bounding box contrast parsing fails gracefully
                pass

            return True, clean_text, None, low_contrast_runs

        except Exception as ocr_err:
            return False, FALLBACK_OCR_TEXT, f"OCR execution failed: {str(ocr_err)}", []

    def extract(self, file_bytes: bytes, filename: str) -> DocumentStructure:
        """
        Execute end-to-end image intake, OCR (or graceful degradation), palette check,
        contrast check, and logo matching.
        """
        # 1. Pillow intake, dimension check, decompression bomb guard, metadata stripping
        clean_img = self._strip_metadata_and_normalize(file_bytes)

        # 2. OCR text extraction with shutil.which("tesseract") guard & bounding box contrast
        ocr_applied, text_content, ocr_limitation, low_contrast_runs = self._run_ocr_and_contrast(clean_img)

        # 3. Pure Python CIE Lab Delta-E brand palette check
        palette_verdict, palette_findings = self._run_palette_check(clean_img)

        # 4. Logo match via perceptual average hash
        logo_verdict, logo_finding = self._run_logo_match(clean_img)

        visual_findings = list(palette_findings)
        visual_findings.append(logo_finding)

        doc = DocumentStructure(
            format="image",
            filename=filename,
            title=filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title(),
            page_count=1,
            full_text=text_content,
            ocr_applied=ocr_applied,
            ocr_limitation=ocr_limitation,
            low_contrast_runs=low_contrast_runs,
            visual_findings=visual_findings,
            logo_verdict=logo_verdict,
            palette_verdict=palette_verdict,
            metadata={
                "width": clean_img.width,
                "height": clean_img.height,
                "format": clean_img.format or "PNG",
                "mode": clean_img.mode,
            },
        )
        return doc

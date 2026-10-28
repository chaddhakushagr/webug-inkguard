"""
DOCX extractor adapter using python-docx.
Extracts:
1. Body text preserving paragraph order.
2. Headings with levels (1..6, Title, Subtitle).
3. Hyperlinks with text and target URLs.
4. Embedded images with alt text presence/absence.
5. Tables with row/col structure.
6. Low-contrast font runs (< 4.5:1 WCAG AA).
7. Location tracking for precise UI highlighting.
"""

import io
import re
from typing import List, Dict, Any, Tuple, Optional
import docx
from docx.text.paragraph import Paragraph
from docx.table import Table

from app.domain.documents.models import (
    DocumentStructure,
    DocumentBlock,
    ExtractedImage,
    ExtractedLink,
    ExtractedTable,
    DocumentValidationError,
)

NSMAP = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
}


def srgb_channel_to_luminance(c: int) -> float:
    c_norm = c / 255.0
    return c_norm / 12.92 if c_norm <= 0.04045 else ((c_norm + 0.055) / 1.055) ** 2.4


def calculate_relative_luminance(r: int, g: int, b: int) -> float:
    return (
        0.2126 * srgb_channel_to_luminance(r)
        + 0.7152 * srgb_channel_to_luminance(g)
        + 0.0722 * srgb_channel_to_luminance(b)
    )


def calculate_contrast_ratio(
    rgb1: Tuple[int, int, int], rgb2: Tuple[int, int, int] = (255, 255, 255)
) -> float:
    l1 = calculate_relative_luminance(*rgb1)
    l2 = calculate_relative_luminance(*rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


class DocxExtractor:
    """Extractor for DOCX documents using python-docx."""

    def extract(self, file_bytes: bytes, filename: str) -> DocumentStructure:
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
        except Exception as e:
            raise DocumentValidationError(
                f"Failed to parse DOCX document: {str(e)}",
                code="CORRUPTED_DOCX",
            )

        blocks: List[DocumentBlock] = []
        images: List[ExtractedImage] = []
        links: List[ExtractedLink] = []
        tables: List[ExtractedTable] = []
        low_contrast_runs: List[Dict[str, Any]] = []

        full_text_parts: List[str] = []
        current_char_offset = 0

        para_counter = 0
        table_counter = 0
        img_counter = 0
        doc_title: Optional[str] = None

        # Iterate through body elements in visual order
        for child in doc.element.body:
            tag = child.tag.split("}")[-1]

            if tag == "p":
                para_counter += 1
                p = Paragraph(child, doc)
                p_text = p.text.strip()
                style_name = p.style.name if p.style else "Normal"
                style_lower = style_name.lower()

                # Determine if heading
                is_heading = False
                heading_level = None

                if style_lower.startswith("heading"):
                    is_heading = True
                    match = re.search(r"\d+", style_name)
                    heading_level = int(match.group(0)) if match else 1
                elif style_lower == "title":
                    is_heading = True
                    heading_level = 1
                    if not doc_title and p_text:
                        doc_title = p_text
                elif style_lower == "subtitle":
                    is_heading = True
                    heading_level = 2

                if is_heading:
                    loc_label = f"Heading {heading_level}: {p_text[:35]}" if p_text else f"Heading {heading_level}"
                    block_type = "heading"
                else:
                    loc_label = f"Paragraph {para_counter}"
                    block_type = "paragraph"

                # Extract embedded hyperlinks in this paragraph
                try:
                    for hyperlink in p._p.xpath(".//w:hyperlink"):
                        r_id = hyperlink.get(
                            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                        )
                        link_url = ""
                        if r_id and r_id in p.part.rels:
                            rel = p.part.rels[r_id]
                            link_url = rel.target_ref or ""
                        link_text = "".join(node.text for node in hyperlink.xpath(".//w:t") if node.text)
                        if link_text.strip():
                            links.append(
                                ExtractedLink(
                                    text=link_text.strip(),
                                    url=link_url,
                                    paragraph_index=para_counter,
                                    location_label=loc_label,
                                )
                            )
                except Exception:
                    pass

                # Extract embedded drawings / images in this paragraph
                try:
                    for drawing in p._p.xpath(".//w:drawing"):
                        doc_pr_nodes = drawing.xpath(".//wp:docPr")
                        if doc_pr_nodes:
                            img_counter += 1
                            node = doc_pr_nodes[0]
                            img_id = node.get("id", str(img_counter))
                            img_name = node.get("name", f"Picture {img_counter}")
                            descr = (node.get("descr") or "").strip()
                            title = (node.get("title") or "").strip()
                            alt_text = descr or title
                            images.append(
                                ExtractedImage(
                                    id=img_id,
                                    name=img_name,
                                    alt_text=alt_text,
                                    has_alt_text=bool(alt_text),
                                    paragraph_index=para_counter,
                                    location_label=f"Image in {loc_label}",
                                )
                            )
                except Exception:
                    pass

                # Extract font color contrast in runs
                for r_idx, run in enumerate(p.runs):
                    if run.font.color and run.font.color.rgb:
                        rgb = run.font.color.rgb
                        try:
                            rgb_tuple = (rgb[0], rgb[1], rgb[2])
                            cr = calculate_contrast_ratio(rgb_tuple, (255, 255, 255))
                            if cr < 4.5 and run.text.strip():
                                low_contrast_runs.append(
                                    {
                                        "text": run.text.strip(),
                                        "color_hex": f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}",
                                        "contrast_ratio": round(cr, 2),
                                        "paragraph_index": para_counter,
                                        "location_label": loc_label,
                                    }
                                )
                        except Exception:
                            pass

                # Calculate spans
                char_start = current_char_offset
                full_text_parts.append(p_text)
                char_end = char_start + len(p_text)
                current_char_offset = char_end + 2  # account for \n\n

                blocks.append(
                    DocumentBlock(
                        block_type=block_type,
                        text=p_text,
                        level=heading_level,
                        paragraph_index=para_counter,
                        char_start=char_start,
                        char_end=char_end,
                        location_label=loc_label,
                        metadata={"style": style_name},
                    )
                )

            elif tag == "tbl":
                table_counter += 1
                tbl = Table(child, doc)
                rows_count = len(tbl.rows)
                cols_count = len(tbl.columns) if rows_count > 0 else 0
                cell_matrix: List[List[str]] = []
                table_lines: List[str] = []

                for r_idx, row in enumerate(tbl.rows):
                    row_texts = [cell.text.strip() for cell in row.cells]
                    cell_matrix.append(row_texts)
                    table_lines.append(" | ".join(row_texts))

                table_str = "\n".join(table_lines)
                table_loc = f"Table {table_counter}"

                tables.append(
                    ExtractedTable(
                        table_index=table_counter,
                        rows=rows_count,
                        cols=cols_count,
                        cells=cell_matrix,
                        location_label=table_loc,
                    )
                )

                char_start = current_char_offset
                full_text_parts.append(table_str)
                char_end = char_start + len(table_str)
                current_char_offset = char_end + 2

                blocks.append(
                    DocumentBlock(
                        block_type="table",
                        text=table_str,
                        paragraph_index=para_counter,
                        char_start=char_start,
                        char_end=char_end,
                        location_label=table_loc,
                        metadata={"rows": rows_count, "cols": cols_count},
                    )
                )

        full_text = "\n\n".join(full_text_parts).strip()

        return DocumentStructure(
            format="docx",
            filename=filename,
            title=doc_title,
            page_count=1,
            blocks=blocks,
            full_text=full_text,
            images=images,
            links=links,
            tables=tables,
            is_scanned=False,
            is_tagged_pdf=None,
            ocr_applied=False,
            low_contrast_runs=low_contrast_runs,
            metadata={"paragraphs": para_counter, "tables": table_counter, "images": img_counter},
        )

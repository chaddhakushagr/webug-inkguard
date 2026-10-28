"""
PDF extractor adapter using pdfplumber.
Extracts:
1. Text per page and page count (enforces 30-page cap).
2. Scanned PDF detection (routes to OCR if tesseract available, else declared limitation).
3. Tagged-PDF accessibility detection via Catalog MarkInfo.
4. Document title check via PDF metadata.
5. Location tracking (Page N, Paragraph M).
"""

import io
import shutil
from typing import List, Dict, Any, Optional
import pdfplumber
import pdfminer.pdftypes

from app.domain.documents.models import (
    DocumentStructure,
    DocumentBlock,
    DocumentValidationError,
)

MAX_PDF_PAGES = 30
SCANNED_TEXT_THRESHOLD = 50  # Characters across all pages


class PdfExtractor:
    """Extractor for PDF documents using pdfplumber."""

    def extract(self, file_bytes: bytes, filename: str) -> DocumentStructure:
        try:
            pdf = pdfplumber.open(io.BytesIO(file_bytes))
        except Exception as e:
            raise DocumentValidationError(
                f"Failed to parse PDF document: {str(e)}",
                code="CORRUPTED_PDF",
            )

        with pdf:
            page_count = len(pdf.pages)
            if page_count > MAX_PDF_PAGES:
                raise DocumentValidationError(
                    f"PDF contains {page_count} pages, exceeding the maximum allowed limit of {MAX_PDF_PAGES} pages.",
                    code="PAGE_LIMIT_EXCEEDED",
                )

            # 1. Document title from metadata
            doc_title: Optional[str] = None
            if pdf.metadata:
                raw_title = pdf.metadata.get("Title") or pdf.metadata.get("title")
                if raw_title and isinstance(raw_title, str) and raw_title.strip():
                    doc_title = raw_title.strip()

            # 2. Tagged PDF check via Catalog MarkInfo
            is_tagged_pdf = False
            try:
                catalog = pdf.doc.catalog
                mark_info_ref = catalog.get("MarkInfo")
                if mark_info_ref:
                    resolved = pdfminer.pdftypes.resolve1(mark_info_ref)
                    if isinstance(resolved, dict):
                        is_tagged_pdf = bool(resolved.get("Marked", False))
            except Exception:
                is_tagged_pdf = False

            # 3. Extract text per page
            blocks: List[DocumentBlock] = []
            full_text_parts: List[str] = []
            current_char_offset = 0
            total_extracted_chars = 0

            for page_idx, page in enumerate(pdf.pages):
                page_num = page_idx + 1
                raw_page_text = page.extract_text() or ""
                clean_page_text = raw_page_text.strip()
                total_extracted_chars += len(clean_page_text)

                if clean_page_text:
                    # Break into paragraph blocks
                    paragraphs = [p.strip() for p in clean_page_text.split("\n\n") if p.strip()]
                    if not paragraphs:
                        paragraphs = [p.strip() for p in clean_page_text.split("\n") if p.strip()]

                    for p_idx, para in enumerate(paragraphs, start=1):
                        char_start = current_char_offset
                        full_text_parts.append(para)
                        char_end = char_start + len(para)
                        current_char_offset = char_end + 2
                        loc_label = f"Page {page_num}, Paragraph {p_idx}"

                        blocks.append(
                            DocumentBlock(
                                block_type="paragraph",
                                text=para,
                                page_num=page_num,
                                paragraph_index=p_idx,
                                char_start=char_start,
                                char_end=char_end,
                                location_label=loc_label,
                                metadata={"page": page_num},
                            )
                        )

            # 4. Scanned PDF detection and OCR routing
            is_scanned = total_extracted_chars < SCANNED_TEXT_THRESHOLD
            ocr_applied = False
            ocr_limitation: Optional[str] = None

            if is_scanned:
                tesseract_path = shutil.which("tesseract")
                if tesseract_path:
                    try:
                        import pytesseract

                        ocr_texts: List[str] = []
                        for page_idx, page in enumerate(pdf.pages):
                            page_num = page_idx + 1
                            # Render page image for OCR
                            img = page.to_image(resolution=150).original
                            ocr_text = pytesseract.image_to_string(img).strip()
                            if ocr_text:
                                ocr_texts.append(ocr_text)
                                char_start = current_char_offset
                                full_text_parts.append(ocr_text)
                                char_end = char_start + len(ocr_text)
                                current_char_offset = char_end + 2
                                loc_label = f"Page {page_num} (OCR)"

                                blocks.append(
                                    DocumentBlock(
                                        block_type="paragraph",
                                        text=ocr_text,
                                        page_num=page_num,
                                        paragraph_index=1,
                                        char_start=char_start,
                                        char_end=char_end,
                                        location_label=loc_label,
                                        metadata={"page": page_num, "source": "ocr"},
                                    )
                                )
                        if ocr_texts:
                            ocr_applied = True
                    except Exception as ocr_err:
                        ocr_limitation = f"OCR execution failed on host: {str(ocr_err)}"
                else:
                    ocr_limitation = (
                        "OCR unavailable on this host: Scanned PDF contains minimal or no extractable text. "
                        "Deploy via Docker or install tesseract-ocr to enable scanned document processing."
                    )
                    if not full_text_parts:
                        notice = f"[Scanned PDF detected ({page_count} pages). {ocr_limitation}]"
                        full_text_parts.append(notice)
                        blocks.append(
                            DocumentBlock(
                                block_type="paragraph",
                                text=notice,
                                page_num=1,
                                paragraph_index=1,
                                char_start=0,
                                char_end=len(notice),
                                location_label="Document Limitation",
                                metadata={"limitation": True},
                            )
                        )

            full_text = "\n\n".join(full_text_parts).strip()

            return DocumentStructure(
                format="pdf",
                filename=filename,
                title=doc_title,
                page_count=page_count,
                blocks=blocks,
                full_text=full_text,
                images=[],
                links=[],
                tables=[],
                is_scanned=is_scanned,
                is_tagged_pdf=is_tagged_pdf,
                ocr_applied=ocr_applied,
                ocr_limitation=ocr_limitation,
                low_contrast_runs=[],
                metadata={
                    "page_count": page_count,
                    "is_scanned": is_scanned,
                    "is_tagged_pdf": is_tagged_pdf,
                },
            )

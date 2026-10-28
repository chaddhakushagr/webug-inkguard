"""
Unified Document Extractor implementing DocumentExtractorPort.
Orchestrates:
1. Safety & magic-bytes validation (validator.py).
2. Per-file extraction timeout guard (10 seconds).
3. Routing to DocxExtractor or PdfExtractor.
"""

import concurrent.futures
from typing import Optional
from app.ports.document_extractor import DocumentExtractorPort
from app.domain.documents.models import DocumentStructure, DocumentValidationError
from app.adapters.documents.validator import validate_document_safety
from app.adapters.documents.docx_extractor import DocxExtractor
from app.adapters.documents.pdf_extractor import PdfExtractor
from app.adapters.documents.image_extractor import ImageExtractor


class DocumentExtractor(DocumentExtractorPort):
    """Main document extractor adapter with safety validation and timeout guards."""

    def __init__(self, timeout_seconds: float = 10.0):
        self.timeout_seconds = timeout_seconds
        self.docx_extractor = DocxExtractor()
        self.pdf_extractor = PdfExtractor()
        self.image_extractor = ImageExtractor()

    def _execute_extraction(self, fmt: str, file_bytes: bytes, filename: str) -> DocumentStructure:
        if fmt == "docx":
            return self.docx_extractor.extract(file_bytes, filename)
        elif fmt == "pdf":
            return self.pdf_extractor.extract(file_bytes, filename)
        elif fmt == "image":
            return self.image_extractor.extract(file_bytes, filename)
        else:
            raise DocumentValidationError(
                f"Unsupported document format '{fmt}'.",
                code="UNSUPPORTED_FORMAT",
            )

    def extract(self, file_bytes: bytes, filename: str) -> DocumentStructure:
        """
        Validate safety and extract structured content from document bytes.
        Enforces magic bytes check, size cap, zip bomb guard, and 10s timeout.
        """
        # Step 1: Safety validation (magic bytes, size cap, zip bomb, macros)
        fmt = validate_document_safety(file_bytes, filename)

        # Step 2: Extraction with timeout protection
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._execute_extraction, fmt, file_bytes, filename)
            try:
                return future.result(timeout=self.timeout_seconds)
            except concurrent.futures.TimeoutError:
                raise DocumentValidationError(
                    f"Document extraction timed out after {self.timeout_seconds} seconds.",
                    code="EXTRACTION_TIMEOUT",
                )
            except Exception as e:
                if isinstance(e, DocumentValidationError):
                    raise e
                raise DocumentValidationError(
                    f"Extraction failed: {str(e)}",
                    code="EXTRACTION_FAILED",
                )

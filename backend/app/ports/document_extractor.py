"""
Port interface for document extraction.
Clean architecture protocol defining extraction of structured documents (DOCX, PDF).
Zero framework or adapter dependencies.
"""

from typing import Protocol
from app.domain.documents.models import DocumentStructure


class DocumentExtractorPort(Protocol):
    """Port interface for structured document extraction."""

    def extract(self, file_bytes: bytes, filename: str) -> DocumentStructure:
        """
        Extract structured content from document bytes (DOCX or PDF).
        Validates magic bytes, sizes, caps, zip bombs, and handles timeouts.
        Raises DocumentValidationError if invalid, corrupted, or exceeding safety limits.
        """
        ...

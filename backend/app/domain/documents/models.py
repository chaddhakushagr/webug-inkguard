"""
Pure domain models for structured document extraction and representation.
Zero external framework or database dependencies.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


class DocumentValidationError(Exception):
    """Raised when an uploaded document fails validation, safety checks, or extraction."""

    def __init__(self, message: str, code: str = "INVALID_DOCUMENT"):
        super().__init__(message)
        self.message = message
        self.code = code


@dataclass
class ExtractedImage:
    id: str
    name: str
    alt_text: str = ""
    has_alt_text: bool = False
    paragraph_index: Optional[int] = None
    location_label: str = "Image"


@dataclass
class ExtractedLink:
    text: str
    url: str
    paragraph_index: Optional[int] = None
    location_label: str = "Link"


@dataclass
class ExtractedTable:
    table_index: int
    rows: int
    cols: int
    cells: List[List[str]] = field(default_factory=list)
    location_label: str = "Table"


@dataclass
class DocumentBlock:
    """A discrete block of content (heading, paragraph, table row, callout)."""
    block_type: str  # "heading", "paragraph", "table", "image", "list_item"
    text: str
    level: Optional[int] = None  # Heading level 1..6 if block_type == "heading"
    page_num: Optional[int] = None  # 1-indexed page number if PDF
    paragraph_index: Optional[int] = None
    char_start: int = 0
    char_end: int = 0
    location_label: str = "Paragraph"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentStructure:
    """Complete structured output from extracting a DOCX or PDF file."""
    format: str  # "docx" or "pdf"
    filename: str
    title: Optional[str] = None
    page_count: int = 1
    blocks: List[DocumentBlock] = field(default_factory=list)
    full_text: str = ""
    images: List[ExtractedImage] = field(default_factory=list)
    links: List[ExtractedLink] = field(default_factory=list)
    tables: List[ExtractedTable] = field(default_factory=list)
    is_scanned: bool = False
    is_tagged_pdf: Optional[bool] = None
    ocr_applied: bool = False
    ocr_limitation: Optional[str] = None
    low_contrast_runs: List[Dict[str, Any]] = field(default_factory=list)
    visual_findings: List[Dict[str, Any]] = field(default_factory=list)
    logo_verdict: Optional[str] = None
    palette_verdict: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def find_location(self, span_start: int, span_end: int) -> str:
        """Map a character span in full_text back to its paragraph/block location label."""
        for block in self.blocks:
            # Overlap condition: max(start1, start2) < min(end1, end2)
            if max(span_start, block.char_start) < min(span_end, block.char_end):
                return block.location_label
            # If span is at exact start of block
            if block.char_start <= span_start <= block.char_end:
                return block.location_label
        return "Body"

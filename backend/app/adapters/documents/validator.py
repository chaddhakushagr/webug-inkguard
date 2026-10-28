"""
Document safety and magic-bytes validator.
Enforces:
1. Magic bytes detection (rejects renamed .exe, scripts, invalid archives).
2. Strict size cap (5 MB).
3. Zip bomb protection (entry count <= 500, uncompressed size <= 25 MB, ratio <= 100:1).
4. Macro prohibition (disallows word/vbaProject.bin).
5. Clean rejection of encrypted / password-protected archives.
"""

import io
import zipfile
from typing import Tuple
from app.domain.documents.models import DocumentValidationError

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_DECOMPRESSED_SIZE = 25 * 1024 * 1024  # 25 MB
MAX_ZIP_ENTRIES = 500
MAX_COMPRESSION_RATIO = 100.0

# Executable magic bytes signatures
EXECUTABLE_SIGNATURES = [
    b"MZ",  # DOS / Windows PE
    b"\x7fELF",  # Linux ELF
    b"\xfe\xed\xfa\xce",  # Mach-O 32-bit
    b"\xfe\xed\xfa\xcf",  # Mach-O 64-bit
    b"\xce\xfa\xed\xfe",  # Mach-O reverse
    b"\xcf\xfa\xed\xfe",  # Mach-O reverse
]


def validate_document_safety(file_bytes: bytes, filename: str = "") -> str:
    """
    Validates document safety and returns the canonical format ('docx' or 'pdf').
    Raises DocumentValidationError with a plain message if invalid or hazardous.
    """
    if not file_bytes:
        raise DocumentValidationError("File is empty (0 bytes).", code="EMPTY_FILE")

    if len(file_bytes) > MAX_FILE_SIZE:
        raise DocumentValidationError(
            f"File size ({len(file_bytes)} bytes) exceeds the maximum allowed limit of 5 MB.",
            code="FILE_TOO_LARGE",
        )

    # 1. Check for executable signatures (regardless of file extension)
    for sig in EXECUTABLE_SIGNATURES:
        if file_bytes.startswith(sig):
            raise DocumentValidationError(
                "File validation failed: Executable binary detected by magic bytes signature. "
                "Only DOCX and PDF documents are accepted.",
                code="EXECUTABLE_DETECTED",
            )

    # 2. Check for PDF magic bytes
    if file_bytes.startswith(b"%PDF-"):
        return "pdf"

    # 3. Check for DOCX (ZIP container with word/document.xml)
    if file_bytes.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes), "r") as zf:
                # Check for password protection / encryption
                for zinfo in zf.infolist():
                    if zinfo.flag_bits & 0x1:
                        raise DocumentValidationError(
                            "Password-protected documents are not supported. Please upload an unprotected file.",
                            code="PASSWORD_PROTECTED",
                        )

                entries = zf.infolist()
                # Zip bomb checks
                if len(entries) > MAX_ZIP_ENTRIES:
                    raise DocumentValidationError(
                        f"Zip bomb guard: Archive contains {len(entries)} entries, exceeding safety limit of {MAX_ZIP_ENTRIES}.",
                        code="ZIP_BOMB_ENTRIES",
                    )

                total_uncompressed = sum(z.file_size for z in entries)
                if total_uncompressed > MAX_DECOMPRESSED_SIZE:
                    raise DocumentValidationError(
                        f"Zip bomb guard: Decompressed size ({total_uncompressed} bytes) exceeds safety limit of 25 MB.",
                        code="ZIP_BOMB_SIZE",
                    )

                ratio = total_uncompressed / max(1, len(file_bytes))
                if ratio > MAX_COMPRESSION_RATIO:
                    raise DocumentValidationError(
                        f"Zip bomb guard: Compression ratio ({ratio:.1f}:1) exceeds safety threshold of {MAX_COMPRESSION_RATIO}:1.",
                        code="ZIP_BOMB_RATIO",
                    )

                namelist = set(zf.namelist())
                # Disallow macros (VBA project binaries)
                if any("vbaProject" in name.lower() or name.lower().endswith(".bin") for name in namelist):
                    raise DocumentValidationError(
                        "Macro-enabled documents (.docm or VBA macros) are not permitted for security.",
                        code="MACRO_DETECTED",
                    )

                # Ensure it is a valid Word document
                if "word/document.xml" not in namelist:
                    raise DocumentValidationError(
                        "ZIP archive is not a valid DOCX document (missing word/document.xml).",
                        code="INVALID_DOCX",
                    )

            return "docx"
        except zipfile.BadZipFile:
            raise DocumentValidationError(
                "The uploaded document is corrupted or not a valid archive.",
                code="CORRUPTED_FILE",
            )
        except DocumentValidationError:
            raise
        except Exception as e:
            raise DocumentValidationError(
                f"Failed to inspect document archive: {str(e)}",
                code="ARCHIVE_INSPECTION_FAILED",
            )

    # 4. Check for Image magic bytes (PNG, JPEG, WebP, GIF)
    is_png = file_bytes.startswith(b"\x89PNG")
    is_jpeg = file_bytes.startswith(b"\xff\xd8\xff")
    is_webp = file_bytes.startswith(b"RIFF") and len(file_bytes) >= 12 and file_bytes[8:12] == b"WEBP"
    is_gif = file_bytes.startswith(b"GIF87a") or file_bytes.startswith(b"GIF89a")

    if is_png or is_jpeg or is_webp or is_gif:
        from PIL import Image

        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                width, height = img.size
                if width > 4096 or height > 4096:
                    raise DocumentValidationError(
                        f"Image dimensions ({width}x{height}) exceed maximum allowed dimension of 4096x4096.",
                        code="DIMENSIONS_EXCEEDED",
                    )
                img.load()
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
        return "image"

    # Unsupported format
    raise DocumentValidationError(
        "Invalid file format: Magic bytes signature does not match supported formats. "
        "Allowed formats are DOCX, PDF, PNG, JPEG, WebP, and GIF.",
        code="UNSUPPORTED_FORMAT",
    )

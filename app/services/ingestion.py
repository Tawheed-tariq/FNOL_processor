"""
Document Ingestion Service
--------------------------
Handles PDF upload validation, text extraction via pdfplumber,
and provides a clean text payload to downstream services.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Optional

import pdfplumber

from app.core.config import settings
from app.core.exceptions import (
    DocumentIngestionError,
    FileSizeLimitError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractedDocument:
    """Raw extraction result from a PDF."""
    filename: str
    file_size_bytes: int
    pages: int
    raw_text: str
    page_texts: list[str]

    @property
    def total_characters(self) -> int:
        return len(self.raw_text)


class DocumentIngestionService:
    """
    Validates and extracts text content from PDF byte streams.

    Responsibilities:
    - File type & size guard
    - Page count guard
    - Text extraction via pdfplumber (handles multi-column, tables, forms)
    - Basic quality checks on extracted text
    """

    MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    def ingest(self, filename: str, content: bytes) -> ExtractedDocument:
        """
        Entry point: validate and extract text from raw PDF bytes.

        Args:
            filename: Original filename (used for type sniffing + logging)
            content:  Raw byte content of the uploaded file

        Returns:
            ExtractedDocument with full text and per-page breakdown

        Raises:
            UnsupportedFileTypeError: for non-PDF files
            FileSizeLimitError:       if file exceeds MAX_FILE_SIZE_MB
            DocumentIngestionError:   for corrupt / unreadable PDFs
        """
        logger.info("Ingesting document '%s' (%d bytes)", filename, len(content))

        self._validate_file_type(filename, content)
        self._validate_file_size(filename, len(content))

        return self._extract_text(filename, content)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _validate_file_type(self, filename: str, content: bytes) -> None:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext != "pdf":
            raise UnsupportedFileTypeError(
                f"Only PDF files are supported. Received: '.{ext}'"
            )
        # Verify PDF magic bytes regardless of extension
        if not content.startswith(b"%PDF"):
            raise UnsupportedFileTypeError(
                f"File '{filename}' does not appear to be a valid PDF (bad magic bytes)."
            )

    def _validate_file_size(self, filename: str, size: int) -> None:
        if size > self.MAX_BYTES:
            raise FileSizeLimitError(
                f"File '{filename}' is {size / 1024 / 1024:.1f} MB, "
                f"which exceeds the {settings.MAX_FILE_SIZE_MB} MB limit."
            )

    def _extract_text(self, filename: str, content: bytes) -> ExtractedDocument:
        try:
            buf = io.BytesIO(content)
            page_texts: list[str] = []

            with pdfplumber.open(buf) as pdf:
                total_pages = len(pdf.pages)
                logger.info("PDF has %d pages", total_pages)

                if total_pages > settings.PDF_MAX_PAGES:
                    raise DocumentIngestionError(
                        f"PDF has {total_pages} pages, exceeding the "
                        f"{settings.PDF_MAX_PAGES}-page limit."
                    )

                for i, page in enumerate(pdf.pages):
                    text = self._extract_page_text(page, i + 1)
                    page_texts.append(text)

            combined = "\n\n--- PAGE BREAK ---\n\n".join(page_texts)

            if not combined.strip():
                raise DocumentIngestionError(
                    f"No extractable text found in '{filename}'. "
                    "The PDF may be image-only (scanned). "
                    "OCR pre-processing is required for such documents."
                )

            logger.info(
                "Extracted %d characters from %d pages of '%s'",
                len(combined), total_pages, filename,
            )

            return ExtractedDocument(
                filename=filename,
                file_size_bytes=len(content),
                pages=total_pages,
                raw_text=combined,
                page_texts=page_texts,
            )

        except (UnsupportedFileTypeError, DocumentIngestionError, FileSizeLimitError):
            raise
        except Exception as exc:
            logger.exception("Unexpected error extracting text from '%s'", filename)
            raise DocumentIngestionError(
                f"Failed to extract text from '{filename}': {exc}"
            ) from exc

    def _extract_page_text(self, page, page_num: int) -> str:
        """
        Extract text from a single pdfplumber Page.
        Tries table extraction first (better for form-like ACORD docs),
        then falls back to word-level extraction for natural reading order.
        """
        try:
            # pdfplumber's extract_text preserves layout better for forms
            text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""

            # Additionally attempt to capture table cells that extract_text may miss
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        if row:
                            cells = [str(c).strip() for c in row if c]
                            if cells:
                                line = " | ".join(cells)
                                if line not in text:
                                    text += f"\n{line}"

            return text.strip()
        except Exception as exc:
            logger.warning("Partial text extraction on page %d: %s", page_num, exc)
            return ""
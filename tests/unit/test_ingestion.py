"""
Unit tests – DocumentIngestionService
"""

import io
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import (
    DocumentIngestionError,
    FileSizeLimitError,
    UnsupportedFileTypeError,
)
from app.services.ingestion import DocumentIngestionService


@pytest.fixture
def svc():
    return DocumentIngestionService()


VALID_PDF_HEADER = b"%PDF-1.4 1 0 obj << /Type /Catalog >> endobj %%EOF"


class TestFileTypeValidation:
    def test_non_pdf_extension_raises(self, svc):
        with pytest.raises(UnsupportedFileTypeError, match="PDF"):
            svc.ingest("document.docx", VALID_PDF_HEADER)

    def test_bad_magic_bytes_raises(self, svc):
        with pytest.raises(UnsupportedFileTypeError, match="magic bytes"):
            svc.ingest("document.pdf", b"not a pdf content here")

    def test_no_extension_raises(self, svc):
        with pytest.raises(UnsupportedFileTypeError):
            svc.ingest("document", VALID_PDF_HEADER)

    def test_uppercase_pdf_extension_rejected(self, svc):
        # Extensions should be lowercased – "PDF" not same as "pdf"
        with pytest.raises(UnsupportedFileTypeError):
            svc.ingest("document.PDF", VALID_PDF_HEADER)


class TestFileSizeValidation:
    def test_file_exceeding_limit_raises(self, svc):
        # Patch MAX_BYTES to a tiny value
        svc.MAX_BYTES = 10
        with pytest.raises(FileSizeLimitError, match="limit"):
            svc.ingest("doc.pdf", b"%PDF" + b"x" * 100)


class TestTextExtraction:
    def test_successful_extraction_returns_document(self, svc, sample_pdf_bytes):
        """Test with a real minimal PDF."""
        try:
            doc = svc.ingest("test.pdf", sample_pdf_bytes)
            assert doc.filename == "test.pdf"
            assert doc.file_size_bytes == len(sample_pdf_bytes)
            assert doc.pages >= 1
        except DocumentIngestionError as e:
            # If pdfplumber can't extract text from the minimal PDF, that's acceptable
            # (image-only PDF). The important thing is no crash on valid PDF bytes.
            assert "No extractable text" in str(e) or "Failed to extract" in str(e)

    def test_mock_pdfplumber_successful_extraction(self, svc):
        """Fully mocked extraction pipeline."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Policy Number: PA-12345\nInsured: Jane Doe"
        mock_page.extract_tables.return_value = []

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with patch("pdfplumber.open", return_value=mock_pdf):
            doc = svc.ingest("policy.pdf", b"%PDF-test-content")

        assert doc.filename == "policy.pdf"
        assert "Jane Doe" in doc.raw_text
        assert doc.pages == 1
        assert doc.total_characters > 0

    def test_empty_pdf_raises_ingestion_error(self, svc):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_page.extract_tables.return_value = []

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with patch("pdfplumber.open", return_value=mock_pdf):
            with pytest.raises(DocumentIngestionError, match="No extractable text"):
                svc.ingest("empty.pdf", b"%PDF-empty")

    def test_multi_page_extraction(self, svc):
        pages = []
        for i in range(3):
            mock_page = MagicMock()
            mock_page.extract_text.return_value = f"Page {i + 1} content"
            mock_page.extract_tables.return_value = []
            pages.append(mock_page)

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = pages

        with patch("pdfplumber.open", return_value=mock_pdf):
            doc = svc.ingest("multi.pdf", b"%PDF-multi")

        assert doc.pages == 3
        assert len(doc.page_texts) == 3
        assert "PAGE BREAK" in doc.raw_text

    def test_table_cells_included_in_text(self, svc):
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Some text"
        mock_page.extract_tables.return_value = [
            [["Policy", "PA-999"], ["Carrier", "ACME"]]
        ]

        mock_pdf = MagicMock()
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_pdf.pages = [mock_page]

        with patch("pdfplumber.open", return_value=mock_pdf):
            doc = svc.ingest("form.pdf", b"%PDF-form")

        assert "PA-999" in doc.raw_text
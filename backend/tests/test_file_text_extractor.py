import sys
import os

# Make sure we can import from the backend root, regardless of how pytest is invoked
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from extractors.file_text_extractor import FileTextExtractor


@pytest.fixture
def extractor():
    return FileTextExtractor()


def test_extract_from_txt_returns_correct_text(extractor):
    file_bytes = b"1600 Amphitheatre Pkwy, Mountain View, CA 94043"
    result = extractor.extract("address.txt", file_bytes)
    assert result == "1600 Amphitheatre Pkwy, Mountain View, CA 94043"


def test_extract_from_txt_handles_empty_file(extractor):
    file_bytes = b""
    result = extractor.extract("empty.txt", file_bytes)
    assert result == ""


def test_extract_rejects_unsupported_file_type(extractor):
    file_bytes = b"some content"
    with pytest.raises(ValueError, match="Unsupported file type"):
        extractor.extract("document.docx", file_bytes)


def test_extract_is_case_insensitive_on_extension(extractor):
    file_bytes = b"hello world"
    result = extractor.extract("FILE.TXT", file_bytes)
    assert result == "hello world"


def test_extract_raises_on_undecodable_bytes(extractor):
    # 0xFF is not valid UTF-8 on its own
    file_bytes = b"\xff\xfe\xfd"
    with pytest.raises(ValueError, match="Could not decode text file"):
        extractor.extract("bad_encoding.txt", file_bytes)

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io


def make_text_pdf_bytes(text: str) -> bytes:
    """Helper: builds a simple one-page PDF containing real, extractable text."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 700, text)
    c.save()
    return buffer.getvalue()


def make_blank_pdf_bytes() -> bytes:
    """Helper: builds a one-page PDF with NO text at all (simulates a scanned/blank page)."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.showPage()
    c.save()
    return buffer.getvalue()


def test_extract_from_pdf_with_real_text(extractor):
    pdf_bytes = make_text_pdf_bytes("1600 Amphitheatre Pkwy, Mountain View, CA 94043")
    result = extractor.extract("address.pdf", pdf_bytes)
    assert "1600 Amphitheatre Pkwy" in result


def test_extract_from_blank_pdf_returns_empty_or_ocr_attempt(extractor):
    pdf_bytes = make_blank_pdf_bytes()
    # A blank page has no text and no real image either — pypdf finds nothing,
    # and OCR on a truly blank page should also find nothing (not raise an error).
    result = extractor.extract("blank.pdf", pdf_bytes)
    assert result.strip() == ""


def test_extract_raises_on_corrupted_pdf(extractor):
    corrupted_bytes = b"this is not a real PDF file at all"
    with pytest.raises(ValueError, match="Could not read PDF file"):
        extractor.extract("fake.pdf", corrupted_bytes)
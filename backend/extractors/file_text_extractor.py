from pypdf import PdfReader
from pdf2image import convert_from_bytes
import pytesseract
import io


class FileTextExtractor:
    """Converts an uploaded file (PDF or TXT) into plain text."""

    SUPPORTED_EXTENSIONS = (".pdf", ".txt")

    def extract(self, filename: str, file_bytes: bytes) -> str:
        """
        Routes to the correct extraction method based on file extension.
        Raises ValueError if the file type is unsupported or unreadable.
        """
        extension = self._get_extension(filename)

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {extension}")

        if extension == ".pdf":
            return self._extract_from_pdf(file_bytes)
        else:
            return self._extract_from_txt(file_bytes)

    def _get_extension(self, filename: str) -> str:
        if "." not in filename:
            return ""
        return "." + filename.rsplit(".", 1)[-1].lower()

    def _extract_from_pdf(self, file_bytes: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            page_texts = []
            pages_needing_ocr = []

            for page_number, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    page_texts.append((page_number, page_text))
                else:
                    pages_needing_ocr.append(page_number)

        except Exception as e:
            raise ValueError(f"Could not read PDF file: {e}")

        if pages_needing_ocr:
            ocr_texts = self._extract_via_ocr(file_bytes, pages_needing_ocr)
            page_texts.extend(ocr_texts)

        page_texts.sort(key=lambda item: item[0])
        return "\n".join(text for _, text in page_texts)

    def _extract_via_ocr(self, file_bytes: bytes, page_numbers: list[int]) -> list[tuple[int, str]]:
        try:
            images = convert_from_bytes(file_bytes)
        except Exception as e:
            raise ValueError(f"Could not run OCR on this PDF: {e}")

        results = []
        for page_number in page_numbers:
            if page_number < len(images):
                page_text = pytesseract.image_to_string(images[page_number])
                if page_text:
                    results.append((page_number, page_text))
        return results

    def _extract_from_txt(self, file_bytes: bytes) -> str:
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("Could not decode text file — unsupported encoding")
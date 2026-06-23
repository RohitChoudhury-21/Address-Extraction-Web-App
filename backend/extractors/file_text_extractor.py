from pypdf import PdfReader
import io

class FileTextExtractor:
    """
    Converts an uploaded file (PDF or TXT) into plain text.
    """

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
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n".join(text_parts)
        except Exception as e:
            raise ValueError(f"Could not read PDF file: {e}")

    def _extract_from_txt(self, file_bytes: bytes) -> str:
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ValueError("Could not decode text file — unsupported encoding")
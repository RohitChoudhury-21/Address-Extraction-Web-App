from extractors.file_text_extractor import FileTextExtractor
from clients.smarty_client import SmartyClient
import requests


class AddressExtractionError(Exception):
    """
    Raised for any handled failure in the extraction pipeline, with a user-facing message and code.
    """

    def __init__(self, message: str, code: str, status_code: int = 400):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class AddressExtractionService:
    """
    Coordinates file text extraction and the Smarty API call, and shapes the result.
    """

    MAX_TEXT_BYTES = 64 * 1024  # Smarty's actual limit is 64KB, not 1MB

    def __init__(self, smarty_client: SmartyClient, file_extractor: FileTextExtractor = None):
        self.smarty_client = smarty_client
        self.file_extractor = file_extractor or FileTextExtractor()

    def process(self, filename: str, file_bytes: bytes) -> list[dict]:
        # Step 1: extract text from the file
        try:
            text = self.file_extractor.extract(filename, file_bytes)
        except ValueError as e:
            raise AddressExtractionError(
                message=str(e),
                code="FILE_READ_ERROR",
                status_code=400,
            )

        # Step 2: validate size before calling Smarty
        text_bytes = text.encode("utf-8")
        if len(text_bytes) > self.MAX_TEXT_BYTES:
            raise AddressExtractionError(
                message="This file is too large to process. Please upload a smaller document.",
                code="FILE_TOO_LARGE",
                status_code=400,
            )

        if not text.strip():
            return []  # empty result, not an error — frontend shows "no addresses found"

        # Step 3: call Smarty
        try:
            smarty_response = self.smarty_client.extract_addresses(text)
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status == 401:
                raise AddressExtractionError(
                    message="Address lookup is temporarily unavailable. Please try again later.",
                    code="SERVICE_AUTH_ERROR",
                    status_code=502,
                )
            elif status == 402:
                raise AddressExtractionError(
                    message="We've hit our address lookup limit for now. Please try again later.",
                    code="SERVICE_QUOTA_EXCEEDED",
                    status_code=502,
                )
            else:
                raise AddressExtractionError(
                    message="Something went wrong reaching the address service. Please try again.",
                    code="SERVICE_ERROR",
                    status_code=502,
                )
        except requests.exceptions.RequestException:
            raise AddressExtractionError(
                message="Something went wrong reaching the address service. Please try again.",
                code="SERVICE_UNREACHABLE",
                status_code=502,
            )

        # Step 4: reshape Smarty's response into a flat structure for the frontend
        return self._format_addresses(smarty_response)

    def _format_addresses(self, smarty_response: dict) -> list[dict]:
        addresses = smarty_response.get("addresses", [])
        formatted = []
        for addr in addresses:
            api_output = addr.get("api_output", [])
            components = api_output[0].get("components", {}) if api_output else {}
            formatted.append({
                "input_text": addr.get("text", ""),
                "primary_number": components.get("primary_number", ""),
                "street_name": components.get("street_name", ""),
                "street_suffix": components.get("street_suffix", ""),
                "city_name": components.get("city_name", ""),
                "state_abbreviation": components.get("state_abbreviation", ""),
                "zipcode": components.get("zipcode", ""),
            })
        return formatted
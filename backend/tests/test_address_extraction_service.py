import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import Mock
import requests

from services.address_extraction_service import AddressExtractionService, AddressExtractionError


@pytest.fixture
def fake_smarty_client():
    """A stand-in for SmartyClient that we fully control — no real network calls."""
    return Mock()


@pytest.fixture
def service(fake_smarty_client):
    return AddressExtractionService(smarty_client=fake_smarty_client)


def test_process_returns_formatted_addresses_on_success(service, fake_smarty_client):
    fake_smarty_client.extract_addresses.return_value = {
        "addresses": [
            {
                "text": "1600 Amphitheatre Pkwy, Mountain View, CA 94043",
                "api_output": [
                    {
                        "components": {
                            "primary_number": "1600",
                            "street_name": "Amphitheatre",
                            "street_suffix": "Pkwy",
                            "city_name": "Mountain View",
                            "state_abbreviation": "CA",
                            "zipcode": "94043",
                        }
                    }
                ],
            }
        ]
    }

    result = service.process("test.txt", b"1600 Amphitheatre Pkwy, Mountain View, CA 94043")

    assert len(result) == 1
    assert result[0]["primary_number"] == "1600"
    assert result[0]["city_name"] == "Mountain View"
    fake_smarty_client.extract_addresses.assert_called_once()


def test_process_returns_empty_list_for_empty_text(service, fake_smarty_client):
    result = service.process("empty.txt", b"")

    assert result == []
    fake_smarty_client.extract_addresses.assert_not_called()


def test_process_raises_file_too_large_error(service, fake_smarty_client):
    huge_text = "a" * (70 * 1024)  # 70KB, over the 64KB limit
    with pytest.raises(AddressExtractionError) as exc_info:
        service.process("huge.txt", huge_text.encode("utf-8"))

    assert exc_info.value.code == "FILE_TOO_LARGE"
    fake_smarty_client.extract_addresses.assert_not_called()


def test_process_raises_unsupported_file_type_error(service, fake_smarty_client):
    with pytest.raises(AddressExtractionError) as exc_info:
        service.process("file.docx", b"some content")

    assert exc_info.value.code == "FILE_READ_ERROR"


def test_process_handles_smarty_401_as_auth_error(service, fake_smarty_client):
    fake_response = Mock()
    fake_response.status_code = 401
    fake_smarty_client.extract_addresses.side_effect = requests.exceptions.HTTPError(response=fake_response)

    with pytest.raises(AddressExtractionError) as exc_info:
        service.process("test.txt", b"some address text")

    assert exc_info.value.code == "SERVICE_AUTH_ERROR"


def test_process_handles_smarty_402_as_quota_error(service, fake_smarty_client):
    fake_response = Mock()
    fake_response.status_code = 402
    fake_smarty_client.extract_addresses.side_effect = requests.exceptions.HTTPError(response=fake_response)

    with pytest.raises(AddressExtractionError) as exc_info:
        service.process("test.txt", b"some address text")

    assert exc_info.value.code == "SERVICE_QUOTA_EXCEEDED"


def test_process_handles_connection_failure(service, fake_smarty_client):
    fake_smarty_client.extract_addresses.side_effect = requests.exceptions.ConnectionError()

    with pytest.raises(AddressExtractionError) as exc_info:
        service.process("test.txt", b"some address text")

    assert exc_info.value.code == "SERVICE_UNREACHABLE"


def test_process_uses_cache_on_second_identical_call(service, fake_smarty_client):
    fake_smarty_client.extract_addresses.return_value = {
        "addresses": [
            {
                "text": "1600 Amphitheatre Pkwy",
                "api_output": [{"components": {"primary_number": "1600"}}],
            }
        ]
    }

    text_bytes = b"1600 Amphitheatre Pkwy, Mountain View, CA 94043"

    first_result = service.process("test.txt", text_bytes)
    second_result = service.process("test.txt", text_bytes)

    assert first_result == second_result
    # Smarty should only have been called ONCE, even though we called process() twice
    fake_smarty_client.extract_addresses.assert_called_once()

def test_process_does_not_use_cache_when_content_differs_with_same_filename(service, fake_smarty_client):
    fake_smarty_client.extract_addresses.return_value = {
        "addresses": [
            {
                "text": "1600 Amphitheatre Pkwy",
                "api_output": [{"components": {"primary_number": "1600"}}],
            }
        ]
    }

    # Same filename both times, but DIFFERENT content
    service.process("address.txt", b"1600 Amphitheatre Pkwy, Mountain View, CA 94043")
    service.process("address.txt", b"1600 Amphitheatre Pkwy, Mountain View, CA 94043 plus a new address: 350 5th Ave, New York, NY 10118")

    # Since the content differs, Smarty should have been called TWICE, not once
    assert fake_smarty_client.extract_addresses.call_count == 2
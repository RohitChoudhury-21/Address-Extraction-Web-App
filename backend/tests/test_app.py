import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_extract_endpoint_returns_addresses_for_valid_txt(client):
    file_content = b"1600 Amphitheatre Pkwy, Mountain View, CA 94043"

    with patch("app.extraction_service.smarty_client.extract_addresses") as mock_extract:
        mock_extract.return_value = {
            "addresses": [
                {
                    "text": "1600 Amphitheatre Pkwy, Mountain View, CA 94043",
                    "api_output": [
                        {"components": {"primary_number": "1600", "city_name": "Mountain View"}}
                    ],
                }
            ]
        }

        response = client.post(
            "/extract",
            files={"file": ("address.txt", file_content, "text/plain")},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["addresses"]) == 1
    assert data["addresses"][0]["primary_number"] == "1600"


def test_extract_endpoint_rejects_unsupported_file_type(client):
    response = client.post(
        "/extract",
        files={"file": ("document.docx", b"some content", "application/octet-stream")},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "FILE_READ_ERROR"


def test_extract_endpoint_rejects_oversized_file(client):
    huge_content = b"a" * (6 * 1024 * 1024)  # 6MB, over the 5MB cap

    response = client.post(
        "/extract",
        files={"file": ("huge.txt", huge_content, "text/plain")},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "UPLOAD_TOO_LARGE"


def test_extract_endpoint_returns_empty_list_for_empty_file(client):
    response = client.post(
        "/extract",
        files={"file": ("empty.txt", b"", "text/plain")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["addresses"] == []


def test_extract_endpoint_requires_a_file(client):
    response = client.post("/extract")

    # FastAPI's own validation should reject this before our code even runs
    assert response.status_code == 422
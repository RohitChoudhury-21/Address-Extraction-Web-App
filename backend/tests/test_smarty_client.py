import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, Mock
import requests

from clients.smarty_client import SmartyClient


@pytest.fixture
def client():
    return SmartyClient(auth_id="fake_id", auth_token="fake_token")


@patch("clients.smarty_client.requests.post")
def test_extract_addresses_sends_correct_request(mock_post, client):
    mock_response = Mock()
    mock_response.json.return_value = {"addresses": []}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    client.extract_addresses("123 Main St")

    # Check the call was made with the right method, URL, headers, and body
    mock_post.assert_called_once()
    call_args = mock_post.call_args

    assert call_args.args[0] == "https://us-extract.api.smarty.com/"
    assert call_args.kwargs["params"] == {"auth-id": "fake_id", "auth-token": "fake_token"}
    assert call_args.kwargs["headers"] == {"Content-Type": "text/plain; charset=utf-8"}
    assert call_args.kwargs["data"] == b"123 Main St"
    assert call_args.kwargs["timeout"] == 15


@patch("clients.smarty_client.requests.post")
def test_extract_addresses_returns_parsed_json(mock_post, client):
    mock_response = Mock()
    mock_response.json.return_value = {"addresses": [{"text": "fake address"}]}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    result = client.extract_addresses("some text")

    assert result == {"addresses": [{"text": "fake address"}]}


@patch("clients.smarty_client.requests.post")
def test_extract_addresses_raises_on_http_error(mock_post, client):
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
    mock_post.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        client.extract_addresses("some text")


@patch("clients.smarty_client.requests.post")
def test_extract_addresses_raises_on_connection_error(mock_post, client):
    mock_post.side_effect = requests.exceptions.ConnectionError("network down")

    with pytest.raises(requests.exceptions.ConnectionError):
        client.extract_addresses("some text")
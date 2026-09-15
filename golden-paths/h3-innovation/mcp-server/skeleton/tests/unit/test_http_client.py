"""Unit tests for HTTP client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from src.infrastructure.http_client import HttpClient, HttpClientError


class TestHttpClient:
    """Tests for HttpClient."""

    @pytest.mark.asyncio
    async def test_client_initialization(self) -> None:
        """Test HTTP client initialization."""
        client = HttpClient(
            base_url="https://api.example.com",
            timeout=30,
            api_key="test-key",
        )

        assert client.base_url == "https://api.example.com"
        assert client.timeout == 30
        assert client.api_key == "test-key"

    @pytest.mark.asyncio
    async def test_get_headers_with_api_key(self) -> None:
        """Test header generation with API key."""
        client = HttpClient(
            base_url="https://api.example.com",
            api_key="test-key",
        )

        headers = client._get_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-key"
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_get_headers_without_api_key(self) -> None:
        """Test header generation without API key."""
        client = HttpClient(base_url="https://api.example.com")

        headers = client._get_headers()

        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_get_without_initialization(self) -> None:
        """Test GET request without initialization."""
        client = HttpClient(base_url="https://api.example.com")

        with pytest.raises(HttpClientError) as exc_info:
            await client.get("/endpoint")

        assert "not initialized" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_request_success(self) -> None:
        """Test successful GET request."""
        async with HttpClient(
            base_url="https://api.example.com",
            api_key="test-key",
        ) as client:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"status": "success", "data": "test"}
            mock_response.status_code = 200

            with patch.object(client._client, "get", return_value=mock_response):
                result = await client.get("/policies/123")

                assert result["status"] == "success"
                assert result["data"] == "test"

    @pytest.mark.asyncio
    async def test_post_request_success(self) -> None:
        """Test successful POST request."""
        async with HttpClient(
            base_url="https://api.example.com",
            api_key="test-key",
        ) as client:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"id": "123", "created": True}
            mock_response.status_code = 201

            with patch.object(client._client, "post", return_value=mock_response):
                result = await client.post("/policies", {"name": "Test Policy"})

                assert result["id"] == "123"
                assert result["created"] is True

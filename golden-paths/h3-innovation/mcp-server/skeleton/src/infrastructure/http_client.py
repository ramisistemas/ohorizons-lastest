"""HTTP client wrapper for external API calls."""

import httpx
from typing import Any, Optional, Dict
from src.infrastructure.logger import setup_logger
from src.infrastructure.config import get_settings

logger = setup_logger(__name__)


class HttpClientError(Exception):
    """Raised when HTTP client encounters an error."""

    pass


class HttpClient:
    """Async HTTP client wrapper with built-in error handling and logging."""

    def __init__(self, base_url: str, timeout: int = 30, api_key: Optional[str] = None):
        """
        Initialize HTTP client.

        Args:
            base_url: Base URL for API calls
            timeout: Request timeout in seconds
            api_key: Optional API key for authentication
        """
        self.base_url = base_url
        self.timeout = timeout
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "HttpClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def get(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Perform GET request.

        Args:
            endpoint: API endpoint path
            **kwargs: Additional query parameters

        Returns:
            Response JSON as dictionary

        Raises:
            HttpClientError: If request fails
        """
        if not self._client:
            raise HttpClientError("Client not initialized. Use async context manager.")

        try:
            response = await self._client.get(
                endpoint,
                headers=self._get_headers(),
                params=kwargs,
            )
            response.raise_for_status()
            logger.debug(f"GET {endpoint} - Status: {response.status_code}")
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error on GET {endpoint}: {str(e)}")
            raise HttpClientError(f"Failed to GET {endpoint}: {str(e)}") from e

    async def post(self, endpoint: str, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """
        Perform POST request.

        Args:
            endpoint: API endpoint path
            data: Request body data
            **kwargs: Additional parameters

        Returns:
            Response JSON as dictionary

        Raises:
            HttpClientError: If request fails
        """
        if not self._client:
            raise HttpClientError("Client not initialized. Use async context manager.")

        try:
            response = await self._client.post(
                endpoint,
                headers=self._get_headers(),
                json=data,
                **kwargs,
            )
            response.raise_for_status()
            logger.debug(f"POST {endpoint} - Status: {response.status_code}")
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error on POST {endpoint}: {str(e)}")
            raise HttpClientError(f"Failed to POST {endpoint}: {str(e)}") from e

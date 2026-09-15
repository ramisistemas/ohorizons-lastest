"""Policy repository implementation."""

from typing import Optional
from datetime import datetime

from src.domain.models import PolicyInfo, PolicyType, PolicyStatus
from src.domain.repositories import IPolicyRepository
from src.domain.exceptions import PolicyNotFoundError, ExternalServiceError
from src.infrastructure.http_client import HttpClient, HttpClientError
from src.infrastructure.logger import setup_logger
from src.infrastructure.config import get_settings

logger = setup_logger(__name__)


class PolicyRepository(IPolicyRepository):
    """Repository implementation for policy operations."""

    def __init__(self) -> None:
        """Initialize policy repository."""
        settings = get_settings()
        self.base_url = settings.insurance_api_base_url
        self.api_key = settings.insurance_api_key
        self.timeout = settings.insurance_api_timeout

    async def get_policy(self, policy_id: str) -> Optional[PolicyInfo]:
        """
        Get policy information by ID from external API.

        Args:
            policy_id: The policy identifier

        Returns:
            PolicyInfo if found, None otherwise

        Raises:
            ExternalServiceError: If API call fails
        """
        try:
            async with HttpClient(
                base_url=self.base_url,
                timeout=self.timeout,
                api_key=self.api_key,
            ) as client:
                response = await client.get(f"/policies/{policy_id}")
                logger.info(f"Retrieved policy {policy_id}")
                return self._map_response_to_policy(response)
        except HttpClientError as e:
            logger.error(f"Failed to retrieve policy {policy_id}: {str(e)}")
            raise ExternalServiceError(
                f"Failed to retrieve policy from backend: {str(e)}",
                code="POLICY_RETRIEVAL_FAILED",
            ) from e

    async def get_policies_by_customer(self, customer_name: str) -> list[PolicyInfo]:
        """
        Get all policies for a customer from external API.

        Args:
            customer_name: The customer name

        Returns:
            List of policies for the customer

        Raises:
            ExternalServiceError: If API call fails
        """
        try:
            async with HttpClient(
                base_url=self.base_url,
                timeout=self.timeout,
                api_key=self.api_key,
            ) as client:
                response = await client.get(
                    "/policies",
                    customer_name=customer_name,
                )
                logger.info(f"Retrieved policies for customer {customer_name}")
                policies = [self._map_response_to_policy(p) for p in response.get("policies", [])]
                return policies
        except HttpClientError as e:
            logger.error(f"Failed to retrieve policies for {customer_name}: {str(e)}")
            raise ExternalServiceError(
                f"Failed to retrieve policies from backend: {str(e)}",
                code="POLICIES_RETRIEVAL_FAILED",
            ) from e

    @staticmethod
    def _map_response_to_policy(data: dict) -> PolicyInfo:
        """
        Map API response to PolicyInfo domain model.

        Args:
            data: Raw API response data

        Returns:
            PolicyInfo instance

        Raises:
            ValueError: If data is invalid
        """
        try:
            return PolicyInfo(
                policy_id=data["policy_id"],
                customer_name=data["customer_name"],
                policy_type=data["policy_type"],
                status=data["status"],
                monthly_premium=float(data["monthly_premium"]),
                coverage_amount=float(data["coverage_amount"]),
                start_date=datetime.fromisoformat(data["start_date"]),
                expiry_date=(
                    datetime.fromisoformat(data["expiry_date"])
                    if data.get("expiry_date")
                    else None
                ),
            )
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Failed to map policy data: {str(e)}")
            raise ValueError(f"Invalid policy data structure: {str(e)}") from e

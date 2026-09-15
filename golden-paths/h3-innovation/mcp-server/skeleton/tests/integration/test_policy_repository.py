"""Integration tests for policy repository."""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from src.infrastructure.repositories import PolicyRepository
from src.domain.models import PolicyType, PolicyStatus
from src.domain.exceptions import ExternalServiceError


class TestPolicyRepositoryIntegration:
    """Integration tests for PolicyRepository."""

    @pytest.mark.asyncio
    async def test_get_policy_integration(self) -> None:
        """Test getting a policy through the repository."""
        # This would require mocking the HTTP client in real integration tests
        repository = PolicyRepository()

        # Mock the HTTP client response
        mock_response = {
            "policy_id": "POL-2024-001",
            "customer_name": "John Doe",
            "policy_type": "auto",
            "status": "active",
            "monthly_premium": 125.50,
            "coverage_amount": 50000.00,
            "start_date": "2023-01-01T00:00:00",
            "expiry_date": "2024-12-31T00:00:00",
        }

        with patch("src.infrastructure.repositories.HttpClient") as mock_http:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_http.return_value = mock_client_instance

            # Act
            policy = await repository.get_policy("POL-2024-001")

            # Assert
            assert policy is not None
            assert policy.policy_id == "POL-2024-001"
            assert policy.customer_name == "John Doe"
            assert policy.policy_type == PolicyType.AUTO
            assert policy.status == PolicyStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_policies_by_customer_integration(self) -> None:
        """Test getting policies by customer through the repository."""
        repository = PolicyRepository()

        mock_response = {
            "policies": [
                {
                    "policy_id": "POL-2024-001",
                    "customer_name": "John Doe",
                    "policy_type": "auto",
                    "status": "active",
                    "monthly_premium": 125.50,
                    "coverage_amount": 50000.00,
                    "start_date": "2023-01-01T00:00:00",
                    "expiry_date": "2024-12-31T00:00:00",
                },
                {
                    "policy_id": "POL-2024-002",
                    "customer_name": "John Doe",
                    "policy_type": "home",
                    "status": "active",
                    "monthly_premium": 250.00,
                    "coverage_amount": 300000.00,
                    "start_date": "2023-06-01T00:00:00",
                    "expiry_date": "2025-05-31T00:00:00",
                },
            ]
        }

        with patch("src.infrastructure.repositories.HttpClient") as mock_http:
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_http.return_value = mock_client_instance

            # Act
            policies = await repository.get_policies_by_customer("John Doe")

            # Assert
            assert len(policies) == 2
            assert policies[0].policy_id == "POL-2024-001"
            assert policies[1].policy_id == "POL-2024-002"

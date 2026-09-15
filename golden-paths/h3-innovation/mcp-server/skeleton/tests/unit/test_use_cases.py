"""Unit tests for application use cases."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from src.application.use_cases import GetPolicyUseCase, GetCustomerPoliciesUseCase
from src.domain.models import PolicyInfo, PolicyType, PolicyStatus
from src.domain.exceptions import PolicyNotFoundError
from datetime import datetime


class TestGetPolicyUseCase:
    """Tests for GetPolicyUseCase."""

    @pytest.mark.asyncio
    async def test_execute_policy_found(self) -> None:
        """Test executing use case when policy is found."""
        # Arrange
        sample_policy = PolicyInfo(
            policy_id="POL-2024-001",
            customer_name="John Doe",
            policy_type=PolicyType.AUTO,
            status=PolicyStatus.ACTIVE,
            monthly_premium=125.50,
            coverage_amount=50000.00,
            start_date=datetime(2023, 1, 1),
            expiry_date=datetime(2024, 12, 31),
        )

        mock_repository = AsyncMock()
        mock_repository.get_policy.return_value = sample_policy

        use_case = GetPolicyUseCase(mock_repository)

        # Act
        result = await use_case.execute("POL-2024-001")

        # Assert
        assert result.policy_id == "POL-2024-001"
        assert result.customer_name == "John Doe"
        assert result.status == PolicyStatus.ACTIVE
        mock_repository.get_policy.assert_called_once_with("POL-2024-001")

    @pytest.mark.asyncio
    async def test_execute_policy_not_found(self) -> None:
        """Test executing use case when policy is not found."""
        # Arrange
        mock_repository = AsyncMock()
        mock_repository.get_policy.return_value = None

        use_case = GetPolicyUseCase(mock_repository)

        # Act & Assert
        with pytest.raises(PolicyNotFoundError) as exc_info:
            await use_case.execute("NON-EXISTENT")

        assert "not found" in str(exc_info.value).lower()
        mock_repository.get_policy.assert_called_once_with("NON-EXISTENT")


class TestGetCustomerPoliciesUseCase:
    """Tests for GetCustomerPoliciesUseCase."""

    @pytest.mark.asyncio
    async def test_execute_policies_found(self) -> None:
        """Test executing use case when policies are found."""
        # Arrange
        policies = [
            PolicyInfo(
                policy_id="POL-2024-001",
                customer_name="John Doe",
                policy_type=PolicyType.AUTO,
                status=PolicyStatus.ACTIVE,
                monthly_premium=125.50,
                coverage_amount=50000.00,
                start_date=datetime(2023, 1, 1),
                expiry_date=datetime(2024, 12, 31),
            ),
            PolicyInfo(
                policy_id="POL-2024-002",
                customer_name="John Doe",
                policy_type=PolicyType.HOME,
                status=PolicyStatus.ACTIVE,
                monthly_premium=250.00,
                coverage_amount=300000.00,
                start_date=datetime(2023, 6, 1),
                expiry_date=datetime(2025, 5, 31),
            ),
        ]

        mock_repository = AsyncMock()
        mock_repository.get_policies_by_customer.return_value = policies

        use_case = GetCustomerPoliciesUseCase(mock_repository)

        # Act
        result = await use_case.execute("John Doe")

        # Assert
        assert len(result) == 2
        assert result[0].policy_id == "POL-2024-001"
        assert result[1].policy_id == "POL-2024-002"
        mock_repository.get_policies_by_customer.assert_called_once_with("John Doe")

    @pytest.mark.asyncio
    async def test_execute_no_policies(self) -> None:
        """Test executing use case when no policies are found."""
        # Arrange
        mock_repository = AsyncMock()
        mock_repository.get_policies_by_customer.return_value = []

        use_case = GetCustomerPoliciesUseCase(mock_repository)

        # Act
        result = await use_case.execute("Unknown Customer")

        # Assert
        assert result == []
        mock_repository.get_policies_by_customer.assert_called_once_with("Unknown Customer")

    @pytest.mark.asyncio
    async def test_execute_empty_customer_name(self) -> None:
        """Test executing use case with empty customer name."""
        # Arrange
        mock_repository = AsyncMock()
        use_case = GetCustomerPoliciesUseCase(mock_repository)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await use_case.execute("")

        assert "cannot be empty" in str(exc_info.value).lower()

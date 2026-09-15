"""Unit tests configuration and fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.domain.models import PolicyInfo, PolicyType, PolicyStatus
from datetime import datetime


@pytest.fixture
def sample_policy() -> PolicyInfo:
    """Create a sample policy for testing."""
    return PolicyInfo(
        policy_id="POL-2024-001",
        customer_name="John Doe",
        policy_type=PolicyType.AUTO,
        status=PolicyStatus.ACTIVE,
        monthly_premium=125.50,
        coverage_amount=50000.00,
        start_date=datetime(2023, 1, 1),
        expiry_date=datetime(2024, 12, 31),
    )


@pytest.fixture
def mock_policy_repository() -> AsyncMock:
    """Create a mock policy repository."""
    return AsyncMock()

"""Unit tests for domain models."""

import pytest
from datetime import datetime

from src.domain.models import PolicyInfo, PolicyType, PolicyStatus, SystemStatus


class TestPolicyInfo:
    """Tests for PolicyInfo model."""

    def test_policy_creation(self) -> None:
        """Test creating a valid policy."""
        policy = PolicyInfo(
            policy_id="POL-001",
            customer_name="Jane Smith",
            policy_type=PolicyType.HOME,
            status=PolicyStatus.ACTIVE,
            monthly_premium=200.00,
            coverage_amount=300000.00,
            start_date=datetime(2023, 1, 1),
            expiry_date=datetime(2024, 12, 31),
        )

        assert policy.policy_id == "POL-001"
        assert policy.customer_name == "Jane Smith"
        assert policy.policy_type == PolicyType.HOME
        assert policy.status == PolicyStatus.ACTIVE

    def test_policy_without_expiry_date(self) -> None:
        """Test creating a policy without expiry date."""
        policy = PolicyInfo(
            policy_id="POL-002",
            customer_name="Bob Johnson",
            policy_type=PolicyType.LIFE,
            status=PolicyStatus.ACTIVE,
            monthly_premium=150.00,
            coverage_amount=500000.00,
            start_date=datetime(2023, 1, 1),
        )

        assert policy.expiry_date is None
        assert policy.policy_id == "POL-002"

    def test_policy_serialization(self) -> None:
        """Test serializing policy to JSON."""
        policy = PolicyInfo(
            policy_id="POL-003",
            customer_name="Alice Brown",
            policy_type=PolicyType.AUTO,
            status=PolicyStatus.PENDING,
            monthly_premium=125.50,
            coverage_amount=50000.00,
            start_date=datetime(2023, 1, 1),
        )

        data = policy.model_dump(mode="json")

        assert data["policy_id"] == "POL-003"
        assert data["customer_name"] == "Alice Brown"
        assert data["policy_type"] == "auto"
        assert data["status"] == "pending"


class TestSystemStatus:
    """Tests for SystemStatus model."""

    def test_system_status_creation(self) -> None:
        """Test creating system status."""
        status = SystemStatus(
            status="healthy",
            uptime_seconds=3600,
            version="1.0.0",
            is_ready=True,
        )

        assert status.status == "healthy"
        assert status.uptime_seconds == 3600
        assert status.version == "1.0.0"
        assert status.is_ready is True

    def test_system_status_default_values(self) -> None:
        """Test system status with default values."""
        status = SystemStatus(
            uptime_seconds=7200,
            version="2.0.0",
        )

        assert status.status == "healthy"
        assert status.is_ready is True
        assert status.timestamp is not None

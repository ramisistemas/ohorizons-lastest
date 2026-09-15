"""Domain models and value objects."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PolicyType(str, Enum):
    """Insurance policy types."""

    AUTO = "auto"
    HOME = "home"
    HEALTH = "health"
    LIFE = "life"


class PolicyStatus(str, Enum):
    """Insurance policy status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    PENDING = "pending"


class PolicyInfo(BaseModel):
    """Policy information value object."""

    policy_id: str = Field(..., description="Unique policy identifier")
    customer_name: str = Field(..., description="Customer name")
    policy_type: PolicyType = Field(..., description="Type of policy")
    status: PolicyStatus = Field(..., description="Current policy status")
    monthly_premium: float = Field(..., description="Monthly premium amount")
    coverage_amount: float = Field(..., description="Coverage amount")
    start_date: datetime = Field(..., description="Policy start date")
    expiry_date: Optional[datetime] = Field(
        default=None, description="Policy expiry date"
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class SystemStatus(BaseModel):
    """System health status value object."""

    status: str = Field(
        default="healthy", description="Overall system status"
    )
    uptime_seconds: int = Field(..., description="Server uptime in seconds")
    version: str = Field(..., description="Server version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Status check timestamp"
    )
    is_ready: bool = Field(
        default=True, description="Whether server is ready to serve requests"
    )

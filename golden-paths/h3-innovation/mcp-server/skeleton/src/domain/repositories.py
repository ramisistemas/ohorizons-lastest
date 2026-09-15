"""Domain repositories (interfaces)."""

from abc import ABC, abstractmethod
from typing import Optional

from src.domain.models import PolicyInfo


class IPolicyRepository(ABC):
    """Repository interface for policy operations."""

    @abstractmethod
    async def get_policy(self, policy_id: str) -> Optional[PolicyInfo]:
        """
        Get policy information by ID.

        Args:
            policy_id: The policy identifier

        Returns:
            PolicyInfo if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_policies_by_customer(self, customer_name: str) -> list[PolicyInfo]:
        """
        Get all policies for a customer.

        Args:
            customer_name: The customer name

        Returns:
            List of policies for the customer
        """
        pass

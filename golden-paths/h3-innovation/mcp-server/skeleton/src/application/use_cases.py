"""Use cases for policy operations."""

import logging
from typing import Optional
from src.domain.models import PolicyInfo
from src.domain.repositories import IPolicyRepository
from src.domain.exceptions import PolicyNotFoundError

logger = logging.getLogger(__name__)


class GetPolicyUseCase:
    """Use case for retrieving policy information."""

    def __init__(self, policy_repository: IPolicyRepository) -> None:
        """
        Initialize use case with repository.

        Args:
            policy_repository: Repository for policy operations
        """
        self.policy_repository = policy_repository

    async def execute(self, policy_id: str) -> PolicyInfo:
        """
        Execute the get policy use case.

        Args:
            policy_id: The policy identifier

        Returns:
            PolicyInfo for the requested policy

        Raises:
            PolicyNotFoundError: If policy not found
        """
        logger.info(f"Executing GetPolicyUseCase for policy {policy_id}")

        policy = await self.policy_repository.get_policy(policy_id)

        if not policy:
            logger.warning(f"Policy {policy_id} not found")
            raise PolicyNotFoundError(
                f"Policy {policy_id} not found",
                code="POLICY_NOT_FOUND",
                details={"policy_id": policy_id},
            )

        logger.info(f"Successfully retrieved policy {policy_id}")
        return policy


class GetCustomerPoliciesUseCase:
    """Use case for retrieving all policies of a customer."""

    def __init__(self, policy_repository: IPolicyRepository) -> None:
        """
        Initialize use case with repository.

        Args:
            policy_repository: Repository for policy operations
        """
        self.policy_repository = policy_repository

    async def execute(self, customer_name: str) -> list[PolicyInfo]:
        """
        Execute the get customer policies use case.

        Args:
            customer_name: The customer name

        Returns:
            List of policies for the customer

        Raises:
            ValueError: If customer_name is invalid
        """
        if not customer_name or not customer_name.strip():
            raise ValueError("Customer name cannot be empty")

        logger.info(f"Executing GetCustomerPoliciesUseCase for {customer_name}")

        policies = await self.policy_repository.get_policies_by_customer(customer_name)

        logger.info(f"Retrieved {len(policies)} policies for {customer_name}")
        return policies

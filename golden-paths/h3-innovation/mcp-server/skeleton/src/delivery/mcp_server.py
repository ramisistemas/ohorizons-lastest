"""MCP Server implementation with tools and resources."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any

import mcp.server.stdio
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    Resource,
    ResourceTemplate,
)

from src.infrastructure.config import get_settings
from src.infrastructure.logger import setup_logger
from src.infrastructure.repositories import PolicyRepository
from src.application.use_cases import GetPolicyUseCase, GetCustomerPoliciesUseCase
from src.domain.exceptions import DomainException

logger = setup_logger(__name__)

# Global variables
_server: Server | None = None
_start_time: datetime = datetime.utcnow()
_policy_use_case: GetPolicyUseCase | None = None
_customer_policies_use_case: GetCustomerPoliciesUseCase | None = None


def _initialize_use_cases() -> None:
    """Initialize use cases with repository."""
    global _policy_use_case, _customer_policies_use_case

    policy_repository = PolicyRepository()
    _policy_use_case = GetPolicyUseCase(policy_repository)
    _customer_policies_use_case = GetCustomerPoliciesUseCase(policy_repository)


async def _handle_get_policy_info(
    policy_id: str | None = None,
) -> list[TextContent]:
    """
    Handle get_policy_info tool call.

    Args:
        policy_id: The policy identifier to retrieve

    Returns:
        List containing policy information or error message
    """
    if not policy_id:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": "policy_id is required",
                        "code": "INVALID_INPUT",
                    }
                ),
            )
        ]

    try:
        if not _policy_use_case:
            raise RuntimeError("Use case not initialized")

        policy = await _policy_use_case.execute(policy_id)

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "policy": policy.model_dump(mode="json"),
                        "success": True,
                    }
                ),
            )
        ]
    except DomainException as e:
        logger.error(f"Domain error in get_policy_info: {str(e)}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": e.message,
                        "code": e.code,
                        "details": e.details,
                    }
                ),
            )
        ]
    except Exception as e:
        logger.error(f"Unexpected error in get_policy_info: {str(e)}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": "Internal server error",
                        "code": "INTERNAL_ERROR",
                    }
                ),
            )
        ]


async def _handle_get_customer_policies(
    customer_name: str | None = None,
) -> list[TextContent]:
    """
    Handle get_customer_policies tool call.

    Args:
        customer_name: The customer name

    Returns:
        List containing customer policies or error message
    """
    if not customer_name:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": "customer_name is required",
                        "code": "INVALID_INPUT",
                    }
                ),
            )
        ]

    try:
        if not _customer_policies_use_case:
            raise RuntimeError("Use case not initialized")

        policies = await _customer_policies_use_case.execute(customer_name)

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "policies": [p.model_dump(mode="json") for p in policies],
                        "count": len(policies),
                        "success": True,
                    }
                ),
            )
        ]
    except DomainException as e:
        logger.error(f"Domain error in get_customer_policies: {str(e)}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": e.message,
                        "code": e.code,
                        "details": e.details,
                    }
                ),
            )
        ]
    except Exception as e:
        logger.error(f"Unexpected error in get_customer_policies: {str(e)}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": "Internal server error",
                        "code": "INTERNAL_ERROR",
                    }
                ),
            )
        ]


async def _handle_get_system_status() -> list[TextContent]:
    """
    Handle system_status resource read.

    Returns:
        List containing system status information
    """
    settings = get_settings()
    uptime = datetime.utcnow() - _start_time

    status_data = {
        "status": "healthy",
        "version": settings.server_version,
        "uptime_seconds": int(uptime.total_seconds()),
        "timestamp": datetime.utcnow().isoformat(),
        "is_ready": True,
    }

    return [
        TextContent(
            type="text",
            text=json.dumps(status_data, indent=2),
        )
    ]


async def _process_tool_call(
    name: str, arguments: dict[str, Any]
) -> list[TextContent]:
    """
    Process tool calls from MCP client.

    Args:
        name: Tool name
        arguments: Tool arguments

    Returns:
        List of response contents
    """
    logger.info(f"Processing tool call: {name} with arguments: {arguments}")

    if name == "get_policy_info":
        return await _handle_get_policy_info(
            policy_id=arguments.get("policy_id")
        )
    elif name == "get_customer_policies":
        return await _handle_get_customer_policies(
            customer_name=arguments.get("customer_name")
        )
    else:
        logger.warning(f"Unknown tool: {name}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": f"Unknown tool: {name}",
                        "code": "UNKNOWN_TOOL",
                    }
                ),
            )
        ]


async def _handle_resource_read(uri: str) -> list[TextContent]:
    """
    Handle resource read requests.

    Args:
        uri: Resource URI

    Returns:
        List of resource contents
    """
    logger.info(f"Reading resource: {uri}")

    if uri == "system://status":
        return await _handle_get_system_status()
    else:
        logger.warning(f"Unknown resource: {uri}")
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "error": f"Unknown resource: {uri}",
                        "code": "UNKNOWN_RESOURCE",
                    }
                ),
            )
        ]


async def _main() -> None:
    """Main server initialization and event loop."""
    global _server

    logger.info("Starting MCP Enterprise Template Server")

    settings = get_settings()
    logger.info(f"Server: {settings.server_name} v{settings.server_version}")

    # Initialize use cases
    _initialize_use_cases()

    # Create MCP server
    _server = Server(name=settings.server_name)

    # Define tools
    tools: list[Tool] = [
        Tool(
            name="get_policy_info",
            description="Retrieve detailed information about an insurance policy",
            inputSchema={
                "type": "object",
                "properties": {
                    "policy_id": {
                        "type": "string",
                        "description": "The unique identifier of the insurance policy",
                    }
                },
                "required": ["policy_id"],
            },
        ),
        Tool(
            name="get_customer_policies",
            description="Retrieve all insurance policies for a specific customer",
            inputSchema={
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "The name of the customer",
                    }
                },
                "required": ["customer_name"],
            },
        ),
    ]

    # Define resources
    resources: list[ResourceTemplate] = [
        ResourceTemplate(
            uriTemplate="system://status",
            name="System Status",
            description="Get the current health and status of the MCP server",
            mimeType="application/json",
        )
    ]

    @_server.list_tools()
    async def list_tools_handler() -> list[Tool]:
        """List available tools."""
        logger.debug("Listing available tools")
        return tools

    @_server.call_tool()
    async def call_tool_handler(
        name: str, arguments: dict[str, Any]
    ) -> list[TextContent]:
        """Handle tool calls."""
        return await _process_tool_call(name, arguments)

    @_server.list_resources()
    async def list_resources_handler() -> list[Resource]:
        """List available resources."""
        logger.debug("Listing available resources")
        return [
            Resource(
                uri="system://status",
                name="System Status",
                mimeType="application/json",
                description="Get the current health and status of the MCP server",
            )
        ]

    @_server.read_resource()
    async def read_resource_handler(uri: str) -> list[TextContent]:
        """Handle resource read requests."""
        return await _handle_resource_read(uri)

    # Run the server with stdio transport
    async with mcp.server.stdio.stdio_server(_server) as (read_stream, write_stream):
        logger.info("MCP server running on stdio transport")
        await _server.run(read_stream, write_stream)


def run_server() -> None:
    """Entry point for running the MCP server."""
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    run_server()

"""HTTP/SSE server implementation with MCP protocol support."""

import asyncio
import uuid
from typing import AsyncGenerator, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.infrastructure.config import get_settings
from src.infrastructure.logger import setup_logger
from src.delivery.http_adapter import (
    HTTPSSEAdapter,
    MCPMessage,
    MessageType,
    SSEClientConnection,
)
from src.delivery.mcp_server import (
    _initialize_use_cases,
    _handle_get_policy_info,
    _handle_get_customer_policies,
    _handle_get_system_status,
)

logger = setup_logger(__name__)

# Global state
_app: FastAPI | None = None
_start_time: datetime = datetime.utcnow()
_connections: dict[str, SSEClientConnection] = {}


def create_http_server() -> FastAPI:
    """
    Create and configure the FastAPI HTTP server.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="MCP HTTP/SSE Bridge",
        description="HTTP and Server-Sent Events bridge for MCP protocol",
        version="1.0.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event() -> None:
        """Initialize on startup."""
        logger.info("Starting MCP HTTP/SSE Server")
        settings = get_settings()
        _initialize_use_cases()
        logger.info(f"Server: {settings.server_name} v{settings.server_version}")

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        """
        Health check endpoint.

        Returns:
            Health status
        """
        uptime = (datetime.utcnow() - _start_time).total_seconds()
        settings = get_settings()
        return {
            "status": "healthy",
            "version": settings.server_version,
            "uptime_seconds": int(uptime),
            "timestamp": datetime.utcnow().isoformat(),
            "active_connections": len(_connections),
        }

    @app.get("/api/v1/status")
    async def get_status() -> dict[str, Any]:
        """
        Get system status.

        Returns:
            System status information
        """
        try:
            result = await _handle_get_system_status()
            import json

            status_data = json.loads(result[0].text)
            return status_data
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/tools")
    async def list_tools() -> dict[str, Any]:
        """
        List available tools.

        Returns:
            List of available tools
        """
        return {
            "tools": [
                {
                    "name": "get_policy_info",
                    "description": "Retrieve detailed information about an insurance policy",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "policy_id": {
                                "type": "string",
                                "description": "The unique identifier of the insurance policy",
                            }
                        },
                        "required": ["policy_id"],
                    },
                },
                {
                    "name": "get_customer_policies",
                    "description": "Retrieve all insurance policies for a specific customer",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "customer_name": {
                                "type": "string",
                                "description": "The name of the customer",
                            }
                        },
                        "required": ["customer_name"],
                    },
                },
            ]
        }

    @app.post("/api/v1/tools/call")
    async def call_tool(request: Request) -> dict[str, Any]:
        """
        Call a tool directly (HTTP POST).

        Args:
            request: HTTP request containing tool call

        Returns:
            Tool call result
        """
        try:
            body = await request.json()
            tool_name = body.get("tool")
            arguments = body.get("arguments", {})

            logger.info(f"Tool call: {tool_name} with args: {arguments}")

            if tool_name == "get_policy_info":
                result = await _handle_get_policy_info(
                    policy_id=arguments.get("policy_id")
                )
            elif tool_name == "get_customer_policies":
                result = await _handle_get_customer_policies(
                    customer_name=arguments.get("customer_name")
                )
            else:
                raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

            import json

            response_data = json.loads(result[0].text)
            return response_data
        except Exception as e:
            logger.error(f"Error calling tool: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/sse/connect")
    async def sse_connect(request: Request) -> StreamingResponse:
        """
        Establish SSE connection.

        Args:
            request: HTTP request

        Returns:
            Streaming response with SSE events
        """
        connection_id = str(uuid.uuid4())
        connection = SSEClientConnection(connection_id)
        _connections[connection_id] = connection

        logger.info(f"New SSE connection established: {connection_id}")

        async def event_generator() -> AsyncGenerator[str, None]:
            """Generate SSE events."""
            try:
                # Send initial connection message
                welcome_msg = MCPMessage(
                    type=MessageType.STATUS,
                    data={
                        "status": "connected",
                        "connection_id": connection_id,
                        "message": "SSE connection established",
                    },
                    request_id=connection_id,
                )
                yield connection.adapter.format_sse_message(welcome_msg)

                # Keep connection alive with heartbeats
                heartbeat_count = 0
                while True:
                    heartbeat_count += 1

                    # Send heartbeat every 30 seconds
                    heartbeat_msg = HTTPSSEAdapter.create_heartbeat()
                    yield connection.adapter.format_sse_message(heartbeat_msg)
                    connection.last_heartbeat = datetime.utcnow()

                    # Check if client is still connected
                    try:
                        await asyncio.sleep(30)
                    except asyncio.CancelledError:
                        logger.info(f"Connection {connection_id} closed by client")
                        break

            except Exception as e:
                logger.error(f"Error in event generator: {str(e)}")
                error_msg = HTTPSSEAdapter.create_error_response(
                    error=str(e), code="CONNECTION_ERROR"
                )
                yield connection.adapter.format_sse_message(error_msg)
            finally:
                if connection_id in _connections:
                    del _connections[connection_id]
                logger.info(f"Connection {connection_id} closed")

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Connection-ID": connection_id,
            },
        )

    @app.post("/api/v1/sse/message")
    async def send_sse_message(request: Request) -> dict[str, Any]:
        """
        Send a message to an SSE connection.

        Args:
            request: HTTP request

        Returns:
            Message processing result
        """
        try:
            body = await request.json()
            connection_id = body.get("connection_id")
            message_data = body.get("message")

            if connection_id not in _connections:
                raise HTTPException(
                    status_code=404, detail=f"Connection not found: {connection_id}"
                )

            connection = _connections[connection_id]
            message = HTTPSSEAdapter.parse_http_request(message_data)

            # Process the message asynchronously
            asyncio.create_task(connection.adapter.process_message(message))

            return {"status": "accepted", "request_id": message.request_id}
        except Exception as e:
            logger.error(f"Error sending SSE message: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/v1/connections")
    async def list_connections() -> dict[str, Any]:
        """
        List all active connections.

        Returns:
            List of active connections info
        """
        connections_info = [conn.get_connection_info() for conn in _connections.values()]
        return {
            "total": len(connections_info),
            "connections": connections_info,
        }

    @app.get("/api/v1/connections/{connection_id}")
    async def get_connection_info(connection_id: str) -> dict[str, Any]:
        """
        Get information about a specific connection.

        Args:
            connection_id: Connection ID

        Returns:
            Connection information
        """
        if connection_id not in _connections:
            raise HTTPException(status_code=404, detail="Connection not found")

        connection = _connections[connection_id]
        return connection.get_connection_info()

    return app


async def run_http_server(
    host: str = "0.0.0.0", port: int = 8000
) -> None:
    """
    Run the HTTP server.

    Args:
        host: Host address
        port: Port number
    """
    global _app
    _app = create_http_server()

    config = uvicorn.Config(
        _app,
        host=host,
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


def run_http_server_sync(host: str = "0.0.0.0", port: int = 8000) -> None:
    """
    Run the HTTP server synchronously.

    Args:
        host: Host address
        port: Port number
    """
    asyncio.run(run_http_server(host, port))


if __name__ == "__main__":
    run_http_server_sync()


"""HTTP/SSE adapter for MCP protocol compatibility."""

import asyncio
import json
import logging
from typing import Any, Callable, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from src.infrastructure.logger import setup_logger

logger = setup_logger(__name__)


class MessageType(str, Enum):
    """SSE message types."""

    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    RESOURCE_READ = "resource_read"
    RESOURCE_RESULT = "resource_result"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    STATUS = "status"


@dataclass
class MCPMessage:
    """Represents an MCP protocol message."""

    type: MessageType
    data: dict[str, Any]
    timestamp: datetime | None = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        """Set default timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "request_id": self.request_id,
        }

    def to_json(self) -> str:
        """Convert message to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MCPMessage":
        """Create MCPMessage from dictionary."""
        return cls(
            type=MessageType(data["type"]),
            data=data.get("data", {}),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if data.get("timestamp")
                else None
            ),
            request_id=data.get("request_id"),
        )


class HTTPSSEAdapter:
    """
    Adapter to convert between HTTP/SSE and MCP protocol messages.

    This allows HTTP clients to communicate with MCP servers using SSE
    for real-time streaming communication.
    """

    def __init__(self) -> None:
        """Initialize the adapter."""
        self.logger = setup_logger(__name__)
        self._message_queue: asyncio.Queue[MCPMessage] = asyncio.Queue()
        self._handlers: dict[MessageType, Callable[..., Any]] = {}
        self._request_handlers: dict[str, asyncio.Event] = {}
        self._responses: dict[str, Any] = {}

    def register_handler(
        self, message_type: MessageType, handler: Callable[..., Any]
    ) -> None:
        """
        Register a handler for a specific message type.

        Args:
            message_type: The type of message to handle
            handler: Async callable that processes the message
        """
        self._handlers[message_type] = handler
        self.logger.debug(f"Registered handler for {message_type.value}")

    async def process_message(self, message: MCPMessage) -> None:
        """
        Process an incoming message.

        Args:
            message: The message to process
        """
        self.logger.info(
            f"Processing message type: {message.type.value}, "
            f"request_id: {message.request_id}"
        )

        handler = self._handlers.get(message.type)
        if not handler:
            error_msg = MCPMessage(
                type=MessageType.ERROR,
                data={
                    "error": f"No handler for message type: {message.type.value}",
                    "code": "HANDLER_NOT_FOUND",
                },
                request_id=message.request_id,
            )
            await self._message_queue.put(error_msg)
            return

        try:
            result = await handler(message)
            response = MCPMessage(
                type=MessageType.TOOL_RESULT
                if message.type == MessageType.TOOL_CALL
                else MessageType.RESOURCE_RESULT,
                data=result,
                request_id=message.request_id,
            )
            await self._message_queue.put(response)
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}", exc_info=True)
            error_msg = MCPMessage(
                type=MessageType.ERROR,
                data={
                    "error": str(e),
                    "code": "PROCESSING_ERROR",
                    "message_type": message.type.value,
                },
                request_id=message.request_id,
            )
            await self._message_queue.put(error_msg)

    async def get_next_message(self, timeout: float = 30.0) -> Optional[MCPMessage]:
        """
        Get the next message from the queue.

        Args:
            timeout: Timeout in seconds

        Returns:
            The next message or None if timeout
        """
        try:
            message = await asyncio.wait_for(self._message_queue.get(), timeout=timeout)
            self.logger.debug(f"Retrieved message: {message.type.value}")
            return message
        except asyncio.TimeoutError:
            return None

    def format_sse_message(self, message: MCPMessage) -> str:
        """
        Format a message as Server-Sent Event format.

        Args:
            message: The message to format

        Returns:
            SSE formatted string
        """
        sse_lines = [f"event: {message.type.value}"]

        if message.request_id:
            sse_lines.append(f"id: {message.request_id}")

        # Split JSON by lines for proper SSE formatting
        json_data = message.to_json()
        sse_lines.append(f"data: {json_data}")
        sse_lines.append("")  # Empty line to mark end of message

        return "\n".join(sse_lines)

    @staticmethod
    def parse_http_request(
        body: dict[str, Any],
    ) -> MCPMessage:
        """
        Parse an HTTP request body into an MCPMessage.

        Args:
            body: The HTTP request body

        Returns:
            Parsed MCPMessage
        """
        message_type = MessageType(body.get("type", "tool_call"))
        data = body.get("data", {})
        request_id = body.get("request_id")

        return MCPMessage(
            type=message_type,
            data=data,
            request_id=request_id,
        )

    @staticmethod
    def create_error_response(
        error: str,
        code: str = "INTERNAL_ERROR",
        request_id: Optional[str] = None,
    ) -> MCPMessage:
        """
        Create an error response message.

        Args:
            error: Error message
            code: Error code
            request_id: Optional request ID

        Returns:
            Error MCPMessage
        """
        return MCPMessage(
            type=MessageType.ERROR,
            data={"error": error, "code": code},
            request_id=request_id,
        )

    @staticmethod
    def create_heartbeat() -> MCPMessage:
        """
        Create a heartbeat message.

        Returns:
            Heartbeat MCPMessage
        """
        return MCPMessage(
            type=MessageType.HEARTBEAT,
            data={"message": "ping"},
        )


class SSEClientConnection:
    """Manages an individual SSE client connection."""

    def __init__(self, connection_id: str) -> None:
        """
        Initialize the connection.

        Args:
            connection_id: Unique identifier for this connection
        """
        self.connection_id = connection_id
        self.created_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.message_count = 0
        self.adapter = HTTPSSEAdapter()
        self.logger = setup_logger(__name__)

    async def send_message(self, message: MCPMessage) -> str:
        """
        Send a message through SSE.

        Args:
            message: The message to send

        Returns:
            SSE formatted string
        """
        self.message_count += 1
        self.logger.debug(
            f"Connection {self.connection_id}: Sending message #{self.message_count}"
        )
        return self.adapter.format_sse_message(message)

    def get_connection_info(self) -> dict[str, Any]:
        """
        Get information about this connection.

        Returns:
            Dictionary with connection info
        """
        uptime = (datetime.utcnow() - self.created_at).total_seconds()
        return {
            "connection_id": self.connection_id,
            "created_at": self.created_at.isoformat(),
            "uptime_seconds": int(uptime),
            "message_count": self.message_count,
            "last_heartbeat": self.last_heartbeat.isoformat(),
        }


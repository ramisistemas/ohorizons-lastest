"""Tests for HTTP/SSE adapter."""

import pytest
import asyncio
import json
from datetime import datetime

from src.delivery.http_adapter import (
    MCPMessage,
    MessageType,
    HTTPSSEAdapter,
    SSEClientConnection,
)


class TestMCPMessage:
    """Tests for MCPMessage class."""

    def test_create_message(self) -> None:
        """Test creating an MCPMessage."""
        msg = MCPMessage(
            type=MessageType.TOOL_CALL,
            data={"tool": "test", "args": {}},
            request_id="req-123",
        )

        assert msg.type == MessageType.TOOL_CALL
        assert msg.data == {"tool": "test", "args": {}}
        assert msg.request_id == "req-123"
        assert msg.timestamp is not None

    def test_message_to_dict(self) -> None:
        """Test converting message to dict."""
        msg = MCPMessage(
            type=MessageType.TOOL_CALL,
            data={"tool": "test"},
            request_id="req-123",
        )

        msg_dict = msg.to_dict()
        assert msg_dict["type"] == "tool_call"
        assert msg_dict["data"] == {"tool": "test"}
        assert msg_dict["request_id"] == "req-123"
        assert "timestamp" in msg_dict

    def test_message_to_json(self) -> None:
        """Test converting message to JSON."""
        msg = MCPMessage(
            type=MessageType.ERROR,
            data={"error": "Test error"},
            request_id="req-456",
        )

        json_str = msg.to_json()
        parsed = json.loads(json_str)

        assert parsed["type"] == "error"
        assert parsed["data"]["error"] == "Test error"
        assert parsed["request_id"] == "req-456"

    def test_message_from_dict(self) -> None:
        """Test creating message from dict."""
        data = {
            "type": "tool_result",
            "data": {"result": "success"},
            "request_id": "req-789",
            "timestamp": "2024-04-06T10:30:45.123456",
        }

        msg = MCPMessage.from_dict(data)

        assert msg.type == MessageType.TOOL_RESULT
        assert msg.data == {"result": "success"}
        assert msg.request_id == "req-789"

    def test_message_all_types(self) -> None:
        """Test all message types."""
        for msg_type in MessageType:
            msg = MCPMessage(type=msg_type, data={})
            assert msg.type == msg_type
            msg_dict = msg.to_dict()
            assert msg_dict["type"] == msg_type.value


class TestHTTPSSEAdapter:
    """Tests for HTTPSSEAdapter class."""

    @pytest.mark.asyncio
    async def test_adapter_initialization(self) -> None:
        """Test adapter initialization."""
        adapter = HTTPSSEAdapter()
        assert adapter is not None
        assert len(adapter._handlers) == 0

    def test_register_handler(self) -> None:
        """Test registering a handler."""
        adapter = HTTPSSEAdapter()

        async def handler(msg: MCPMessage) -> dict:
            return {"status": "handled"}

        adapter.register_handler(MessageType.TOOL_CALL, handler)
        assert MessageType.TOOL_CALL in adapter._handlers

    def test_format_sse_message(self) -> None:
        """Test formatting SSE message."""
        adapter = HTTPSSEAdapter()
        msg = MCPMessage(
            type=MessageType.HEARTBEAT,
            data={"message": "ping"},
            request_id="req-123",
        )

        sse_str = adapter.format_sse_message(msg)

        assert "event: heartbeat" in sse_str
        assert "id: req-123" in sse_str
        assert "data:" in sse_str

    def test_parse_http_request(self) -> None:
        """Test parsing HTTP request."""
        body = {
            "type": "tool_call",
            "data": {"tool": "test_tool", "args": {"arg1": "value1"}},
            "request_id": "req-123",
        }

        msg = HTTPSSEAdapter.parse_http_request(body)

        assert msg.type == MessageType.TOOL_CALL
        assert msg.data["tool"] == "test_tool"
        assert msg.request_id == "req-123"

    def test_create_error_response(self) -> None:
        """Test creating error response."""
        msg = HTTPSSEAdapter.create_error_response(
            error="Test error",
            code="TEST_ERROR",
            request_id="req-123",
        )

        assert msg.type == MessageType.ERROR
        assert msg.data["error"] == "Test error"
        assert msg.data["code"] == "TEST_ERROR"
        assert msg.request_id == "req-123"

    def test_create_heartbeat(self) -> None:
        """Test creating heartbeat message."""
        msg = HTTPSSEAdapter.create_heartbeat()

        assert msg.type == MessageType.HEARTBEAT
        assert "message" in msg.data

    @pytest.mark.asyncio
    async def test_get_next_message_timeout(self) -> None:
        """Test getting message with timeout."""
        adapter = HTTPSSEAdapter()

        # Should timeout and return None
        msg = await adapter.get_next_message(timeout=0.1)
        assert msg is None

    @pytest.mark.asyncio
    async def test_message_queue(self) -> None:
        """Test message queue operations."""
        adapter = HTTPSSEAdapter()

        # Add a message
        msg = MCPMessage(type=MessageType.HEARTBEAT, data={})
        await adapter._message_queue.put(msg)

        # Retrieve it
        retrieved = await adapter.get_next_message(timeout=1.0)
        assert retrieved is not None
        assert retrieved.type == MessageType.HEARTBEAT


class TestSSEClientConnection:
    """Tests for SSEClientConnection class."""

    def test_connection_creation(self) -> None:
        """Test creating a connection."""
        conn = SSEClientConnection("conn-123")

        assert conn.connection_id == "conn-123"
        assert conn.message_count == 0
        assert conn.created_at is not None

    @pytest.mark.asyncio
    async def test_send_message(self) -> None:
        """Test sending a message."""
        conn = SSEClientConnection("conn-123")
        msg = MCPMessage(type=MessageType.TOOL_CALL, data={})

        sse_str = await conn.send_message(msg)

        assert "event:" in sse_str
        assert conn.message_count == 1

    def test_get_connection_info(self) -> None:
        """Test getting connection info."""
        conn = SSEClientConnection("conn-456")

        info = conn.get_connection_info()

        assert info["connection_id"] == "conn-456"
        assert "created_at" in info
        assert "uptime_seconds" in info
        assert info["message_count"] == 0

    def test_multiple_messages(self) -> None:
        """Test sending multiple messages."""
        conn = SSEClientConnection("conn-789")

        # Simulate sending multiple messages
        conn.message_count = 5

        info = conn.get_connection_info()
        assert info["message_count"] == 5


class TestIntegration:
    """Integration tests."""

    @pytest.mark.asyncio
    async def test_message_processing_flow(self) -> None:
        """Test complete message processing flow."""
        adapter = HTTPSSEAdapter()
        results = []

        async def tool_handler(msg: MCPMessage) -> dict:
            return {"processed": True, "tool": msg.data.get("tool")}

        adapter.register_handler(MessageType.TOOL_CALL, tool_handler)

        # Create and process a message
        msg = MCPMessage(
            type=MessageType.TOOL_CALL,
            data={"tool": "test_tool"},
            request_id="req-123",
        )

        # Process message (runs async)
        await adapter.process_message(msg)

        # Get response (with timeout)
        response = await adapter.get_next_message(timeout=1.0)
        assert response is not None
        assert response.type == MessageType.TOOL_RESULT
        assert response.request_id == "req-123"


# Pytest fixtures
@pytest.fixture
def adapter() -> HTTPSSEAdapter:
    """Provide an adapter instance."""
    return HTTPSSEAdapter()


@pytest.fixture
def connection() -> SSEClientConnection:
    """Provide a connection instance."""
    return SSEClientConnection("test-conn")


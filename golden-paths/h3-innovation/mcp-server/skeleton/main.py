"""Main entry point for MCP Enterprise Template."""

import sys
import logging
import argparse

from src.delivery.mcp_server import run_server
from src.delivery.http_server import run_http_server_sync
from src.infrastructure.logger import setup_logger
from src.infrastructure.config import get_settings

# Setup logging
logger = setup_logger(__name__)


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code
    """
    parser = argparse.ArgumentParser(
        description="MCP Enterprise Template Server"
    )
    parser.add_argument(
        "--mode",
        choices=["mcp", "http", "both"],
        default="mcp",
        help="Server mode: 'mcp' for MCP/stdio, 'http' for HTTP/SSE, 'both' for both",
    )
    parser.add_argument(
        "--http-host",
        default="0.0.0.0",
        help="HTTP server host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--http-port",
        type=int,
        default=8000,
        help="HTTP server port (default: 8000)",
    )

    args = parser.parse_args()

    try:
        settings = get_settings()
        logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
        logger.info("=" * 80)
        logger.info("MCP Enterprise Template Server")
        logger.info(f"Version: {settings.server_version}")
        logger.info(f"Debug Mode: {settings.debug}")
        logger.info(f"Mode: {args.mode}")
        logger.info("=" * 80)

        if args.mode == "mcp":
            run_server()
        elif args.mode == "http":
            run_http_server_sync(host=args.http_host, port=args.http_port)
        elif args.mode == "both":
            # Run MCP in the background and HTTP in foreground
            import threading

            mcp_thread = threading.Thread(target=run_server, daemon=True)
            mcp_thread.start()
            logger.info("MCP server started in background thread")

            run_http_server_sync(host=args.http_host, port=args.http_port)

        return 0
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

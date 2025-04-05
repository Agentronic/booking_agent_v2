#!/usr/bin/env python3
"""
MCP server for the slot calendar functionality.
This server exposes the booking system capabilities through the Model Context Protocol.
"""

import anyio
import click
import mcp.types as types
from mcp.server.lowlevel import Server
from datetime import datetime, time, date as date_obj
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to allow importing slot_calendar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
log_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'mcp_server.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also log to console for development
    ]
)
logger = logging.getLogger('mcp_server')

# Import the existing slot calendar functionality
from slot_calendar import (
    is_slot_available,
    book_slot,
    cancel_booking,
    slots_available_on_day,
    setup_database
)

@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
def main(port: int, transport: str) -> int:
    # Initialize the database
    setup_database()
    
    app = Server("slot-calendar")

    @app.call_tool()
    async def calendar_tool(name: str, arguments: dict) -> any:
        """Handle calendar tool calls."""
        if name == "is_slot_available":
            return is_slot_available(
                arguments["date"],
                arguments["time"],
                arguments["duration"]
            )
        
        elif name == "book_slot":
            logger.debug(f"book_slot called with args: {arguments}")
            try:
                result = book_slot(
                    arguments["date"],
                    arguments["start_time"],
                    arguments["duration"],
                    arguments["client_id"],
                    arguments["service_name"]
                )
                logger.debug(f"book_slot returned: {result} (type: {type(result)})")
                # Convert the booking result into a list of TextContent
                return [types.TextContent(
                    type="text",
                    text=f"Booking successful. Your booking ID is: {result}"
                )]
            except Exception as e:
                logger.error(f"book_slot raised exception: {str(e)}", exc_info=True)
                raise
        
        elif name == "cancel_booking":
            logger.debug(f"cancel_booking called with args: {arguments}")
            try:
                result = cancel_booking(
                    arguments["booking_id"]
                )
                logger.debug(f"cancel_booking returned: {result} (type: {type(result)})")
                return [types.TextContent(
                    type="text",
                    text=f"Booking {arguments['booking_id']} has been cancelled successfully."
                )]
            except Exception as e:
                logger.error(f"cancel_booking raised exception: {str(e)}", exc_info=True)
                raise
        
        elif name == "slots_available_on_day":
            logger.debug(f"slots_available_on_day called with args: {arguments}")
            try:
                result = slots_available_on_day(
                    arguments["date"],
                    arguments["duration"]
                )
                logger.debug(f"slots_available_on_day returned: {result} (type: {type(result)})")
                # Convert the slots result into a list of TextContent
                if result:
                    return [types.TextContent(
                        type="text",
                        text=f"Available slots on {arguments['date']}: {', '.join(result)}"
                    )]
                else:
                    return [types.TextContent(
                        type="text",
                        text=f"No available slots found on {arguments['date']} for duration {arguments['duration']} minutes."
                    )]
            except Exception as e:
                logger.error(f"slots_available_on_day raised exception: {str(e)}", exc_info=True)
                raise
        
        else:
            raise ValueError(f"Unknown tool: {name}")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="is_slot_available",
                description="Check if a slot is available",
                inputSchema={
                    "type": "object",
                    "required": ["date", "time", "duration"],
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format"
                        },
                        "time": {
                            "type": "string",
                            "description": "Time in HH:MM format"
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Duration in minutes"
                        }
                    }
                }
            ),
            types.Tool(
                name="book_slot",
                description="Book a slot",
                inputSchema={
                    "type": "object",
                    "required": ["date", "start_time", "duration", "client_id", "service_name"],
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format"
                        },
                        "start_time": {
                            "type": "string",
                            "description": "Start time in HH:MM format"
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Duration in minutes"
                        },
                        "client_id": {
                            "type": "string",
                            "description": "Client identifier"
                        },
                        "service_name": {
                            "type": "string",
                            "description": "Name of the service"
                        }
                    }
                }
            ),
            types.Tool(
                name="cancel_booking",
                description="Cancel a booking",
                inputSchema={
                    "type": "object",
                    "required": ["booking_id"],
                    "properties": {
                        "booking_id": {
                            "type": "integer",
                            "description": "Booking ID to cancel"
                        }
                    }
                }
            ),
            types.Tool(
                name="slots_available_on_day",
                description="Get available slots for a day",
                inputSchema={
                    "type": "object",
                    "required": ["date", "duration"],
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format"
                        },
                        "duration": {
                            "type": "integer",
                            "description": "Duration in minutes"
                        }
                    }
                }
            )
        ]

    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn
        uvicorn.run(starlette_app, host="0.0.0.0", port=port)
    else:
        from mcp.server.stdio import stdio_server

        async def arun():
            async with stdio_server() as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )

        anyio.run(arun)

    return 0

if __name__ == "__main__":
    main() 
"""
MCP (Model Context Protocol) client implementation for the booking agent system.
This implementation follows the official AG2 MCP integration guidelines.
"""

import asyncio
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import logging
import os
import sys
from dotenv import load_dotenv
import nest_asyncio
from contextlib import AsyncExitStack
from anyio import create_task_group

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPClient:
    """MCP client implementation for the booking agent system."""
    
    def __init__(self):
        """Initialize the MCP client."""
        self.session = None
        self.initialized = False
        self._lock = asyncio.Lock()
        self._stack = None
        
    async def initialize(self):
        """Initialize the MCP client session and create the toolkit."""
        async with self._lock:
            if self.initialized:
                return
            
            try:
                # Set up server parameters for local MCP server
                server_params = StdioServerParameters(
                    command="python",
                    args=["app/calendar/mcp/server.py"]  # Path to your MCP server script
                )

                # Create a new exit stack for this initialization
                self._stack = AsyncExitStack()
                await self._stack.__aenter__()
                
                # Create and initialize the session
                session, _ = await self.create_session(server_params)
                await session.initialize()
                self.session = session
                self.initialized = True
                logger.info("MCP client initialized successfully")
                    
            except Exception as e:
                logger.error(f"Error initializing MCP client: {str(e)}")
                if self._stack:
                    await self._stack.__aexit__(*sys.exc_info())
                    self._stack = None
                self.initialized = False
                raise
    
    async def create_session(self, server_params):
        """Create a new MCP session with the given server parameters."""
        try:
            read, write = await self._stack.enter_async_context(stdio_client(server_params))
            session = await self._stack.enter_async_context(ClientSession(read, write))
            return session, self._stack
        except Exception:
            await self._stack.__aexit__(*sys.exc_info())
            raise
    
    async def execute_tool(self, tool_name: str, **kwargs):
        """
        Execute a tool by name with the provided arguments.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Result of the tool execution
        """
        if not self.initialized:
            await self.initialize()
        
        try:
            # Create a message that describes the tool execution
            message = f"Execute tool {tool_name} with arguments: {kwargs}"
            
            # Execute the tool directly
            result = await self.session.execute_tool(tool_name, **kwargs)
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def close(self):
        """Close the MCP client session."""
        async with self._lock:
            if self.session:
                await self.session.close()
                self.session = None
                if self._stack:
                    await self._stack.__aexit__(None, None, None)
                    self._stack = None
                self.initialized = False
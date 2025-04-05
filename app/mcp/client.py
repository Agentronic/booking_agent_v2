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
from dotenv import load_dotenv
import nest_asyncio

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
                
                # Start the client session
                async with stdio_client(server_params) as (read, write), ClientSession(read, write) as session:
                    self.session = session
                    
                    # Initialize the session
                    await session.initialize()
                    self.initialized = True
                    logger.info("MCP client initialized successfully")
                    
            except Exception as e:
                logger.error(f"Error initializing MCP client: {str(e)}")
                self.initialized = False
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
                self.toolkit = None
                self.initialized = False

# Create a global instance of the MCP client
mcp_client = MCPClient()

# Initialize the client when the module is imported
async def init_client():
    try:
        await mcp_client.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize MCP client: {str(e)}")

# Run the initialization in an event loop
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If the loop is already running, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(init_client())
except Exception as e:
    logger.error(f"Failed to initialize MCP client: {str(e)}") 
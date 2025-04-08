#!/usr/bin/env python3
"""
Debug script for MCP client agent.
"""

import asyncio
import logging
from app.mcp.agent_mcp_client import MCPClient
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_agent():
    try:
        # Create a new instance instead of using the global one
        client = MCPClient()
        
        # Step 1: Initialize the client
        logger.debug("Step 1: Initializing client...")
        await client.initialize()
        
        # Step 2: Verify initialization
        logger.debug("Step 2: Verifying initialization...")
        if not client.initialized:
            raise Exception("Client failed to initialize")
            
        # Step 3: Check if agent and toolkit are set up
        logger.debug("Step 3: Checking agent and toolkit...")
        if not client.agent or not client.toolkit:
            raise Exception("Agent or toolkit not properly initialized")
            
        # Step 4: List available tools
        logger.debug("Step 4: Listing available tools...")
        tools = await client.session.list_tools()
        logger.debug(f"Available tools: {tools}")
        
        # Step 5: Check tomorrow's availability
        logger.debug("Step 5: Checking tomorrow's availability...")
        tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
        result = await client.execute_tool("slots_available_on_day", date=tomorrow)
        logger.debug(f"Tomorrow's availability: {result}")
        
        # Step 6: Clean up
        logger.debug("Step 6: Cleaning up...")
        await client.close()
        
    except Exception as e:
        logger.error(f"Debug error: {str(e)}")
        if 'client' in locals():
            await client.close()
        raise

if __name__ == "__main__":
    asyncio.run(debug_agent()) 
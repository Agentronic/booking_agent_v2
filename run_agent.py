#!/usr/bin/env python3
"""
Script to run the MCP client agent.
"""

import asyncio
from app.mcp.agent_mcp_client import mcp_client

async def main():
    try:
        # The client is already initialized when imported
        # We can just wait for it to complete its tasks
        print("Agent is running and will list tools and check tomorrow's availability...")
        
        # Keep the script running to see the agent's output
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        await mcp_client.close()
    except Exception as e:
        print(f"Error: {str(e)}")
        await mcp_client.close()

if __name__ == "__main__":
    asyncio.run(main()) 
import json
import subprocess
import sys
import time
import asyncio
from typing import Dict, Any
from mcp.server.stdio import stdio_server

async def test_list_tools():
    print("Starting server process...")
    process = subprocess.Popen(
        [sys.executable, "app/calendar/mcp/server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Give the server a moment to start
        await asyncio.sleep(1)
        
        print("Connecting to server...")
        # Create a JSON-RPC message for tools/list
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        # Send the message
        message_str = json.dumps(message) + "\n"
        print(f"Sending message: {message_str.strip()}")
        process.stdin.write(message_str)
        process.stdin.flush()
        
        # Read the response
        print("Reading response...")
        response = process.stdout.readline()
        print(f"Received response: {response.strip()}")
        
        if not response:
            stderr = process.stderr.read()
            if stderr:
                print(f"Server stderr: {stderr}")
            raise Exception("No response received from server")
        
        # Parse the response
        response_data = json.loads(response)
        assert response_data["jsonrpc"] == "2.0"
        assert response_data["id"] == 1
        assert "result" in response_data
        
        tools = response_data["result"]
        print(f"Received tools: {json.dumps(tools, indent=2)}")
        
        # Verify we have the expected tools
        tool_names = {tool["name"] for tool in tools}
        expected_tools = {
            "is_slot_available",
            "book_slot",
            "cancel_booking",
            "slots_available_on_day"
        }
        
        assert tool_names == expected_tools, f"Expected tools {expected_tools}, got {tool_names}"
        
        # Verify each tool has the required fields
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"
            assert "properties" in tool["inputSchema"]
            
        print("Test passed successfully!")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")
        stderr = process.stderr.read()
        if stderr:
            print(f"Server stderr: {stderr}")
        raise
    finally:
        print("Terminating server process...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

if __name__ == "__main__":
    asyncio.run(test_list_tools()) 
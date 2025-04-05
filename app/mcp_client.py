"""
MCP (Model Context Protocol) client implementation for the Booking Agent.
This client handles communication with the google-calendar-mcp server using the stdio protocol.
"""

import json
import subprocess
from typing import Dict, Any, Optional, List
import os
import sys
from dataclasses import dataclass
import threading
from queue import Queue
import time
import inspect

@dataclass
class MCPRequest:
    method: str
    params: Dict[str, Any]
    request_id: int

@dataclass
class MCPResponse:
    result: Any
    error: Optional[Dict[str, Any]]
    request_id: int

class MCPClient:
    def __init__(self):
        """Initialize the MCP client and start the server process."""
        caller = inspect.currentframe().f_back
        print(f"DEBUG: [MCPClient.__init__:line_{caller.f_lineno}] Initializing MCP client", file=sys.stderr)
        
        # Get the absolute path to the google-calendar-mcp directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.mcp_dir = os.path.join(current_dir, "google-calendar-mcp")
        
        # First ensure dependencies are installed and project is built
        print(f"DEBUG: [MCPClient.__init__:line_{caller.f_lineno}] Installing dependencies in {self.mcp_dir}", file=sys.stderr)
        subprocess.run(["npm", "install"], cwd=self.mcp_dir, check=True)
        
        print(f"DEBUG: [MCPClient.__init__:line_{caller.f_lineno}] Building the project", file=sys.stderr)
        subprocess.run(["npm", "run", "build"], cwd=self.mcp_dir, check=True)
        
        # Set up instance variables
        self.server_cmd = ["node", "--inspect-brk=9229", "dist/index.js"]
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0
        self.request_queue: Queue = Queue()
        self.response_queue: Queue = Queue()
        self.response_events: Dict[int, threading.Event] = {}
        self.response_data: Dict[int, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
        # Start the server process
        self._start_server()
        
        # Register available methods
        self._register_methods()
        
        # Start reader thread
        self._reader_thread = threading.Thread(target=self._read_responses, daemon=True)
        self._reader_thread.start()
        print(f"DEBUG: [MCPClient.__init__:line_{caller.f_lineno}] Started MCP response reader thread", file=sys.stderr)
        
        # Start writer thread
        self._writer_thread = threading.Thread(target=self._write_requests, daemon=True)
        self._writer_thread.start()
        print(f"DEBUG: [MCPClient.__init__:line_{caller.f_lineno}] Started MCP request writer thread", file=sys.stderr)

    def _start_server(self):
        """Start the MCP server process."""
        caller = inspect.currentframe().f_back
        print(f"DEBUG: [MCPClient._start_server:line_{caller.f_lineno}] Starting MCP server with command: {' '.join(self.server_cmd)}", file=sys.stderr)
        print(f"DEBUG: [MCPClient._start_server:line_{caller.f_lineno}] Working directory: {self.mcp_dir}", file=sys.stderr)
        print(f"DEBUG: [MCPClient._start_server:line_{caller.f_lineno}] Waiting for debugger to attach on port 9229...", file=sys.stderr)
        
        self.process = subprocess.Popen(
            self.server_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=self.mcp_dir
        )
        
        # Wait for the debugger to attach
        time.sleep(2)  # Give some time for the debugger to attach

    def _register_methods(self):
        """Register available methods with the MCP server."""
        caller = inspect.currentframe().f_back
        print(f"DEBUG: [MCPClient._register_methods:line_{caller.f_lineno}] Registering methods with MCP server", file=sys.stderr)
        
        methods = [
            "get_available_slots",
            "book_appointment",
            "list_events",
            "cancel_appointment"
        ]
        
        for method in methods:
            try:
                self.call_tool("register_method", {"method": method})
                print(f"DEBUG: [MCPClient._register_methods:line_{caller.f_lineno}] Registered method: {method}", file=sys.stderr)
            except Exception as e:
                print(f"ERROR: [MCPClient._register_methods:line_{caller.f_lineno}] Failed to register method {method}: {str(e)}", file=sys.stderr)

    def _read_responses(self):
        """Read responses from the MCP server in a separate thread."""
        caller = inspect.currentframe().f_back
        print(f"DEBUG: [MCPClient._read_responses:line_{caller.f_lineno}] Starting response reader loop", file=sys.stderr)
        while self.process and self.process.poll() is None:
            try:
                line = self.process.stdout.readline()
                if not line:
                    break
                    
                try:
                    response = json.loads(line)
                    print(f"DEBUG: [MCPClient._read_responses:line_{caller.f_lineno}] Received raw MCP response: {line.strip()}", file=sys.stderr)
                    print(f"DEBUG: [MCPClient._read_responses:line_{caller.f_lineno}] Parsed MCP response: {json.dumps(response, indent=2)}", file=sys.stderr)
                    self.response_queue.put(response)
                except json.JSONDecodeError:
                    print(f"ERROR: [MCPClient._read_responses:line_{caller.f_lineno}] Failed to parse MCP response: {line}", file=sys.stderr)
            except Exception as e:
                print(f"ERROR: [MCPClient._read_responses:line_{caller.f_lineno}] Error reading MCP response: {e}", file=sys.stderr)
                import traceback
                print(f"ERROR: [MCPClient._read_responses:line_{caller.f_lineno}] Traceback: {traceback.format_exc()}", file=sys.stderr)

    def _write_requests(self):
        """Write requests to the MCP server in a separate thread."""
        caller = inspect.currentframe().f_back
        print(f"DEBUG: [MCPClient._write_requests:line_{caller.f_lineno}] Starting request writer loop", file=sys.stderr)
        while self.process and self.process.poll() is None:
            try:
                request = self.request_queue.get()
                if request is None:
                    break
                    
                request_str = json.dumps(request)
                print(f"DEBUG: [MCPClient._write_requests:line_{caller.f_lineno}] Writing raw MCP request: {request_str}", file=sys.stderr)
                print(f"DEBUG: [MCPClient._write_requests:line_{caller.f_lineno}] Formatted MCP request: {json.dumps(request, indent=2)}", file=sys.stderr)
                self.process.stdin.write(request_str + "\n")
                self.process.stdin.flush()
            except Exception as e:
                print(f"ERROR: [MCPClient._write_requests:line_{caller.f_lineno}] Error writing MCP request: {e}", file=sys.stderr)
                import traceback
                print(f"ERROR: [MCPClient._write_requests:line_{caller.f_lineno}] Traceback: {traceback.format_exc()}", file=sys.stderr)

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool and wait for its response.
        
        Args:
            tool_name (str): Name of the MCP tool to call
            arguments (dict): Arguments for the tool
            
        Returns:
            dict: Response from the MCP server
        """
        caller = inspect.currentframe().f_back
        start_time = time.time()
        print(f"DEBUG: [MCPClient.call_tool:line_{caller.f_lineno}] Starting MCP tool call: {tool_name}", file=sys.stderr)
        print(f"DEBUG: [MCPClient.call_tool:line_{caller.f_lineno}] Tool arguments: {json.dumps(arguments, indent=2)}", file=sys.stderr)
        
        with self._lock:
            self.request_id += 1
            current_id = self.request_id
            
            request = {
                "jsonrpc": "2.0",
                "id": current_id,
                "method": "call_tool",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
        
        print(f"DEBUG: [MCPClient.call_tool:line_{caller.f_lineno}] Queuing MCP request with ID: {current_id}", file=sys.stderr)
        print(f"DEBUG: [MCPClient.call_tool:line_{caller.f_lineno}] Full request payload: {json.dumps(request, indent=2)}", file=sys.stderr)
        self.request_queue.put(request)
        
        # Wait for matching response
        while True:
            response = self.response_queue.get()
            print(f"DEBUG: [MCPClient.call_tool:line_{caller.f_lineno}] Processing response with ID: {response.get('id')} (expecting: {current_id})", file=sys.stderr)
            
            if response.get("id") == current_id:
                if "result" in response:
                    print(f"DEBUG: [MCPClient.call_tool:line_{caller.f_lineno}] Found matching response with result: {json.dumps(response['result'], indent=2)}", file=sys.stderr)
                    result = self._process_response(response["result"])
                    print(f"DEBUG: [MCPClient.call_tool:line_{caller.f_lineno}] MCP tool call completed in {time.time() - start_time:.2f}s", file=sys.stderr)
                    print(f"DEBUG: [MCPClient.call_tool:line_{caller.f_lineno}] Final processed result: {json.dumps(result, indent=2)}", file=sys.stderr)
                    return result
                elif "error" in response:
                    print(f"ERROR: [MCPClient.call_tool:line_{caller.f_lineno}] MCP error response: {json.dumps(response['error'], indent=2)}", file=sys.stderr)
                    return {}
                break
            else:
                # Put non-matching responses back in queue
                print(f"DEBUG: [MCPClient.call_tool:line_{caller.f_lineno}] Re-queuing non-matching response with ID: {response.get('id')}", file=sys.stderr)
                self.response_queue.put(response)
        
        return {}
    
    def _process_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize MCP response format."""
        caller = inspect.currentframe().f_back
        print(f"DEBUG: [MCPClient._process_response:line_{caller.f_lineno}] Processing MCP response: {json.dumps(result, indent=2)}", file=sys.stderr)
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
            print(f"DEBUG: [MCPClient._process_response:line_{caller.f_lineno}] Found content in response: {json.dumps(content, indent=2)}", file=sys.stderr)
            if isinstance(content, list) and len(content) > 0:
                text = content[0].get("text", "")
                print(f"DEBUG: [MCPClient._process_response:line_{caller.f_lineno}] Response text: {text}", file=sys.stderr)
                try:
                    # Try to parse the text content as JSON
                    parsed = json.loads(text)
                    print(f"DEBUG: [MCPClient._process_response:line_{caller.f_lineno}] Successfully parsed JSON response: {json.dumps(parsed, indent=2)}", file=sys.stderr)
                    return parsed
                except json.JSONDecodeError:
                    print(f"DEBUG: [MCPClient._process_response:line_{caller.f_lineno}] Response text is not JSON, returning as text", file=sys.stderr)
                    return {"text": text}
        print(f"DEBUG: [MCPClient._process_response:line_{caller.f_lineno}] Returning unprocessed result: {json.dumps(result, indent=2)}", file=sys.stderr)
        return result

    def __del__(self):
        """Cleanup when the client is destroyed."""
        caller = inspect.currentframe().f_back
        print(f"DEBUG: [MCPClient.__del__:line_{caller.f_lineno}] Cleaning up MCP client", file=sys.stderr)
        if self.process:
            self.request_queue.put(None)  # Signal writer thread to stop
            self.process.terminate()
            self.process.wait()
            print(f"DEBUG: [MCPClient.__del__:line_{caller.f_lineno}] MCP client cleanup complete", file=sys.stderr) 
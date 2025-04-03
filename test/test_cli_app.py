#!/usr/bin/env python
"""
Test script for the CLI app to verify that the infinite loop issue is fixed.
This script simulates a conversation with the booking agent.
"""

import os
import sys
import logging
import subprocess
import time
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_cli.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def run_test():
    """Run a test of the CLI app with a simulated conversation."""
    logger.info("Starting CLI app test")
    
    # Add the parent directory to the path so we can import modules
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Start the CLI app process
    process = subprocess.Popen(
        ["python", os.path.join(project_root, "bin", "cli_app.py")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1  # Line buffered
    )
    
    # Wait for the app to initialize
    time.sleep(2)
    
    # Send a test message
    test_message = "I'd like to book a haircut\n"
    logger.info(f"Sending test message: {test_message.strip()}")
    process.stdin.write(test_message)
    process.stdin.flush()
    
    # Wait for response (with timeout)
    start_time = time.time()
    timeout = 30  # 30 seconds timeout
    output = []
    
    while process.poll() is None and (time.time() - start_time) < timeout:
        # Read output line by line
        line = process.stdout.readline()
        if line:
            output.append(line.strip())
            logger.info(f"Received: {line.strip()}")
        
        # Check for response completion
        if "Booking Agent:" in line:
            logger.info("Response received, waiting for 5 more seconds to ensure no infinite loop")
            # Wait a bit more to ensure no infinite loop
            time.sleep(5)
            break
    
    # Check if we timed out
    if (time.time() - start_time) >= timeout:
        logger.error("Test timed out - possible infinite loop detected")
        process.terminate()
        return False
    
    # Send exit command
    logger.info("Sending exit command")
    process.stdin.write("exit\n")
    process.stdin.flush()
    
    # Wait for process to terminate
    process.wait(timeout=5)
    
    # Get any remaining output
    remaining_output, errors = process.communicate()
    if remaining_output:
        output.extend(remaining_output.strip().split('\n'))
    
    # Log errors if any
    if errors:
        logger.error(f"Errors: {errors}")
    
    # Check if the test was successful
    success = any("Booking Agent:" in line for line in output)
    logger.info(f"Test {'successful' if success else 'failed'}")
    
    return success

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)

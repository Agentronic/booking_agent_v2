#!/usr/bin/env python
"""
Test script for the booking agent functionality.
This script directly tests the handle_booking_request function
with different test cases.
"""
import sys
import os
import logging
import time
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("booking_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the booking request handler
try:
    from app.agent import handle_booking_request
    logger.info("Successfully imported booking agent handler")
except ImportError as e:
    logger.error("Failed to import booking agent: %s", e, exc_info=True)
    print(f"Error: Could not load agent module: {str(e)}")
    sys.exit(1)

def run_test(test_message, test_id):
    """Run a test with the given message and ID."""
    print(f"\n=== TEST {test_id}: '{test_message}' ===")
    
    start_time = time.time()
    print(f"Sending message: '{test_message}'")
    
    try:
        # Call the booking agent handler
        response = handle_booking_request(test_message, f"test_user_{test_id}")
        
        # Print the response
        print(f"\nResponse received in {time.time() - start_time:.2f} seconds:")
        print(f"BOOKING AGENT: {response}")
        print("=" * 80)
        return True
    except Exception as e:
        logger.error("Test failed: %s", e, exc_info=True)
        print(f"ERROR: {str(e)}")
        print("=" * 80)
        return False

def main():
    """Run a series of tests on the booking agent."""
    print("\n===== BOOKING AGENT TEST SUITE =====\n")
    
    # Define test cases
    test_cases = [
        "What time slots do you have available?",
        "I'd like to book a haircut",
        "Can I get a massage tomorrow at 2pm?",
        "Is there any availability for a consultation next week?",
        "I need to cancel my appointment",
    ]
    
    # Run the tests
    success_count = 0
    for i, test_case in enumerate(test_cases):
        if run_test(test_case, i+1):
            success_count += 1
    
    # Print summary
    print(f"\nTest Summary: {success_count}/{len(test_cases)} tests passed")

if __name__ == "__main__":
    main()

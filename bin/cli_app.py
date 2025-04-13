#!/usr/bin/env python
import os
import sys
import logging
from dotenv import load_dotenv
from functools import wraps
import signal

# Debugpy configuration
import debugpy
debugpy.listen(('0.0.0.0', 5678))
# print("Waiting for debugger to attach...")
# debugpy.wait_for_client()
print("Debugger attached!")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("booking_cli.log"),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the conversation handler
try:
    from app.agent import conversational_round_trip
    logger.info("Successfully imported AG2 multi-agent conversation handler")
except ImportError as e:
    logger.error("Failed to load AG2 agent: %s", e, exc_info=True)
    print(f"Error: Could not load agent module: {str(e)}")
    sys.exit(1)

def timeout(seconds=0, minutes=0, hours=0):
    """
    Add a signal-based timeout to any function.
    Usage:
    @timeout(seconds=5)
    def my_slow_function(...)
    Args:
    - seconds: The time limit, in seconds.
    - minutes: The time limit, in minutes.
    - hours: The time limit, in hours.
    """
    limit = seconds + 60 * minutes + 3600 * hours

    def decorator(func):
        def handler(signum, frame):
            raise TimeoutError("timed out after {} seconds".format(limit))

        def wrapper(*args, **kwargs):
            try:
                signal.signal(signal.SIGALRM, handler)
                signal.alarm(limit)
                result = func(*args, **kwargs)
                signal.alarm(0)
                return result
            except TimeoutError as exc:
                raise exc

        return wrapper

    return decorator

async def main():
    """
    Simple CLI interface for the booking agent.
    Uses STDIN/STDOUT for interaction.
    """
    print("\n===== Booking Agent CLI =====")
    print("Type 'exit' or 'quit' to end the conversation.")
    print("Type 'help' for available commands.")
    print("================================\n")
    
    # Generate a unique user ID for this session
    user_id = f"cli_user_{os.getpid()}"
    
    # Welcome message
    print("Welcome to the Booking Agent! I can help you book appointments for:")
    print("- Haircut (30 min)")
    print("- Massage (60 min)")
    print("- Consultation (45 min)")
    print("\nHow can I help you today?")

    # Process input regardless of whether it's from a pipe or terminal
    try:
        while True:
            try:
                # Read input line
                user_input = input("\nYou: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\nThank you for using the Booking Agent. Goodbye!")
                    break
                
                # Check for help command
                if user_input.lower() == 'help':
                    print("\nAvailable commands:")
                    print("- 'exit', 'quit', or 'bye': End the conversation")
                    print("- 'help': Show this help message")
                    print("- 'clear': Clear the conversation history")
                    print("- 'debug on/off': Toggle debug mode")
                    print("\nExample queries:")
                    print("- 'What time slots do you have available?'")
                    print("- 'I'd like to book a haircut tomorrow at 10am'")
                    print("- 'Can I schedule a massage for Friday afternoon?'")
                    continue
                
                # Process the booking request using the centralized conversation handler
                response = await conversational_round_trip(user_input, user_id)
                print(f"\nBooking Agent: {response}")
                
            except (KeyboardInterrupt, EOFError):
                print("\n\nConversation interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\nAn unexpected error occurred: {e}")
    
    except Exception as final_error:
        print(f"\nFatal error: {final_error}")
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

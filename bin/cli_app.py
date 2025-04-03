#!/usr/bin/env python
import os
import sys
import logging
from dotenv import load_dotenv
from functools import wraps
import signal

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
    from app.agent import handle_booking_request
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

def main():
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
    
    # Main conversation loop
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
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
                
            # Process input with a timeout
            @timeout(14)  # 14-second timeout
            def process_input(user_input):
                # Check for exit commands
                if user_input.strip().lower() in ['exit', 'quit']:
                    print("Thank you for using the Booking Agent. Goodbye!")
                    sys.exit(0)
                
                # Process the booking request
                try:
                    response = handle_booking_request(user_input, user_id)
                    # The response is now a string that can be directly printed
                    print(f"\nBooking Agent: {response}")
                except Exception as e:
                    print(f"\nAn unexpected error occurred: {e}")
            
            process_input(user_input)
            
        except KeyboardInterrupt:
            print("\n\nConversation interrupted. Goodbye!")
            break
        except KeyError as e:
            logger.error("Missing key in conversation: %s", e, exc_info=True)
            print(f"\nSorry, there was an error with the conversation: {str(e)}")
            print("Please try again or type 'exit' to quit.")
        except ValueError as e:
            logger.error("Invalid value in conversation: %s", e, exc_info=True)
            print(f"\nSorry, there was an error with your input: {str(e)}")
            print("Please try again or type 'exit' to quit.")
        except Exception as e:
            logger.error("Unexpected error in conversation: %s", e, exc_info=True)
            print(f"\nSorry, there was an unexpected error: {str(e)}")
            print("Please try again or type 'exit' to quit.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python
import os
import sys
import logging
from dotenv import load_dotenv

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

# Import the conversation handler
try:
    from agent import handle_booking_request
    logger.info("Successfully imported AG2 multi-agent conversation handler")
except ImportError as e:
    logger.error("Failed to load AG2 agent: %s", e, exc_info=True)
    print(f"Error: Could not load agent module: {str(e)}")
    sys.exit(1)

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
                
            # Process the user input
            logger.info("User input: %s", user_input)
            response = handle_booking_request(user_input, user_id)
            
            # Display the response
            print(f"\nBooking Agent: {response}")
            
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

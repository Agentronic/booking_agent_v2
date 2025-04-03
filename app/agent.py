"""
Multi-agent framework for booking services using AutoGen (AG2).
Implements three specialized agents:
- User Proxy Agent: Represents the human user in the conversation
- Booking Agent: Coordinates the booking process
- Service Provider Agent: Provides information about services and availability
"""

import autogen
from utils import parse_datetime, format_datetime, get_time_slots
from datetime import datetime, timedelta
import random
import os
import logging
from dotenv import load_dotenv
import json
from app import slot_calendar_tools

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Maintain conversation state between requests
# Each user session would have its own unique key in a real application
CONVERSATION_HISTORY = {
    "default_user": []
}

# Configuration for the agents
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    logger.warning(
        "OPENAI_API_KEY not found in environment variables. AG2 will not function properly.")

config_list = [
    {
        "model": "gpt-4o-mini",
        "api_key": api_key
    }
]

# Agent definitions


def create_agents():
    """Create and configure the three specialized agents."""

    # User Proxy Agent: Represents the human user in the conversation
    user_proxy = autogen.UserProxyAgent(
        name="UserProxy",
        system_message="""You are a proxy for the human user who wants to book a service.
        Your goal is to help the user book an appointment by communicating with the Booking Agent.
        You should express the user's preferences and needs clearly.
        IMPORTANT: Only send ONE message with the user's request and then TERMINATE your participation in the conversation.
        Do not respond to further messages from other agents.""",
        human_input_mode="NEVER",  # In production, set to "ALWAYS" to get actual user input
        # Disable Docker for code execution
        code_execution_config={"use_docker": False}
    )

    # Booking Agent: Coordinates the booking process
    booking_agent = autogen.AssistantAgent(
        name="BookingAgent",
        system_message="""You are a helpful booking assistant.
        Your goal is to coordinate the booking process by understanding user needs
        and working with the Service Provider to check availability and book appointments.
        
        You should gather information about:
        1. The type of service requested (Haircut - 30 min, Massage - 60 min, or Consultation - 45 min)
        2. Preferred date and time (in YYYY-MM-DD and HH:MM format)
        3. Any special requirements
        
        Workflow for booking an appointment:
        1. Collect service information from the user
        2. Ask the Service Provider to check availability for the requested time
        3. If the slot is available, confirm with the user and ask Service Provider to book it
        4. If the slot is not available, ask Service Provider for alternatives and present them to the user
        5. Once booked, provide a confirmation summary to the user
        
        Always ensure dates are in YYYY-MM-DD format and times are in HH:MM 24-hour format when communicating with the Service Provider.
        When communicating with the user, use a more friendly format (e.g., 'Monday, April 5 at 2:30 PM').""",
        llm_config={"config_list": config_list}
    )

    # Service Provider Agent: Provides information about services and availability
    service_provider = autogen.AssistantAgent(
        name="ServiceProvider",
        system_message="""You are a service provider that manages appointment scheduling.
        Your goal is to provide information about available services and time slots.
        
        You offer the following services:
        - Haircut (30 min)
        - Massage (60 min)
        - Consultation (45 min)
        
        You have access to a calendar system to check availability and book appointments.
        Use the following calendar tools when needed:
        
        1. check_slot_availability - Check if a specific time slot is available
           Parameters: date (YYYY-MM-DD), time (HH:MM), duration (minutes)
        
        2. find_next_available_slot - Find the next available slot after a certain time
           Parameters: after_date (YYYY-MM-DD), after_time (HH:MM), duration (minutes)
        
        3. book_appointment - Book an appointment in the calendar
           Parameters: date (YYYY-MM-DD), time (HH:MM), duration (minutes), client_id, service_name
        
        4. cancel_appointment - Cancel an existing appointment
           Parameters: date (YYYY-MM-DD), time (HH:MM)
        
        Always verify slot availability before confirming bookings. If a requested slot is unavailable,
        suggest alternative times using the find_next_available_slot tool.""",
        llm_config={"config_list": config_list}
    )

    return user_proxy, booking_agent, service_provider


def execute_calendar_function(function_name, **kwargs):
    """Execute a calendar function and return the result.

    Args:
        function_name: Name of the calendar function to execute
        **kwargs: Arguments to pass to the function

    Returns:
        Result of the calendar function
    """
    logger.info(
        f"Executing calendar function: {function_name} with args: {kwargs}")

    try:
        # Map function names to actual functions
        function_map = {
            'check_slot_availability': slot_calendar_tools.is_slot_available_tool,
            'find_next_available_slot': slot_calendar_tools.next_available_slot_tool,
            'book_appointment': slot_calendar_tools.book_slot_tool,
            'cancel_appointment': slot_calendar_tools.release_slot_tool
        }

        if function_name not in function_map:
            return {
                'success': False,
                'error': f'Unknown function: {function_name}'
            }

        # Execute the function
        result = function_map[function_name](kwargs)
        logger.info(f"Calendar function result: {result}")
        return result
    except Exception as e:
        logger.error(
            f"Error executing calendar function: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': f'Error executing function: {str(e)}'
        }


def setup_group_chat():
    """Set up the group chat between the three agents."""
    user_proxy, booking_agent, service_provider = create_agents()

    # Register calendar functions with the user proxy agent
    user_proxy.register_function(
        function_map={
            'check_slot_availability': lambda date, time, duration: execute_calendar_function(
                'check_slot_availability', date=date, time=time, duration=int(duration)
            ),
            'find_next_available_slot': lambda after_date, after_time, duration: execute_calendar_function(
                'find_next_available_slot', after_date=after_date, after_time=after_time, duration=int(duration)
            ),
            'book_appointment': lambda date, time, duration, client_id, service_name: execute_calendar_function(
                'book_appointment', date=date, time=time, duration=int(duration), client_id=client_id, service_name=service_name
            ),
            'cancel_appointment': lambda date, time: execute_calendar_function(
                'cancel_appointment', date=date, time=time
            ),
            'get_available_slots': lambda start_date=None, num_days=3, duration=30: get_available_slots(
                start_date, int(num_days), int(duration)
            )
        }
    )

    # Create a group chat with all three agents
    groupchat = autogen.GroupChat(
        agents=[user_proxy, booking_agent, service_provider],
        messages=[],
        max_round=3  # Limited to prevent infinite loops
    )

    # Create a group chat manager to manage the conversation
    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config={"config_list": config_list}
    )

    return user_proxy, manager


def get_available_slots(start_date=None, num_days=3, duration=30):
    """Get actual available time slots from the calendar system.

    Args:
        start_date: Optional starting date (defaults to tomorrow)
        num_days: Number of days to check for availability
        duration: Duration of the appointment in minutes

    Returns:
        List of available time slots in human-readable format
    """
    slots = []

    # Default to tomorrow if no start date provided
    if start_date is None:
        start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Start time at 9 AM
    current_date = start_date
    current_time = "09:00"

    # Check each day
    for day_offset in range(num_days):
        # Calculate the date to check
        if day_offset > 0:
            date_obj = datetime.strptime(
                start_date, "%Y-%m-%d") + timedelta(days=day_offset)
            current_date = date_obj.strftime("%Y-%m-%d")
            current_time = "09:00"  # Reset to beginning of day

        # Find slots for this day (from 9 AM to 5 PM)
        end_of_day = False
        while not end_of_day:
            # Find next available slot
            args = {
                'after_date': current_date,
                'after_time': current_time,
                'duration': duration
            }

            result = slot_calendar_tools.next_available_slot_tool(args)

            if result['success']:
                slot_date = result['date']
                slot_time = result['time']

                # Check if we've moved to the next day
                if slot_date != current_date:
                    break

                # Check if we've reached end of business day (5 PM)
                time_obj = datetime.strptime(slot_time, "%H:%M")
                if time_obj.hour >= 17:
                    end_of_day = True
                    continue

                # Format the slot in a human-readable format
                date_obj = datetime.strptime(slot_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%A, %B %d")
                formatted_time = datetime.strptime(
                    slot_time, "%H:%M").strftime("%I:%M %p")
                slots.append(f"{formatted_date} at {formatted_time}")

                # Move to the next potential slot (add duration + 15 min buffer)
                next_time = datetime.strptime(
                    f"{slot_date} {slot_time}", "%Y-%m-%d %H:%M") + timedelta(minutes=duration+15)
                current_time = next_time.strftime("%H:%M")
            else:
                # If there's an error or no more slots, move to next day
                end_of_day = True

    return slots


def handle_booking_request(user_message, user_id="default_user"):
    """Handle a booking request using the multi-agent system."""
    logger.info(f"Processing booking request: {user_message}")

    try:
        # Check if we have an existing conversation for this user
        existing_conversation = CONVERSATION_HISTORY.get(user_id, [])
        logger.info(f"Found {len(existing_conversation)} previous messages for user")

        # Set up a fresh group chat for each interaction
        user_proxy, manager = setup_group_chat()
        
        # If the user message is empty or just contains whitespace, provide a default message
        if not user_message.strip():
            user_message = "I'd like to book an appointment"
            logger.info("Empty user message, using default: 'I'd like to book an appointment'")

        # Determine if the message is related to availability or booking
        availability_keywords = ["available", "time", "slot", "schedule", "when", "appointment", "book"]
        is_availability_request = any(keyword in user_message.lower() for keyword in availability_keywords)

        # If there's existing conversation, add context to the message
        context_message = user_message
        if existing_conversation:
            # Format previous conversation for context
            context = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                # Include last 5 messages for context
                for msg in existing_conversation[-5:]
            ])
            context_message = f"Previous conversation:\n{context}\n\nCurrent message: {user_message}"
            logger.info("Added conversation context to message")

        # Add available slots information if this is an availability request
        if is_availability_request or not existing_conversation:
            # Get available slots for different service durations
            haircut_slots = get_available_slots(duration=30)  # Haircut - 30 min
            massage_slots = get_available_slots(duration=60)  # Massage - 60 min
            consultation_slots = get_available_slots(duration=45)  # Consultation - 45 min

            # Format the slots information
            slots_info = "\n\nHere are some available time slots:\n"
            slots_info += "\nFor Haircut (30 min):\n" + "\n".join([f"- {slot}" for slot in haircut_slots[:5]])
            slots_info += "\n\nFor Massage (60 min):\n" + "\n".join([f"- {slot}" for slot in massage_slots[:5]])
            slots_info += "\n\nFor Consultation (45 min):\n" + "\n".join([f"- {slot}" for slot in consultation_slots[:5]])

            # Add the slots information to the context message
            context_message += slots_info
            logger.info("Added available slots information to message")

        # Make sure we have a clear user request in the message
        if not any(service in context_message.lower() for service in ["haircut", "massage", "consultation"]) and \
           not any(action in context_message.lower() for action in ["book", "schedule", "appointment"]):
            # Add a clear request if none is present
            context_message = f"I'd like to book an appointment. {context_message}"
            logger.info("Added booking intent to message")
        
        # Set a maximum number of rounds to prevent infinite loops
        max_rounds = 3
        
        # Initiate the conversation with the user's message and context
        logger.info("Starting multi-agent conversation")
        logger.info(f"Sending message to agents: {context_message[:100]}...")
        
        try:
            # Set a timeout for the chat to prevent hanging
            user_proxy.initiate_chat(
                manager,
                message=context_message,
                max_turns=max_rounds  # Limit the number of turns to prevent infinite loops
            )
        except Exception as chat_error:
            logger.warning(f"Chat terminated early: {str(chat_error)}")

        # Access the conversation from the group chat
        groupchat = manager.groupchat
        messages = groupchat.messages
        logger.info(f"Chat completed with {len(messages)} messages")

        # Extract the first response from BookingAgent
        booking_agent_messages = [msg for msg in messages
                                 if msg.get("name") == "BookingAgent"]

        # Get the response content
        if booking_agent_messages:
            # Use the first response from the booking agent
            response_content = booking_agent_messages[0].get("content", "No response available.")
            logger.info(f"Successfully extracted response from BookingAgent")
        else:
            # If no booking agent messages, check for service provider messages
            service_provider_messages = [msg for msg in messages
                                        if msg.get("name") == "ServiceProvider"]
            if service_provider_messages:
                response_content = service_provider_messages[0].get("content", "No response available.")
                logger.info(f"Using ServiceProvider response instead")
            else:
                # No suitable messages found
                logger.warning("No assistant responses found in chat history")
                response_content = "I'm sorry, there was an issue with the booking process. Please try again."

        # Update conversation history
        CONVERSATION_HISTORY[user_id] = CONVERSATION_HISTORY.get(user_id, []) + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response_content}
        ]

        return response_content
    except Exception as e:
        logger.error(
            f"Error in handle_booking_request: {str(e)}", exc_info=True)
        return f"I'm sorry, there was an issue with the booking process: {str(e)}"


def handle_conversation(message, user_id="default_user"):
    """Main entry point for the conversation system."""
    logger.info(f"Received message: {message}")

    try:
        logger.info("Attempting to use AG2 multi-agent system")
        return handle_booking_request(message, user_id)
    except Exception as e:
        logger.error(
            f"AG2 failed with error: {str(e)}. Falling back to basic conversation handler", exc_info=True)
        # Fallback to basic conversation handler if AG2 fails
        from basic_conversation import handle_conversation as basic_handler
        basic_response = basic_handler(message)

        # Still maintain conversation history even in fallback mode
        CONVERSATION_HISTORY[user_id] = CONVERSATION_HISTORY.get(user_id, []) + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": basic_response}
        ]

        return f"The booking system encountered an error. Falling back to basic mode. {basic_response}"

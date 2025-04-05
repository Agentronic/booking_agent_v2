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
from app.calendar import slot_calendar_tools

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
        
        When asked for input and no user input is available:
        1. If the conversation is about selecting a time slot, respond with: "I'll take the earliest available slot."
        2. If asked for confirmation, respond with: "Yes, please book that appointment."
        3. For any other questions, respond with: "Please proceed with the booking process."
        
        This will help keep the conversation flowing even when the user can't provide immediate input.""",
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
        
        IMPORTANT: You must ALWAYS use the tools via slot_calendar_tools for any availability or booking operations.
        NEVER make assumptions or best guesses about availability or bookings.

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
        max_round=10,  # Increased to allow for more complex conversations
        speaker_selection_method="round_robin"  # Ensures each agent gets a turn in order
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

                # Move to the next potential slot (just add duration without buffer)
                next_time = datetime.strptime(
                    f"{slot_date} {slot_time}", "%Y-%m-%d %H:%M") + timedelta(minutes=duration)
                current_time = next_time.strftime("%H:%M")
            else:
                # If there's an error or no more slots, move to next day
                end_of_day = True

    return slots


# Note: The handle_booking_request function has been refactored into the BookingAgentService class
# This function is maintained for backward compatibility
def handle_booking_request(user_message, user_id="default_user"):
    """Legacy function that delegates to the centralized BookingAgentService."""
    logger.info(f"Using legacy handle_booking_request with: {user_message}")
    return booking_agent_service.process_message(user_message, user_id)


class BookingAgentService:
    """
    Central service that encapsulates all booking agent functionality.
    This class maintains conversation state and handles booking logic
    independent of the frontend (CLI or web UI).
    """
    
    def __init__(self):
        """Initialize the booking agent service."""
        # Maintain conversation state for each user
        self.conversation_history = {}
    
    def get_user_state(self, user_id):
        """Get or initialize user state."""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = {
                "messages": [],
                "state": "initial", 
                "service": None,
                "date": None,
                "time": None,
                "duration": None,
                "available_slots": []
            }
        return self.conversation_history[user_id]
    
    def process_message(self, message, user_id="default_user"):
        """
        Process a user message and maintain conversation state.
        
        Args:
            message: The user's message text
            user_id: Unique identifier for the user/session
            
        Returns:
            Response message from the booking agent
        """
        logger.info(f"Processing message: {message} for user: {user_id}")
        
        # Get or initialize user state
        user_state = self.get_user_state(user_id)
        user_state["messages"].append({"role": "user", "content": message})
        
        # Process the message based on current state
        response = self.handle_booking_request(message, user_state)
        
        # Store the response
        user_state["messages"].append({"role": "assistant", "content": response})
        return response
            
    
    def handle_booking_request(self, user_message, user_state):
        """
        Handle a booking request based on user message and current state.
        
        Args:
            user_message: The user's message text
            user_state: The user's current conversation state
            
        Returns:
            Response message from the booking agent
        """
        try:
            # Check if this is a confirmation message
            if user_state["state"] == "confirming" and any(word in user_message.lower() for word in ["yes", "confirm", "book", "ok", "sure"]):
                
                # User is confirming the booking
                client_id = f"user_{user_state.get('user_id', 'default')}_{int(datetime.now().timestamp())}"
                
                # Book the appointment
                booking_args = {
                    "date": user_state["date"],
                    "time": user_state["time"],
                    "duration": user_state["duration"],
                    "client_id": client_id,
                    "service_name": user_state["service"]
                }
                
                booking_result = slot_calendar_tools.book_slot_tool(booking_args)
                
                if booking_result["success"] and booking_result.get("booked", False):
                    date_obj = datetime.strptime(user_state["date"], "%Y-%m-%d")
                    time_obj = datetime.strptime(user_state["time"], "%H:%M")
                    formatted_date = date_obj.strftime("%A, %B %d")
                    formatted_time = time_obj.strftime("%I:%M %p")
                    
                    response = f"""Your {user_state["service"].lower()} appointment has been confirmed for {formatted_date} at {formatted_time}.
Your booking reference is {client_id}.
Thank you for booking with us!"""
                    user_state["state"] = "booked"
                else:
                    response = f"""I'm sorry, I couldn't book that slot. It may no longer be available.
Would you like to see other available slots?"""
                    user_state["state"] = "initial"
            
            # Check for a request to show available slots
            elif "available" in user_message.lower() or "slots" in user_message.lower() or "times" in user_message.lower():
                # Detect service type if mentioned
                service = None
                duration = 30  # Default duration
                
                if "haircut" in user_message.lower():
                    service = "Haircut"
                    duration = 30
                elif "massage" in user_message.lower():
                    service = "Massage"
                    duration = 60
                elif "consultation" in user_message.lower():
                    service = "Consultation"
                    duration = 45
                elif user_state["service"]:
                    # Use the previously mentioned service
                    service = user_state["service"]
                    if service == "Haircut":
                        duration = 30
                    elif service == "Massage":
                        duration = 60
                    elif service == "Consultation":
                        duration = 45
                
                # Get today and tomorrow dates
                today = datetime.now().date()
                tomorrow = today + timedelta(days=1)
                date = tomorrow.strftime("%Y-%m-%d")
                
                # Find available slots
                available_slots = get_available_slots(start_date=date, duration=duration)
                
                response = f"""Here are the available slots for {service}:
{chr(10).join([f"- {slot}" for slot in available_slots[:5]])}

Would you like to book one of these slots?"""
                
                user_state["state"] = "selecting"
                user_state["service"] = service
                user_state["duration"] = duration
                user_state["available_slots"] = available_slots[:5]
            
            # Handle a new booking request
            elif any(word in user_message.lower() for word in ["book", "schedule", "appointment"]):
                # Parse the user's message to extract key details
                service = None
                date = None
                time = None
                
                # Detect service type
                if "haircut" in user_message.lower():
                    service = "Haircut"
                    duration = 30
                elif "massage" in user_message.lower():
                    service = "Massage"
                    duration = 60
                elif "consultation" in user_message.lower():
                    service = "Consultation"
                    duration = 45
                else:
                    service = "Haircut"  # Default to haircut
                    duration = 30
                
                # Try to parse date
                today = datetime.now().date()
                tomorrow = today + timedelta(days=1)
                
                if "tomorrow" in user_message.lower():
                    date = tomorrow.strftime("%Y-%m-%d")
                else:
                    # Use tomorrow's date as default
                    date = tomorrow.strftime("%Y-%m-%d")
                
                # Try to parse time
                import re
                time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(am|pm)?', user_message.lower())
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2) or "00")
                    am_pm = time_match.group(3)
                    
                    if am_pm == "pm" and hour < 12:
                        hour += 12
                    elif am_pm == "am" and hour == 12:
                        hour = 0
                    
                    time = f"{hour:02d}:{minute:02d}"
                else:
                    # Default to first available slot
                    time = "09:00"
                
                # Find available slots
                available_slots = get_available_slots(start_date=date, duration=duration)
                
                # Check if the requested time is available
                formatted_time = datetime.strptime(time, "%H:%M").strftime("%I:%M %p")
                formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%A, %B %d")
                
                # Save the state
                user_state["state"] = "confirming"
                user_state["service"] = service
                user_state["date"] = date
                user_state["time"] = time
                user_state["duration"] = duration
                user_state["available_slots"] = available_slots[:5]
                
                # Direct response with booking details
                response = f"""Great! I can help you book a {service.lower()} for {formatted_date} at {formatted_time}.

Available slots for {service} on {formatted_date}:
{chr(10).join([f"- {slot}" for slot in available_slots[:5]])}

Would you like to confirm this booking?"""
            
            # Default fallback response
            else:
                response = """I can help you book an appointment for a haircut, massage, or consultation.
What service would you like to book?"""
                user_state["state"] = "initial"
            
            return response
        
        except Exception as e:
            logger.error(f"Error in handle_booking_request: {str(e)}", exc_info=True)
            return f"I'm sorry, there was an issue with the booking process: {str(e)}"

# Create a global instance of the booking agent service
booking_agent_service = BookingAgentService()

def handle_conversation(message, user_id="default_user"):
    """
    Main entry point for the conversation system.
    This function delegates to the BookingAgentService.
    """
    logger.info(f"Received message: {message}")
    
    logger.info("Using BookingAgentService to handle message")
    return booking_agent_service.process_message(message, user_id)

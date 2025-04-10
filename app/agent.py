"""
Multi-agent framework for booking services using AutoGen (AG2).
Implements three specialized agents:
- User Proxy Agent: Represents the human user in the conversation
- Booking Agent: Coordinates the booking process
- Service Provider Agent: Provides information about services and availability
"""

import autogen
from app.utils import parse_datetime, format_datetime
from datetime import datetime, timedelta
import random
import os
import logging
from dotenv import load_dotenv
import json
from autogen.mcp import create_toolkit
from app.mcp.client import MCPClient
import asyncio

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
service_provider = None

async def create_agents():
    """Create and configure the three specialized agents."""
    global service_provider
    
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
        2. Ask the Service Provider to check availability for the requested time always
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
        
        IMPORTANT: You must ALWAYS use the tools from your toolkit(mcp) for any availability or booking operations.
        NEVER make assumptions or best guesses about availability or bookings, always use the tools.
        
        Always verify slot availability before confirming bookings. If a requested slot is unavailable,
        suggest alternative times using the find_next_available_slot tool.""",
        llm_config={"config_list": config_list}
    )

    # Initialize the MCP client
    client = MCPClient()
    await client.initialize()  # Ensure the client is initialized
    
    # Create a toolkit instance using the MCP client session
    toolkit = await create_toolkit(session=client.session)
    
    # Register the toolkit with the service provider agent so it can use the tools
    toolkit.register_for_llm(service_provider)

    return user_proxy, booking_agent, service_provider


async def setup_group_chat():
    """Set up the group chat between the three agents."""
    user_proxy, booking_agent, service_provider = await create_agents()

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

        # Use the existing service provider agent
        self.service_provider = service_provider
    
    async def get_available_slots(self, start_date=None, num_days=3, duration=30):
        """Get available time slots by communicating with the Service Provider Agent.

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
                # Ask Service Provider Agent to check slot availability
                message = f"Check if slot is available on {current_date} at {current_time} for {duration} minutes"
                result = await service_provider.a_run(
                    message=message,
                    tools=service_provider.toolkit.tools,
                    max_turns=2
                )
                
                if result and isinstance(result, list) and len(result) > 0:
                    # If the slot is available, add it to the list
                    if "available" in result[0].text.lower():
                        # Format the slot in a human-readable format
                        date_obj = datetime.strptime(current_date, "%Y-%m-%d")
                        formatted_date = date_obj.strftime("%A, %B %d")
                        formatted_time = datetime.strptime(
                            current_time, "%H:%M").strftime("%I:%M %p")
                        slots.append(f"{formatted_date} at {formatted_time}")

                # Check if we've reached end of business day (5 PM)
                time_obj = datetime.strptime(current_time, "%H:%M")
                if time_obj.hour >= 17:
                    end_of_day = True
                    continue

                # Move to the next 30-minute interval
                next_time = datetime.strptime(
                    f"{current_date} {current_time}", "%Y-%m-%d %H:%M") + timedelta(minutes=30)
                current_time = next_time.strftime("%H:%M")

        return slots

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
    
    async def process_message(self, message, user_id="default_user"):
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
        response = await self.handle_booking_request(message, user_state)
        
        # Store the response
        user_state["messages"].append({"role": "assistant", "content": response})
        return response
            
    
    async def handle_booking_request(self, user_message, user_state):
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
                
                # Ask Service Provider Agent to book the slot
                message = f"Book a slot on {user_state['date']} at {user_state['time']} for {user_state['duration']} minutes for client {client_id} for service {user_state['service']}"
                booking_result = await service_provider.a_run(
                    message=message,
                    tools=service_provider.toolkit.tools,
                    max_turns=2
                )
                
                if booking_result and isinstance(booking_result, list) and len(booking_result) > 0:
                    booking_response = booking_result[0].text
                    return f"Booking confirmed! {booking_response}"
                else:
                    return "Sorry, I couldn't complete the booking. Please try again."
            
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
                available_slots = await self.get_available_slots(start_date=date, duration=duration)
                
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
                available_slots = await self.get_available_slots(start_date=date, duration=duration)
                
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

async def handle_conversation(message, user_id="default_user"):
    """
    Main entry point for the conversation system.
    This function delegates to the BookingAgentService.
    """
    logger.info(f"Received message: {message}")
    
    logger.info("Using BookingAgentService to handle message")
    return await booking_agent_service.process_message(message, user_id)

# Initialize the booking agent service and group chat
booking_agent_service = BookingAgentService()

# Initialize the group chat
asyncio.run(setup_group_chat())

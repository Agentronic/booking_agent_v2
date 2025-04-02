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

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Maintain conversation state between requests
# Each user session would have its own unique key in a real application
CONVERSATION_HISTORY = {
    "default_user": []
}

# Configuration for the agents
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    logger.warning("OPENAI_API_KEY not found in environment variables. AG2 will not function properly.")

config_list = [
    {
        "model": "gpt-3.5-turbo",
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
        You should express the user's preferences and needs clearly.""",
        human_input_mode="NEVER",  # In production, set to "ALWAYS" to get actual user input
        code_execution_config={"use_docker": False}  # Disable Docker for code execution
    )
    
    # Booking Agent: Coordinates the booking process
    booking_agent = autogen.AssistantAgent(
        name="BookingAgent",
        system_message="""You are a helpful booking assistant.
        Your goal is to coordinate the booking process by understanding user needs
        and checking availability with the Service Provider.
        
        You should gather information about:
        1. The type of service requested
        2. Preferred date and time
        3. Any special requirements
        
        After collecting this information, work with the Service Provider to find available slots.""",
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
        
        When asked about availability, check if the requested time slot is available
        and provide alternative options if needed.""",
        llm_config={"config_list": config_list}
    )
    
    return user_proxy, booking_agent, service_provider

def setup_group_chat():
    """Set up the group chat between the three agents."""
    user_proxy, booking_agent, service_provider = create_agents()
    
    # Create a group chat with all three agents
    groupchat = autogen.GroupChat(
        agents=[user_proxy, booking_agent, service_provider],
        messages=[],
        max_round=10  # Limit the conversation to 10 rounds
    )
    
    # Create a group chat manager to manage the conversation
    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config={"config_list": config_list}
    )
    
    return user_proxy, manager

def generate_available_slots():
    """Generate some fake available time slots."""
    now = datetime.now()
    slots = []
    
    # Generate slots for the next 3 days
    for i in range(1, 4):
        day = now + timedelta(days=i)
        # Random number of slots per day (2-4)
        num_slots = random.randint(2, 4)
        
        for _ in range(num_slots):
            # Random hour between 9 AM and 4 PM
            hour = random.randint(9, 16)
            # Minutes either 00 or 30
            minute = random.choice([0, 30])
            
            slot_time = day.replace(hour=hour, minute=minute, second=0, microsecond=0)
            slots.append(slot_time.strftime("%A, %B %d at %I:%M %p"))
    
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
        
        # If there's existing conversation, add context to the message
        context_message = user_message
        if existing_conversation:
            # Format previous conversation for context
            context = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in existing_conversation[-5:]  # Include last 5 messages for context
            ])
            context_message = f"Previous conversation:\n{context}\n\nCurrent message: {user_message}"
            logger.info("Added conversation context to message")
        
        # Initiate the conversation with the user's message and context
        logger.info("Starting multi-agent conversation")
        user_proxy.initiate_chat(
            manager,
            message=context_message
        )
        
        # Access the conversation from the group chat
        groupchat = manager.groupchat
        messages = groupchat.messages
        logger.info(f"Chat completed with {len(messages)} messages")
        
        # Extract responses from BookingAgent
        logger.info(f"Message structure: {messages[0].keys() if messages else 'No messages'}")
        # Dump the first few messages for debugging
        for i, msg in enumerate(messages[:3]):
            logger.info(f"Message {i}: {msg}")
            
        # Filter for BookingAgent messages
        booking_agent_messages = [msg for msg in messages 
                                if msg.get("name") == "BookingAgent" or 
                                   (msg.get("role") == "assistant" and msg.get("name") != "UserProxy")]
        
        # Get the response content
        response_content = None
        if booking_agent_messages:
            final_message = booking_agent_messages[-1]
            logger.info(f"Successfully extracted final response from {final_message.get('name', 'unknown')}")
            response_content = final_message.get("content", "No response available.")
        else:
            # If no booking agent messages, just return the last non-user message
            non_user_messages = [msg for msg in messages if msg.get("name") != "UserProxy"]
            if non_user_messages:
                response_content = non_user_messages[-1].get("content", "No response available.")
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
        logger.error(f"Error in handle_booking_request: {str(e)}", exc_info=True)
        return f"I'm sorry, there was an issue with the booking process: {str(e)}"

def handle_conversation(message, user_id="default_user"):
    """Main entry point for the conversation system."""
    logger.info(f"Received message: {message}")
    
    try:
        logger.info("Attempting to use AG2 multi-agent system")
        return handle_booking_request(message, user_id)
    except Exception as e:
        logger.error(f"AG2 failed with error: {str(e)}. Falling back to basic conversation handler", exc_info=True)
        # Fallback to basic conversation handler if AG2 fails
        from basic_conversation import handle_conversation as basic_handler
        basic_response = basic_handler(message)
        
        # Still maintain conversation history even in fallback mode
        CONVERSATION_HISTORY[user_id] = CONVERSATION_HISTORY.get(user_id, []) + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": basic_response}
        ]
        
        return f"The booking system encountered an error. Falling back to basic mode. {basic_response}"
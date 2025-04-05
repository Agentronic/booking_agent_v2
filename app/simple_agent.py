#!/usr/bin/env python
"""
Simplified booking agent that directly uses the calendar tools
without the multi-agent system.
"""
import os
import sys
import logging
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simple_agent.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import calendar tools
try:
    from app.calendar import slot_calendar
    from app.calendar import slot_calendar_tools
    logger.info("Successfully imported calendar tools")
except ImportError as e:
    logger.error("Failed to import calendar tools: %s", e, exc_info=True)
    print(f"Error: Could not load calendar tools: {str(e)}")
    sys.exit(1)

# Store conversation history
CONVERSATION_HISTORY = {}

def format_time_slot(slot):
    """Format a time slot for display."""
    try:
        dt = datetime.fromisoformat(slot)
        return dt.strftime("%A, %B %d at %I:%M %p")
    except (ValueError, TypeError):
        return str(slot)

def get_available_slots(service_type=None):
    """Get available slots for a service type."""
    try:
        # Define service durations
        service_duration = {
            "haircut": 30,
            "massage": 60,
            "consultation": 45
        }
        
        # Format the response
        response = "Here are some available time slots:\n\n"
        
        # Get tomorrow's date as a starting point
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_date = tomorrow.strftime("%Y-%m-%d")
        tomorrow_time = "09:00"  # Start at 9 AM
        
        # Generate slots for each service type
        services_to_check = [service_type.lower()] if service_type and service_type.lower() in service_duration else service_duration.keys()
        
        for service in services_to_check:
            duration = service_duration[service]
            response += f"For {service.capitalize()} ({duration} min):\n"
            
            # Find 5 available slots for this service
            current_date, current_time = tomorrow_date, tomorrow_time
            slots_found = 0
            
            while slots_found < 5:
                # Find next available slot
                result = slot_calendar.next_available_slot((current_date, current_time), duration)
                
                if not result:
                    response += "- No more slots available\n"
                    break
                    
                next_date, next_time = result
                
                # Format and add to response
                dt_str = f"{next_date} {next_time}"
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                formatted_time = dt.strftime("%A, %B %d at %I:%M %p")
                response += f"- {formatted_time}\n"
                
                # Update for next iteration
                # Move forward by 15 minutes to find the next slot
                dt = dt + timedelta(minutes=15)
                current_date = dt.strftime("%Y-%m-%d")
                current_time = dt.strftime("%H:%M")
                
                slots_found += 1
            
            response += "\n"
        
        return response
    except Exception as e:
        logger.error("Error getting available slots: %s", e, exc_info=True)
        return f"Sorry, I couldn't retrieve the available slots. Error: {str(e)}"

def process_booking_request(service_type, date_time=None):
    """Process a booking request."""
    try:
        # Validate service type
        valid_services = ["haircut", "massage", "consultation"]
        if service_type.lower() not in valid_services:
            return f"Sorry, we don't offer '{service_type}' as a service. Available services are: Haircut, Massage, and Consultation."
        
        # Map service type to duration
        service_duration = {
            "haircut": 30,
            "massage": 60,
            "consultation": 45
        }
        duration = service_duration.get(service_type.lower())
        
        # Generate a client ID (would normally come from user authentication)
        client_id = f"client_{int(datetime.now().timestamp())}"
        
        # If no specific date/time, book the next available slot
        if not date_time:
            # Get tomorrow's date as a starting point
            tomorrow = datetime.now() + timedelta(days=1)
            tomorrow_date = tomorrow.strftime("%Y-%m-%d")
            tomorrow_time = "09:00"  # Start at 9 AM
            
            # Find next available slot
            result = slot_calendar.next_available_slot((tomorrow_date, tomorrow_time), duration)
            
            if not result:
                return f"Sorry, there are no available slots for {service_type}."
            
            date, time = result
            
            # Book the slot
            booking_success = slot_calendar.book_slot(
                date=date,
                start_time=time,
                duration=duration,
                client_id=client_id,
                service_name=service_type
            )
            
            # Format the response
            if booking_success:
                dt_str = f"{date} {time}"
                dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                formatted_time = dt.strftime("%A, %B %d at %I:%M %p")
                return f"Great! I've booked your {service_type} appointment for {formatted_time}. Your client ID is {client_id}."
            else:
                return f"Sorry, I couldn't book your appointment. The slot may no longer be available."
        else:
            # TODO: Parse date_time and book specific slot
            return f"Sorry, booking for specific times is not implemented yet."
    except Exception as e:
        logger.error("Error processing booking request: %s", e, exc_info=True)
        return f"Sorry, I couldn't process your booking request. Error: {str(e)}"

def process_cancellation_request(client_id=None):
    """Process a cancellation request."""
    try:
        # Note: The current slot_calendar implementation doesn't have a way to list
        # appointments by client ID. In a real system, we would query the database
        # to find appointments for the client.
        
        # For now, we'll simulate this by providing a message about the limitation
        if not client_id:
            return "To cancel an appointment, please provide your client ID and the date and time of your appointment."
        else:
            # In a real implementation, we would look up the appointment details
            # For now, we'll ask for more information
            return f"I found your client ID {client_id}, but I need the date and time of your appointment to cancel it. Please provide this information."
    except Exception as e:
        logger.error("Error processing cancellation request: %s", e, exc_info=True)
        return f"Sorry, I couldn't process your cancellation request. Error: {str(e)}"

def handle_simple_booking_request(user_message, user_id="default_user"):
    """
    Handle a booking request using the simplified agent.
    This function directly uses the calendar tools without the multi-agent system.
    """
    logger.info("Processing booking request: %s", user_message)
    
    try:
        # Check if we have an existing conversation for this user
        existing_conversation = CONVERSATION_HISTORY.get(user_id, [])
        logger.info("Found %d previous messages for user", len(existing_conversation))
        
        # Determine the intent of the message
        message_lower = user_message.lower()
        
        # Check for availability request
        if any(keyword in message_lower for keyword in ["available", "time", "slot", "schedule", "when"]):
            # Extract service type if mentioned
            service_type = None
            if "haircut" in message_lower:
                service_type = "haircut"
            elif "massage" in message_lower:
                service_type = "massage"
            elif "consultation" in message_lower:
                service_type = "consultation"
            
            # Get available slots
            response = get_available_slots(service_type)
            
            # Add follow-up question
            response += "\nWhich service would you like to book? (Haircut, Massage, or Consultation)"
        
        # Check for booking request
        elif any(keyword in message_lower for keyword in ["book", "schedule", "appointment", "reserve"]):
            # Extract service type
            service_type = None
            if "haircut" in message_lower:
                service_type = "haircut"
            elif "massage" in message_lower:
                service_type = "massage"
            elif "consultation" in message_lower:
                service_type = "consultation"
            
            if not service_type:
                response = "What type of service would you like to book? (Haircut, Massage, or Consultation)"
            else:
                # Process the booking request
                response = process_booking_request(service_type)
        
        # Check for cancellation request
        elif any(keyword in message_lower for keyword in ["cancel", "reschedule", "delete"]):
            # Extract booking ID if mentioned
            booking_id = None
            # TODO: Extract booking ID from message
            
            # Process the cancellation request
            response = process_cancellation_request(booking_id)
        
        # Default response
        else:
            response = """I can help you with booking appointments! Here's what I can do:
1. Check available time slots
2. Book an appointment (Haircut, Massage, or Consultation)
3. Cancel an existing appointment

What would you like to do?"""
        
        # Store the conversation
        existing_conversation.append({
            "role": "user",
            "content": user_message
        })
        existing_conversation.append({
            "role": "assistant",
            "content": response
        })
        CONVERSATION_HISTORY[user_id] = existing_conversation
        
        return response
    except Exception as e:
        logger.error("Error handling booking request: %s", e, exc_info=True)
        return f"Sorry, I encountered an error while processing your request: {str(e)}"

if __name__ == "__main__":
    # Test the agent
    test_messages = [
        "What time slots do you have available?",
        "I'd like to book a haircut",
        "Can I get a massage tomorrow at 2pm?",
        "I need to cancel my appointment"
    ]
    
    for msg in test_messages:
        print(f"\n>>> User: {msg}")
        response = handle_simple_booking_request(msg)
        print(f">>> Agent: {response}")

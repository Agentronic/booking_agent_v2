"""
Basic conversation handling for the booking agent (Phase 1).
This is a temporary implementation that will be replaced with the AG2 framework in Phase 2.
"""

import re
from datetime import datetime, timedelta
import random

# Simple pattern matching for booking intents
GREETING_PATTERNS = [r'hi\b', r'hello\b', r'hey\b', r'greetings', r'howdy']
BOOKING_PATTERNS = [r'book', r'schedule', r'appointment', r'reserve', r'slot']
TIME_PATTERNS = [r'today', r'tomorrow', r'next week', r'monday', r'tuesday', r'wednesday', 
                 r'thursday', r'friday', r'saturday', r'sunday', r'\d{1,2}(?::\d{2})?\s*(?:am|pm)',
                 r'\d{1,2}(?::\d{2})?']
SERVICE_PATTERNS = [r'haircut', r'massage', r'consultation', r'meeting', r'call', r'service']

def detect_intent(message):
    """Detect user intent from message."""
    message = message.lower()
    
    if any(re.search(pattern, message) for pattern in GREETING_PATTERNS):
        return "greeting"
    
    if any(re.search(pattern, message) for pattern in BOOKING_PATTERNS):
        if any(re.search(pattern, message) for pattern in TIME_PATTERNS):
            return "booking_with_time"
        if any(re.search(pattern, message) for pattern in SERVICE_PATTERNS):
            return "booking_with_service"
        return "booking_general"
    
    return "unknown"

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

def handle_conversation(message):
    """Handle conversation based on detected intent."""
    intent = detect_intent(message)
    
    if intent == "greeting":
        return "Hello! I'm your booking assistant. How can I help you schedule an appointment today?"
    
    elif intent == "booking_general":
        return "I'd be happy to help you book an appointment. What service are you interested in, and when would you like to schedule it?"
    
    elif intent == "booking_with_service":
        return "Great! I can help with that. When would you like to schedule your appointment?"
    
    elif intent == "booking_with_time":
        # Generate some fake available slots
        available_slots = generate_available_slots()
        slots_text = "\n".join([f"• {slot}" for slot in available_slots])
        
        return f"I found several available slots around that time:\n\n{slots_text}\n\nWhich one would you prefer?"
    
    else:
        return "I'm still learning how to help with bookings. Could you try asking about scheduling an appointment?"
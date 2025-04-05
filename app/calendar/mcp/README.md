# Slot Calendar MCP Server

This is an MCP (Model Context Protocol) server that exposes the slot calendar functionality through a standardized interface.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python server.py
```

## Available Methods

The server exposes the following methods from the slot calendar:

1. `is_slot_available(date: str, time: str, duration: int) -> bool`
   - Checks if a slot is available at the specified date and time
   - Returns True if available, False otherwise

2. `book_slot(date: str, start_time: str, duration: int, client_id: str, service_name: str) -> Optional[int]`
   - Books a slot at the specified date and time
   - Returns the booking ID if successful, None otherwise

3. `cancel_booking(booking_id: int) -> bool`
   - Cancels a booking with the specified ID
   - Returns True if successful, False otherwise

4. `slots_available_on_day(date: str, duration: int) -> List[str]`
   - Returns a list of available start times for the specified date
   - Times are returned in HH:MM format

## Example Usage

The server can be accessed using any MCP-compatible client. Here's an example using Python:

```python
from mcp.client import Client

client = Client("http://localhost:8000")  # Adjust port as needed

# Check slot availability
result = client.call("is_slot_available", {
    "date": "2024-03-20",
    "time": "14:00",
    "duration": 30
})

# Book a slot
booking_id = client.call("book_slot", {
    "date": "2024-03-20",
    "start_time": "14:00",
    "duration": 30,
    "client_id": "client123",
    "service_name": "Consultation"
})
```

## Error Handling

The server will return appropriate error responses for:
- Invalid input parameters
- Database errors
- Unavailable slots
- Non-existent bookings
- Unsupported methods 
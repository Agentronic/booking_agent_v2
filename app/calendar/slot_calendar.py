#!/usr/bin/env python3
"""
Simple calendar booking system using SQLite.

This module provides basic functions to manage and query appointment slots.
It is designed to be simple and is intended as a placeholder until
integration with external calendar services.
"""

import sqlite3
import os
import logging
from pathlib import Path
from datetime import datetime, time, date as date_obj, timedelta
from typing import List, Tuple, Optional

# Set up logging
log_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) / 'logs'
log_dir.mkdir(exist_ok=True)
log_file = log_dir / 'slot_calendar.log'

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()  # Also log to console for development
    ]
)
logger = logging.getLogger('slot_calendar')

# Database configuration
DB_NAME = 'calendar.db'
# Determine project root assuming script is in app/calendar/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, DB_NAME)

# --- Database Setup ---

def setup_database(db_path: str = DB_PATH):
    """
    Initializes the SQLite database and the bookings table if they don't exist.

    Args:
        db_path: The path to the database file. Defaults to DB_PATH.
    """
    logger.info(f"Setting up database at: {db_path}")
    # Ensure the directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL, -- Store end time for easier overlap checks
            duration_minutes INTEGER NOT NULL,
            customer_id TEXT NOT NULL,
            service_name TEXT NOT NULL
            -- UNIQUE constraint removed to allow manual ID setting if needed,
            -- but overlap check in book_slot prevents double booking.
            -- UNIQUE (date, start_time)
        )
        ''')
        # Index for faster lookups by date
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_booking_date ON bookings (date);")
        conn.commit()
        conn.close()
        logger.info("Database setup complete.")
    except sqlite3.Error as e:
        logger.error(f"Database error during setup: {e}")
        raise # Re-raise the exception

# --- Helper Functions ---

def _validate_duration(duration: int):
    """Raises ValueError if duration is not a positive multiple of 15."""
    if not isinstance(duration, int) or duration <= 0 or duration % 15 != 0:
        raise ValueError("Duration must be a positive integer multiple of 15 minutes.")

def _parse_time(time_str: str) -> time:
    """Parses HH:MM string to time object."""
    return datetime.strptime(time_str, "%H:%M").time()

def _format_time(time_obj: time) -> str:
    """Formats time object to HH:MM string."""
    return time_obj.strftime("%H:%M")

def _parse_date(date_str: str) -> date_obj:
    """Parses YYYY-MM-DD string to date object."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def _combine_datetime(date_val: date_obj, time_val: time) -> datetime:
    """Combines date and time objects into a datetime object."""
    return datetime.combine(date_val, time_val)

def _calculate_end_datetime(start_dt: datetime, duration: int) -> datetime:
    """Calculates end datetime given start and duration."""
    return start_dt + timedelta(minutes=duration)

# --- Core Calendar Functions ---

def is_slot_available(date: str, time: str, duration: int) -> bool:
    """
    Checks if the entire time slot from the given date and time, lasting
    for the specified duration, is available.

    Args:
        date: The date in YYYY-MM-DD format.
        time: The start time in HH:MM format.
        duration: The duration in minutes (multiple of 15).

    Returns:
        True if the slot is available, False otherwise.
    """
    _validate_duration(duration)
    try:
        req_start_dt = _combine_datetime(_parse_date(date), _parse_time(time))
        req_end_dt = _calculate_end_datetime(req_start_dt, duration)

        conn = sqlite3.connect(DB_PATH)
        # Use context manager for connection
        with conn:
            cursor = conn.cursor()
            # Query for bookings that overlap with the requested slot on the same date
            # Overlap conditions:
            # 1. Existing booking starts during the requested slot (exclusive of end time)
            # 2. Existing booking ends during the requested slot (exclusive of start time)
            # 3. Existing booking completely contains the requested slot
            cursor.execute("""
                SELECT 1 FROM bookings
                WHERE date = ? AND (
                    (start_time < ? AND end_time > ?) OR -- Existing overlaps requested start
                    (start_time < ? AND end_time > ?) OR -- Existing overlaps requested end
                    (start_time >= ? AND end_time <= ?)   -- Existing contained within requested (shouldn't happen with above checks but safe)
                ) LIMIT 1
            """, (date, _format_time(req_end_dt.time()), _format_time(req_start_dt.time()), # Cond 1 & 2 combined
                  _format_time(req_end_dt.time()), _format_time(req_start_dt.time()), # Redundant but clearer
                  _format_time(req_start_dt.time()), _format_time(req_end_dt.time()) # Cond 3
                 ))
            # Simplified overlap check: An overlap occurs if the requested slot's start time is before an existing slot's end time,
            # AND the requested slot's end time is after the existing slot's start time.
            cursor.execute("""
                SELECT 1 FROM bookings
                WHERE date = ? AND end_time > ? AND start_time < ?
                LIMIT 1
            """, (date, time, _format_time(req_end_dt.time())))

            overlapping_booking = cursor.fetchone()

        return overlapping_booking is None # Available if no overlap found

    except sqlite3.Error as e:
        logger.error(f"Database error in is_slot_available: {e}")
        return False # Treat database errors as unavailable for safety
    except ValueError as e:
        logger.error(f"Input error in is_slot_available: {e}")
        return False # Invalid input means slot is not available in the requested format

def book_slot(date: str, start_time: str, duration: int, client_id: str, service_name: str) -> Optional[int]:
    """
    Marks the specified time slot as booked if available.

    Args:
        date: The date in YYYY-MM-DD format.
        start_time: The start time in HH:MM format.
        duration: The duration in minutes (multiple of 15).
        client_id: An identifier for the client booking the slot (max 32 chars).
        service_name: The name of the service being booked (max 100 chars).

    Returns:
        The unique booking ID if successful.
    Raises:
        ValueError: If the slot is not available or input is invalid.
    """
    logger.debug(f"book_slot entered with: date={date}, start_time={start_time}, duration={duration}, client_id={client_id}, service_name={service_name}")
    
    _validate_duration(duration)
    # Basic input validation
    if len(client_id) > 32:
        logger.warning(f"book_slot: client_id too long: {len(client_id)} chars")
        raise ValueError("client_id cannot exceed 32 characters.")
    if len(service_name) > 100:
        logger.warning(f"book_slot: service_name too long: {len(service_name)} chars")
        raise ValueError("service_name cannot exceed 100 characters.")

    if not is_slot_available(date, start_time, duration):
        logger.warning(f"book_slot: slot not available: {date} {start_time} for {duration} minutes")
        raise ValueError(f"Slot {date} {start_time} for {duration} minutes is not available.")

    try:
        req_start_dt = _combine_datetime(_parse_date(date), _parse_time(start_time))
        req_end_dt = _calculate_end_datetime(req_start_dt, duration)
        end_time_str = _format_time(req_end_dt.time())
        logger.debug(f"book_slot: calculated end_time: {end_time_str}")

        conn = sqlite3.connect(DB_PATH)
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bookings (date, start_time, end_time, duration_minutes, customer_id, service_name)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (date, start_time, end_time_str, duration, client_id, service_name))
            booking_id = cursor.lastrowid # Get the auto-generated ID
            logger.debug(f"book_slot: inserted booking with ID: {booking_id}")
            logger.info(f"book_slot: successfully booked slot {date} {start_time}, Booking ID: {booking_id}")
        return booking_id
    except sqlite3.Error as e:
        logger.error(f"book_slot: database error: {str(e)}", exc_info=True)
        # If it was an integrity error (like UNIQUE constraint if re-enabled), raise ValueError
        if "UNIQUE constraint failed" in str(e):
             raise ValueError(f"Slot {date} {start_time} for {duration} minutes is not available (database constraint).") from e
        raise # Re-raise other database errors

def cancel_booking(booking_id: int) -> bool:
    """
    Deletes the booking with the specified ID, releasing the time slot.

    Args:
        booking_id: The unique ID of the booking to cancel.

    Returns:
        True if the booking was successfully cancelled, False otherwise (e.g., booking ID not found).
    """
    if not isinstance(booking_id, int) or booking_id <= 0:
        logger.warning("Invalid booking_id provided.")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        with conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bookings WHERE booking_id = ?", (booking_id,))
            changes = conn.total_changes
        # total_changes counts changes in the current transaction *before* commit.
        # For DELETE, check cursor.rowcount after execute.
        if cursor.rowcount > 0:
             logger.info(f"Successfully cancelled booking ID: {booking_id}")
             return True
        else:
             logger.warning(f"Booking ID not found: {booking_id}")
             return False
    except sqlite3.Error as e:
        logger.error(f"Database error during cancellation: {e}")
        return False


def slots_available_on_day(date: str, duration: int) -> List[str]:
    """
    Returns a list of available start times (HH:MM) on the given day
    for slots of at least the given duration, aligned to 30-minute intervals.

    Args:
        date: The date in YYYY-MM-DD format.
        duration: The required duration in minutes (multiple of 15).

    Returns:
        A list of available start times as strings (HH:MM), aligned to :00 or :30.
    """
    _validate_duration(duration)
    available_slots = []
    try:
        target_date = _parse_date(date)
        # Define typical working hours (e.g., 9 AM to 5 PM)
        # Adjust as needed
        day_start_time = time(9, 0)
        day_end_time = time(17, 0) # Slots must *start* before 5 PM

        current_check_time = day_start_time
        while current_check_time < day_end_time:
            time_str = _format_time(current_check_time)
            if is_slot_available(date, time_str, duration):
                available_slots.append(time_str)

            # Move to the next 30-minute interval
            current_dt = _combine_datetime(target_date, current_check_time)
            next_dt = current_dt + timedelta(minutes=30)
            current_check_time = next_dt.time()

        return available_slots

    except ValueError as e:
        logger.error(f"Input error in slots_available_on_day: {e}")
        return []
    except sqlite3.Error as e:
        logger.error(f"Database error in slots_available_on_day: {e}")
        return []


def next_available_slot(after_date_time: Tuple[str, str], duration: int) -> Optional[Tuple[str, str]]:
    """
    Returns the next available date and time (YYYY-MM-DD, HH:MM) after the given
    date/time where there is an available slot of at least the specified duration.
    Searches indefinitely into the future.

    Args:
        after_date_time: A tuple containing the date (YYYY-MM-DD) and time (HH:MM)
                         to search after.
        duration: The required duration in minutes (multiple of 15).

    Returns:
        A tuple (date, time) of the next available slot, or None if none found (highly unlikely).
    """
    _validate_duration(duration)
    try:
        start_date_str, start_time_str = after_date_time
        current_dt = _combine_datetime(_parse_date(start_date_str), _parse_time(start_time_str))

        # Start checking from the next 15-minute interval
        minute_offset = 15 - (current_dt.minute % 15)
        if minute_offset == 15: minute_offset = 0 # Already aligned
        current_dt += timedelta(minutes=minute_offset)

        # Limit search range for practical purposes (e.g., 1 year)
        search_limit_dt = current_dt + timedelta(days=365)

        while current_dt < search_limit_dt:
            # Define working hours (e.g., 9 AM to 5 PM) - skip checks outside these hours
            if not (time(9, 0) <= current_dt.time() < time(17, 0)):
                # If before 9 AM, jump to 9 AM
                if current_dt.time() < time(9, 0):
                    current_dt = datetime.combine(current_dt.date(), time(9, 0))
                # If 5 PM or later, jump to 9 AM next day
                else:
                    current_dt = datetime.combine(current_dt.date() + timedelta(days=1), time(9, 0))
                continue # Re-evaluate the loop condition with the new time

            date_str = current_dt.strftime("%Y-%m-%d")
            time_str = _format_time(current_dt.time())

            if is_slot_available(date_str, time_str, duration):
                return (date_str, time_str)

            # Move to the next 15-minute interval
            current_dt += timedelta(minutes=15)

        return None # Should ideally not be reached if search is long enough

    except ValueError as e:
        logger.error(f"Input error in next_available_slot: {e}")
        return None
    except sqlite3.Error as e:
        logger.error(f"Database error in next_available_slot: {e}")
        return None


# --- Initialization ---
# Automatically setup database when module is imported
# Consider if this is desired, or if setup should be explicit
setup_database()
# print(f"slot_calendar module loaded. DB Path: {DB_PATH}")
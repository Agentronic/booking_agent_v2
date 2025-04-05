#!/usr/bin/env python3
"""
Simple Calendar Booking System

This module implements a simple calendar slot booking system with SQLite storage.
It provides functionality to check availability, book slots, and release bookings.
"""

import sqlite3
import datetime
from typing import Tuple, Optional, List


# Global variable to store the database name
# This can be modified by tests to use a test database
DB_NAME = 'calendar.db'


def setup_database():
    """
    Initialize the SQLite database and create the necessary table if it doesn't exist.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create the bookings table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings (
        date TEXT,
        start_time TEXT,
        duration_minutes INTEGER,
        customer_id TEXT,
        service_name TEXT,
        PRIMARY KEY (date, start_time)
    )
    ''')
    
    conn.commit()
    conn.close()


def next_available_slot(after_date_time: Tuple[str, str], duration: int) -> Optional[Tuple[str, str]]:
    """
    Find the next available slot after the given date and time with at least the specified duration.
    
    Args:
        after_date_time: A tuple of (date, time) where date is in yyyy-mm-dd format and time is in hh:mm format
        duration: Duration in minutes (must be a multiple of 15)
    
    Returns:
        A tuple of (date, time) for the next available slot, or None if no slot is found
    """
    # Validate duration is a multiple of 15
    if duration % 15 != 0:
        raise ValueError("Duration must be a multiple of 15 minutes")
    
    date, time = after_date_time
    
    # Convert to datetime for easier manipulation
    current_datetime = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    
    # Get all bookings from the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT date, start_time, duration_minutes FROM bookings ORDER BY date, start_time")
    bookings = cursor.fetchall()
    conn.close()
    
    # If no bookings, return the requested time
    if not bookings:
        return (date, time)
    
    # Convert bookings to datetime objects for easier comparison
    booking_intervals = []
    for booking_date, booking_time, booking_duration in bookings:
        start_dt = datetime.datetime.strptime(f"{booking_date} {booking_time}", "%Y-%m-%d %H:%M")
        end_dt = start_dt + datetime.timedelta(minutes=booking_duration)
        booking_intervals.append((start_dt, end_dt))
    
    # Sort bookings by start time
    booking_intervals.sort(key=lambda x: x[0])
    
    # Check if the requested time is available
    candidate_start = current_datetime
    candidate_end = candidate_start + datetime.timedelta(minutes=duration)
    
    while True:
        # Check if this candidate time overlaps with any booking
        overlaps = False
        for start_dt, end_dt in booking_intervals:
            # If candidate start is before booking end AND candidate end is after booking start
            if candidate_start < end_dt and candidate_end > start_dt:
                overlaps = True
                # Move candidate start to the end of this booking
                candidate_start = end_dt
                candidate_end = candidate_start + datetime.timedelta(minutes=duration)
                break
        
        if not overlaps:
            # Found an available slot
            return (candidate_start.strftime("%Y-%m-%d"), candidate_start.strftime("%H:%M"))
        
        # Safety check to prevent infinite loop (e.g., if we're looking too far in the future)
        if candidate_start > current_datetime + datetime.timedelta(days=365):
            return None


def is_slot_available(date: str, time: str, duration: int) -> bool:
    """
    Check if a slot is available for the specified date, time, and duration.
    
    Args:
        date: Date in yyyy-mm-dd format
        time: Time in hh:mm format
        duration: Duration in minutes (must be a multiple of 15)
    
    Returns:
        True if the slot is available, False otherwise
    """
    # Validate duration is a multiple of 15
    if duration % 15 != 0:
        raise ValueError("Duration must be a multiple of 15 minutes")
    
    # Convert to datetime for easier manipulation
    target_start = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    target_end = target_start + datetime.timedelta(minutes=duration)
    
    # Get all bookings from the database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT date, start_time, duration_minutes FROM bookings")
    bookings = cursor.fetchall()
    conn.close()
    
    # Check if the requested slot overlaps with any existing booking
    for booking_date, booking_time, booking_duration in bookings:
        booking_start = datetime.datetime.strptime(f"{booking_date} {booking_time}", "%Y-%m-%d %H:%M")
        booking_end = booking_start + datetime.timedelta(minutes=booking_duration)
        
        # If target start is before booking end AND target end is after booking start, there's an overlap
        if target_start < booking_end and target_end > booking_start:
            return False
    
    return True


def book_slot(date: str, start_time: str, duration: int, client_id: str, service_name: str) -> bool:
    """
    Book a slot for the specified date, time, duration, client, and service.
    
    Args:
        date: Date in yyyy-mm-dd format
        start_time: Start time in hh:mm format
        duration: Duration in minutes (must be a multiple of 15)
        client_id: Client identifier (up to 32 characters)
        service_name: Service name (up to 100 characters)
    
    Returns:
        True if booking was successful, False otherwise
    """
    # Validate duration is a multiple of 15
    if duration % 15 != 0:
        raise ValueError("Duration must be a multiple of 15 minutes")
    
    # Validate client_id and service_name lengths
    if len(client_id) > 32:
        raise ValueError("Client ID must be 32 characters or less")
    if len(service_name) > 100:
        raise ValueError("Service name must be 100 characters or less")
    
    # Check if the slot is available
    if not is_slot_available(date, start_time, duration):
        return False
    
    # Insert the booking into the database
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO bookings (date, start_time, duration_minutes, customer_id, service_name) VALUES (?, ?, ?, ?, ?)",
            (date, start_time, duration, client_id, service_name)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.Error:
        # Could be a primary key violation or other database error
        return False


def release_slot(date: str, start_time: str) -> bool:
    """
    Release a booking at the specified date and time.
    
    Args:
        date: Date in yyyy-mm-dd format
        start_time: Start time in hh:mm format
    
    Returns:
        True if release was successful, False otherwise
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Check if the booking exists
    cursor.execute(
        "SELECT COUNT(*) FROM bookings WHERE date = ? AND start_time = ?",
        (date, start_time)
    )
    count = cursor.fetchone()[0]
    
    if count == 0:
        conn.close()
        return False
    
    # Delete the booking
    cursor.execute(
        "DELETE FROM bookings WHERE date = ? AND start_time = ?",
        (date, start_time)
    )
    conn.commit()
    conn.close()
    
    return True


# Initialize the database when the module is imported
setup_database()
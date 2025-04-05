#!/usr/bin/env python3
"""
Unit tests for the simple calendar booking system.
"""

import os
import sys
import unittest
import sqlite3
from datetime import datetime, timedelta
from typing import List, Tuple

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Corrected import path if necessary (assuming slot_calendar is directly in app/calendar)
from app.calendar import slot_calendar


class TestCalendarBookingSystem(unittest.TestCase):
    """Test cases for the calendar booking system."""

    TEST_DB = 'test_calendar.db'
    DB_PATH = os.path.join(os.path.dirname(__file__), TEST_DB) # Store test db in test dir

    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests."""
        # Ensure any previous test db is removed
        if os.path.exists(cls.DB_PATH):
            os.remove(cls.DB_PATH)
        # Redirect database path for the module
        slot_calendar.DB_PATH = cls.DB_PATH
        # Setup the database schema using the module's function
        # Note: The actual setup_database stub does nothing yet,
        # so we manually create the schema here for tests to run.
        # Once setup_database is implemented, this manual setup might be redundant
        # depending on its implementation.
        cls._setup_test_database_schema()
        # Call the module's setup (even if it's a stub for now)
        # We call setup_database from the module to ensure it runs if it has logic
        slot_calendar.setup_database(db_path=cls.DB_PATH)


    @classmethod
    def _setup_test_database_schema(cls):
        """Initialize the test database schema."""
        conn = sqlite3.connect(cls.DB_PATH)
        cursor = conn.cursor()

        # Create the bookings table with booking_id and end_time
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL, -- Added end_time column
            duration_minutes INTEGER NOT NULL,
            customer_id TEXT NOT NULL,
            service_name TEXT NOT NULL,
            UNIQUE (date, start_time)
        )
        ''')
        # Consider adding indexes later if performance becomes an issue
        # cursor.execute("CREATE INDEX IF NOT EXISTS idx_booking_datetime ON bookings (date, start_time);")

        conn.commit()
        conn.close()

    def setUp(self):
        """Set up test environment before each test."""
        # Clear the bookings table before each test
        conn = sqlite3.connect(self.DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bookings")
        # Reset autoincrement counter (optional, but good practice for testing)
        # cursor.execute("DELETE FROM sqlite_sequence WHERE name='bookings';")
        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up after each test."""
        pass # Nothing needed here for now

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Remove the test database
        if os.path.exists(cls.DB_PATH):
            os.remove(cls.DB_PATH)

    # --- Test Cases ---

    def test_is_slot_available_empty_calendar(self):
        """Test is_slot_available with an empty calendar."""
        # With an empty calendar, any slot should be available
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "10:00", 30))
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "14:30", 60))
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "23:45", 15))
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "00:00", 15))

    def test_is_slot_available_with_booking(self):
        """Test is_slot_available with existing bookings."""
        # Add a booking
        booking_id = slot_calendar.book_slot("2025-04-01", "10:00", 60, "client123", "Haircut")
        self.assertIsInstance(booking_id, int)

        # Test overlapping slots
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "10:00", 30)) # Same start time
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "10:30", 30)) # Within booking
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "09:45", 30)) # Overlaps start
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "10:45", 30)) # Overlaps end
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "09:30", 60)) # Encompasses start
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "10:00", 90)) # Encompasses end
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "09:30", 90)) # Completely encompasses

        # Test non-overlapping slots
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "09:00", 45)) # Before booking
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "11:00", 30)) # After booking
        self.assertTrue(slot_calendar.is_slot_available("2025-04-02", "10:00", 60)) # Different day

    def test_book_slot_success(self):
        """Test booking an available slot successfully."""
        booking_id = slot_calendar.book_slot("2025-04-01", "10:00", 60, "client123", "Haircut")
        self.assertIsInstance(booking_id, int)

        # Verify the slot is no longer available
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "10:00", 60))

    def test_book_slot_unavailable(self):
        """Test booking a slot that overlaps with an existing one."""
        # Book initial slot
        slot_calendar.book_slot("2025-04-01", "10:00", 60, "client123", "Haircut")

        # Try to book overlapping slot - should raise ValueError
        with self.assertRaises(ValueError):
            slot_calendar.book_slot("2025-04-01", "10:30", 30, "client456", "Manicure")
        with self.assertRaises(ValueError):
            slot_calendar.book_slot("2025-04-01", "09:45", 30, "client456", "Manicure") # Overlaps start


    def test_cancel_booking_success(self):
        """Test cancelling an existing booking."""
        # Book a slot first
        booking_id = slot_calendar.book_slot("2025-04-01", "14:00", 30, "client789", "Consult")
        self.assertIsInstance(booking_id, int)
        # Verify it's booked
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "14:00", 30))

        # Cancel the booking
        result = slot_calendar.cancel_booking(booking_id)
        self.assertTrue(result)

        # Verify the slot is now available
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "14:00", 30))

    def test_cancel_booking_non_existent(self):
        """Test cancelling a booking ID that does not exist."""
        # Try to cancel a booking ID that hasn't been created
        result = slot_calendar.cancel_booking(999)
        # Should return False as no booking was cancelled
        self.assertFalse(result) # Corrected assertion

    def test_next_available_slot_empty_calendar(self):
        """Test finding the next available slot in an empty calendar."""
        # Expect the next 15-min interval within working hours (9-5)
        result = slot_calendar.next_available_slot(("2025-04-01", "10:05"), 30)
        self.assertEqual(result, ("2025-04-01", "10:15"))
        result = slot_calendar.next_available_slot(("2025-04-01", "08:00"), 60) # Before work hours
        self.assertEqual(result, ("2025-04-01", "09:00"))
        result = slot_calendar.next_available_slot(("2025-04-01", "17:00"), 30) # After work hours
        self.assertEqual(result, ("2025-04-02", "09:00")) # Should be next day

    def test_next_available_slot_with_bookings(self):
        """Test finding the next available slot with existing bookings."""
        # Add bookings
        slot_calendar.book_slot("2025-04-01", "10:00", 60, "client123", "Haircut") # 10:00 - 11:00
        slot_calendar.book_slot("2025-04-01", "12:00", 30, "client456", "Manicure") # 12:00 - 12:30

        # Test finding slots
        result = slot_calendar.next_available_slot(("2025-04-01", "09:00"), 30) # Before first booking
        self.assertEqual(result, ("2025-04-01", "09:00"))
        result = slot_calendar.next_available_slot(("2025-04-01", "10:00"), 30) # Starts during first booking
        self.assertEqual(result, ("2025-04-01", "11:00")) # Should be after first booking
        result = slot_calendar.next_available_slot(("2025-04-01", "10:45"), 30) # Starts during first booking
        self.assertEqual(result, ("2025-04-01", "11:00")) # Should be after first booking
        result = slot_calendar.next_available_slot(("2025-04-01", "11:45"), 60) # Needs 60 mins, overlaps second booking
        self.assertEqual(result, ("2025-04-01", "12:30")) # Should be after second booking

    def test_slots_available_on_day_empty(self):
        """Test slots_available_on_day with an empty calendar."""
        # Expect slots every 30 mins from 9:00 to 16:30 (inclusive)
        expected_slots = [f"{h:02d}:{m:02d}" for h in range(9, 17) for m in (0, 30)]
        result = slot_calendar.slots_available_on_day("2025-04-01", 30)
        self.assertListEqual(result, expected_slots)

    def test_slots_available_on_day_with_bookings(self):
        """Test slots_available_on_day with existing bookings."""
        # Add bookings
        slot_calendar.book_slot("2025-04-01", "10:00", 60, "client123", "Haircut") # 10:00 - 11:00
        slot_calendar.book_slot("2025-04-01", "14:00", 30, "client456", "Consult") # 14:00 - 14:30

        # Expect slots every 30 mins, skipping booked times
        all_slots = [f"{h:02d}:{m:02d}" for h in range(9, 17) for m in (0, 30)]
        # Remove booked slots: 10:00, 10:30 (covered by 10:00-11:00), 14:00
        expected_slots = [s for s in all_slots if s not in ["10:00", "10:30", "14:00"]]
        result = slot_calendar.slots_available_on_day("2025-04-01", 30)
        self.assertListEqual(result, expected_slots)

    def test_duration_validation(self):
        """Test that functions raise ValueError for invalid durations."""
        invalid_durations = [0, -15, 10, 17, 31]
        valid_date = "2025-04-01"
        valid_time = "10:00"

        for duration in invalid_durations:
            with self.assertRaises(ValueError, msg=f"Failed for duration {duration}"):
                slot_calendar.is_slot_available(valid_date, valid_time, duration)
            with self.assertRaises(ValueError, msg=f"Failed for duration {duration}"):
                slot_calendar.book_slot(valid_date, valid_time, duration, "test", "test")
            with self.assertRaises(ValueError, msg=f"Failed for duration {duration}"):
                slot_calendar.slots_available_on_day(valid_date, duration)
            with self.assertRaises(ValueError, msg=f"Failed for duration {duration}"):
                slot_calendar.next_available_slot((valid_date, valid_time), duration)

        # Test with valid durations - should not raise error
        valid_durations = [15, 30, 45, 60, 75, 90, 105, 120]
        for duration in valid_durations:
            try:
                slot_calendar.is_slot_available(valid_date, valid_time, duration)
                # book_slot will fail if slot unavailable, so only test others here
                slot_calendar.slots_available_on_day(valid_date, duration)
                slot_calendar.next_available_slot((valid_date, valid_time), duration)
            except ValueError:
                self.fail(f"Function raised ValueError unexpectedly for valid duration {duration}")


if __name__ == "__main__":
    unittest.main()

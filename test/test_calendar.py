#!/usr/bin/env python3
"""
Unit tests for the simple calendar booking system.
"""

import os
import unittest
import sqlite3
from datetime import datetime, timedelta
import slot_calendar


class TestCalendarBookingSystem(unittest.TestCase):
    """Test cases for the calendar booking system."""
    
    TEST_DB = 'test_calendar.db'
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests."""
        # Redirect database to test database
        slot_calendar.DB_NAME = cls.TEST_DB
        slot_calendar.setup_database()
        
    @classmethod
    def _setup_test_database(cls):
        """Initialize the test database."""
        conn = sqlite3.connect(cls.TEST_DB)
        cursor = conn.cursor()
        
        # Create the bookings table
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
    
    def setUp(self):
        """Set up test environment before each test."""
        # Clear the test database before each test
        if os.path.exists(self.TEST_DB):
            conn = sqlite3.connect(self.TEST_DB)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bookings")
            conn.commit()
            conn.close()
        else:
            self._setup_test_database()
    
    def tearDown(self):
        """Clean up after each test."""
        pass
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Remove the test database
        if os.path.exists(cls.TEST_DB):
            os.remove(cls.TEST_DB)
    
    def test_is_slot_available_empty_calendar(self):
        """Test is_slot_available with an empty calendar."""
        # With an empty calendar, any slot should be available
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "10:00", 30))
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "14:30", 60))
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "23:45", 15))  # End of day
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "00:00", 15))  # Start of day
        self.assertTrue(slot_calendar.is_slot_available("2025-12-31", "23:45", 15))  # End of year
        self.assertTrue(slot_calendar.is_slot_available("2025-01-01", "00:00", 15))  # Start of year
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "10:00", 1440))  # Full day (24 hours)
    
    def test_is_slot_available_with_booking(self):
        """Test is_slot_available with existing bookings."""
        # Add a booking
        slot_calendar.book_slot("2025-04-01", "10:00", 60, "client123", "Haircut")
        
        # Test overlapping slots
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "10:00", 30))  # Same start time
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "10:30", 30))  # Within booking
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "09:45", 30))  # Overlaps start
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "10:45", 30))  # Overlaps end
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "09:30", 60))  # Encompasses start
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "10:00", 90))  # Encompasses end
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "09:30", 90))  # Completely encompasses booking
        
        # Test non-overlapping slots
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "09:00", 45))  # Before booking
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "11:00", 30))  # After booking
        self.assertTrue(slot_calendar.is_slot_available("2025-04-02", "10:00", 60))  # Different day
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "09:00", 15))  # Just before booking
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "11:00", 15))  # Just after booking
    
    def test_book_slot(self):
        """Test booking a slot."""
        # Book a slot
        result = slot_calendar.book_slot("2025-04-01", "10:00", 60, "client123", "Haircut")
        self.assertTrue(result)
        
        # Verify the slot is no longer available
        self.assertFalse(slot_calendar.is_slot_available("2025-04-01", "10:00", 60))
        
        # Try to book the same slot again
        result = slot_calendar.book_slot("2025-04-01", "10:00", 30, "client456", "Manicure")
        self.assertFalse(result)
        
        # Book a different slot
        result = slot_calendar.book_slot("2025-04-01", "11:30", 45, "client789", "Massage")
        self.assertTrue(result)
    
    def test_release_slot(self):
        """Test releasing a booked slot."""
        # Book a slot
        slot_calendar.book_slot("2025-04-01", "10:00", 60, "client123", "Haircut")
        
        # Release the slot
        result = slot_calendar.release_slot("2025-04-01", "10:00")
        self.assertTrue(result)
        
        # Verify the slot is now available
        self.assertTrue(slot_calendar.is_slot_available("2025-04-01", "10:00", 60))
        
        # Try to release a slot that isn't booked
        result = slot_calendar.release_slot("2025-04-01", "14:00")
        self.assertFalse(result)
    
    def test_next_available_slot_empty_calendar(self):
        """Test finding the next available slot in an empty calendar."""
        # With an empty calendar, the next available slot should be the requested time
        result = slot_calendar.next_available_slot(("2025-04-01", "10:00"), 30)
        self.assertEqual(result, ("2025-04-01", "10:00"))
        
        # Test with different durations
        result = slot_calendar.next_available_slot(("2025-04-01", "10:00"), 15)
        self.assertEqual(result, ("2025-04-01", "10:00"))
        
        result = slot_calendar.next_available_slot(("2025-04-01", "10:00"), 60)
        self.assertEqual(result, ("2025-04-01", "10:00"))
        
        # Test with different times
        result = slot_calendar.next_available_slot(("2025-04-01", "00:00"), 30)  # Start of day
        self.assertEqual(result, ("2025-04-01", "00:00"))
        
        result = slot_calendar.next_available_slot(("2025-04-01", "23:30"), 30)  # End of day
        self.assertEqual(result, ("2025-04-01", "23:30"))
    
    def test_next_available_slot_with_bookings(self):
        """Test finding the next available slot with existing bookings."""
        # Add some bookings
        slot_calendar.book_slot("2025-04-01", "10:00", 60, "client123", "Haircut")
        slot_calendar.book_slot("2025-04-01", "12:00", 30, "client456", "Manicure")
        
        # Test finding a slot between bookings
        result = slot_calendar.next_available_slot(("2025-04-01", "09:00"), 30)
        self.assertEqual(result, ("2025-04-01", "09:00"))
        
        # Test finding a slot after the first booking
        result = slot_calendar.next_available_slot(("2025-04-01", "10:00"), 30)
        self.assertEqual(result, ("2025-04-01", "11:00"))
        
        # Test finding a slot that spans multiple bookings
        result = slot_calendar.next_available_slot(("2025-04-01", "10:00"), 120)
        self.assertEqual(result, ("2025-04-01", "12:30"))
        
        # Test finding a slot with exact fit between bookings
        result = slot_calendar.next_available_slot(("2025-04-01", "10:30"), 60)
        self.assertEqual(result, ("2025-04-01", "11:00"))
        
        # Test finding a slot with a time that's already in the middle of a booking
        result = slot_calendar.next_available_slot(("2025-04-01", "10:30"), 30)
        self.assertEqual(result, ("2025-04-01", "11:00"))
    
    def test_duration_validation(self):
        """Test that durations must be multiples of 15 minutes."""
        # Try to book with invalid durations
        with self.assertRaises(ValueError):
            slot_calendar.book_slot("2025-04-01", "10:00", 17, "client123", "Haircut")
        
        with self.assertRaises(ValueError):
            slot_calendar.is_slot_available("2025-04-01", "10:00", 22)
        
        with self.assertRaises(ValueError):
            slot_calendar.next_available_slot(("2025-04-01", "10:00"), 7)
            
        # Test with valid durations
        for duration in [15, 30, 45, 60, 75, 90, 105, 120]:
            try:
                slot_calendar.is_slot_available("2025-04-01", "10:00", duration)
            except ValueError:
                self.fail(f"is_slot_available raised ValueError unexpectedly for duration {duration}")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
Unit tests for the calendar tools for AG2.
"""

import os
import unittest
import json
import sqlite3
from datetime import datetime, timedelta
import slot_calendar
import slot_calendar_tools as calendar_tools


class TestCalendarTools(unittest.TestCase):
    """Test cases for the calendar tools."""
    
    TEST_DB = 'test_calendar_tools.db'
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests."""
        # Redirect database to test database
        slot_calendar.DB_NAME = cls.TEST_DB
        slot_calendar.setup_database()
        
    def setUp(self):
        """Set up test environment before each test."""
        # Clear all bookings before each test
        conn = sqlite3.connect(self.TEST_DB)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bookings")
        conn.commit()
        conn.close()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        if os.path.exists(cls.TEST_DB):
            os.remove(cls.TEST_DB)
    
    def test_next_available_slot_tool(self):
        """Test the next_available_slot tool."""
        # Test with empty calendar
        args = {
            'after_date': '2025-04-01',
            'after_time': '10:00',
            'duration': 30
        }
        
        result = calendar_tools.next_available_slot_tool(args)
        self.assertTrue(result['success'])
        self.assertEqual(result['date'], '2025-04-01')
        self.assertEqual(result['time'], '10:00')
        
        # Add some bookings
        slot_calendar.book_slot('2025-04-01', '10:00', 60, 'client123', 'Haircut')
        
        # Test finding a slot after the booking
        result = calendar_tools.next_available_slot_tool(args)
        self.assertTrue(result['success'])
        self.assertEqual(result['date'], '2025-04-01')
        self.assertEqual(result['time'], '11:00')
        
        # Test with invalid duration
        args['duration'] = 17
        result = calendar_tools.next_available_slot_tool(args)
        self.assertFalse(result['success'])
        self.assertIn('must be a multiple of 15', result['error'])
    
    def test_is_slot_available_tool(self):
        """Test the is_slot_available tool."""
        # Test with empty calendar
        args = {
            'date': '2025-04-01',
            'time': '10:00',
            'duration': 30
        }
        
        result = calendar_tools.is_slot_available_tool(args)
        self.assertTrue(result['success'])
        self.assertTrue(result['available'])
        
        # Add a booking
        slot_calendar.book_slot('2025-04-01', '10:00', 60, 'client123', 'Haircut')
        
        # Test with unavailable slot
        result = calendar_tools.is_slot_available_tool(args)
        self.assertTrue(result['success'])
        self.assertFalse(result['available'])
        
        # Test with available slot
        args['time'] = '11:30'
        result = calendar_tools.is_slot_available_tool(args)
        self.assertTrue(result['success'])
        self.assertTrue(result['available'])
        
        # Test with invalid duration
        args['duration'] = 17
        result = calendar_tools.is_slot_available_tool(args)
        self.assertFalse(result['success'])
        self.assertIn('must be a multiple of 15', result['error'])
    
    def test_book_slot_tool(self):
        """Test the book_slot tool."""
        # Test booking an available slot
        args = {
            'date': '2025-04-01',
            'time': '10:00',
            'duration': 30,
            'client_id': 'client123',
            'service_name': 'Haircut'
        }
        
        result = calendar_tools.book_slot_tool(args)
        self.assertTrue(result['success'])
        self.assertTrue(result['booked'])
        
        # Test booking the same slot again
        result = calendar_tools.book_slot_tool(args)
        self.assertTrue(result['success'])
        self.assertFalse(result['booked'])
        
        # Test with invalid duration
        args['time'] = '11:00'
        args['duration'] = 17
        result = calendar_tools.book_slot_tool(args)
        self.assertFalse(result['success'])
        self.assertIn('must be a multiple of 15', result['error'])
        
        # Test with missing parameters
        incomplete_args = {
            'date': '2025-04-01',
            'time': '11:00'
            # Missing other required parameters
        }
        result = calendar_tools.book_slot_tool(incomplete_args)
        self.assertFalse(result['success'])
        self.assertIn('Missing required parameters', result['error'])
    
    def test_release_slot_tool(self):
        """Test the release_slot tool."""
        # Add a booking
        slot_calendar.book_slot('2025-04-01', '10:00', 60, 'client123', 'Haircut')
        
        # Test releasing the booking
        args = {
            'date': '2025-04-01',
            'time': '10:00'
        }
        
        result = calendar_tools.release_slot_tool(args)
        self.assertTrue(result['success'])
        self.assertTrue(result['released'])
        
        # Test releasing a non-existent booking
        result = calendar_tools.release_slot_tool(args)
        self.assertTrue(result['success'])
        self.assertFalse(result['released'])
        
        # Test with missing parameters
        incomplete_args = {
            'date': '2025-04-01'
            # Missing time parameter
        }
        result = calendar_tools.release_slot_tool(incomplete_args)
        self.assertFalse(result['success'])
        self.assertIn('Missing required parameters', result['error'])
    
    def test_execute_calendar_tool(self):
        """Test the execute_calendar_tool function."""
        # Test next_available_slot
        args = {
            'after_date': '2025-04-01',
            'after_time': '10:00',
            'duration': 30
        }
        
        result_json = calendar_tools.execute_calendar_tool('next_available_slot', json.dumps(args))
        result = json.loads(result_json)
        self.assertTrue(result['success'])
        self.assertEqual(result['date'], '2025-04-01')
        self.assertEqual(result['time'], '10:00')
        
        # Test with unknown tool
        result_json = calendar_tools.execute_calendar_tool('unknown_tool', json.dumps(args))
        result = json.loads(result_json)
        self.assertFalse(result['success'])
        self.assertIn('Unknown tool', result['error'])
        
        # Test with invalid JSON
        result_json = calendar_tools.execute_calendar_tool('next_available_slot', '{invalid json}')
        result = json.loads(result_json)
        self.assertFalse(result['success'])
        self.assertIn('Invalid JSON', result['error'])


if __name__ == '__main__':
    unittest.main()

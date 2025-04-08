#!/usr/bin/env python3
"""
Database Dump Utility for Calendar Database

This script dumps the entire contents of the bookings table in the calendar database
in a fixed-width column format, similar to the output of 'SELECT * FROM bookings'.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Add the project root to the path
bin_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(bin_dir)
sys.path.append(project_root)

# Import the database name from the slot_calendar module
from app.calendar import slot_calendar


def dump_calendar_db(db_path=None):
    """
    Dump the contents of the bookings table in the calendar database.
    
    Args:
        db_path: Optional path to the database file. If None, uses the default from slot_calendar.
    """
    # Use the default database path if none is provided
    if db_path is None:
        db_path = slot_calendar.DB_PATH
    
    # Check if the database file exists
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        print("The database may not have been created yet or is in a different location.")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(bookings)")
        columns = cursor.fetchall()
        
        if not columns:
            print("Table 'bookings' not found in the database.")
            return
        
        # Extract column names
        column_names = [col[1] for col in columns]
        
        # Determine column widths (minimum 15 characters, or length of column name + 2)
        col_widths = [max(15, len(name) + 2) for name in column_names]
        
        # Print header
        header = "".join(name.ljust(width) for name, width in zip(column_names, col_widths))
        print("\n" + "=" * len(header))
        print("CALENDAR DATABASE DUMP")
        print(f"Database: {db_path}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * len(header))
        print(header)
        print("-" * len(header))
        
        # Query all rows
        cursor.execute("SELECT * FROM bookings ORDER BY date, start_time")
        rows = cursor.fetchall()
        
        if not rows:
            print("No bookings found in the database.")
        else:
            # Print each row
            for row in rows:
                formatted_row = "".join(str(cell).ljust(width) for cell, width in zip(row, col_widths))
                print(formatted_row)
        
        print("-" * len(header))
        print(f"Total records: {len(rows)}")
        print("=" * len(header) + "\n")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()


def main():
    """Main function to handle command line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Dump the contents of the calendar database.')
    parser.add_argument('--db', help='Path to the database file (optional)')
    args = parser.parse_args()
    
    dump_calendar_db(args.db)


if __name__ == "__main__":
    main()

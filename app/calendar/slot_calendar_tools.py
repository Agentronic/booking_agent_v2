#!/usr/bin/env python3
"""
Calendar Tools for AG2 - Exposes the calendar booking system methods as tools that AG2 can use.
"""

import json
from typing import Dict, Any, Optional, Tuple
from app.calendar import slot_calendar


def next_available_slot_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool for finding the next available time slot.
    
    Args:
        args: Dictionary containing:
            - after_date: Date in yyyy-mm-dd format
            - after_time: Time in hh:mm format
            - duration: Duration in minutes (must be multiple of 15)
    
    Returns:
        Dictionary with result information:
            - success: Boolean indicating success
            - date: Available date (if success)
            - time: Available time (if success)
            - error: Error message (if not success)
    """
    try:
        # Extract and validate arguments
        after_date = args.get('after_date')
        after_time = args.get('after_time')
        duration = args.get('duration')
        
        if not all([after_date, after_time, duration]):
            return {
                'success': False,
                'error': 'Missing required parameters: after_date, after_time, and duration are required'
            }
        
        try:
            duration = int(duration)
        except ValueError:
            return {
                'success': False,
                'error': 'Duration must be an integer'
            }
        
        # Call the calendar function
        result = slot_calendar.next_available_slot((after_date, after_time), duration)
        
        if result:
            return {
                'success': True,
                'date': result[0],
                'time': result[1]
            }
        else:
            return {
                'success': False,
                'error': 'No available slot found within the next year'
            }
    except ValueError as e:
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def is_slot_available_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool for checking if a specific slot is available.
    
    Args:
        args: Dictionary containing:
            - date: Date in yyyy-mm-dd format
            - time: Time in hh:mm format
            - duration: Duration in minutes (must be multiple of 15)
    
    Returns:
        Dictionary with result information:
            - success: Boolean indicating success of the operation
            - available: Boolean indicating if slot is available (if success)
            - error: Error message (if not success)
    """
    try:
        # Extract and validate arguments
        date = args.get('date')
        time = args.get('time')
        duration = args.get('duration')
        
        if not all([date, time, duration]):
            return {
                'success': False,
                'error': 'Missing required parameters: date, time, and duration are required'
            }
        
        try:
            duration = int(duration)
        except ValueError:
            return {
                'success': False,
                'error': 'Duration must be an integer'
            }
        
        # Call the calendar function
        available = slot_calendar.is_slot_available(date, time, duration)
        
        return {
            'success': True,
            'available': available
        }
    except ValueError as e:
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def book_slot_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool for booking a slot.
    
    Args:
        args: Dictionary containing:
            - date: Date in yyyy-mm-dd format
            - time: Time in hh:mm format
            - duration: Duration in minutes (must be multiple of 15)
            - client_id: Client identifier (max 32 chars)
            - service_name: Service name (max 100 chars)
    
    Returns:
        Dictionary with result information:
            - success: Boolean indicating success of the operation
            - booked: Boolean indicating if booking was successful (if success)
            - error: Error message (if not success)
    """
    try:
        # Extract and validate arguments
        date = args.get('date')
        time = args.get('time')
        duration = args.get('duration')
        client_id = args.get('client_id')
        service_name = args.get('service_name')
        
        if not all([date, time, duration, client_id, service_name]):
            return {
                'success': False,
                'error': 'Missing required parameters: date, time, duration, client_id, and service_name are required'
            }
        
        try:
            duration = int(duration)
        except ValueError:
            return {
                'success': False,
                'error': 'Duration must be an integer'
            }
        
        # Call the calendar function
        booked = slot_calendar.book_slot(date, time, duration, client_id, service_name)
        
        return {
            'success': True,
            'booked': booked
        }
    except ValueError as e:
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def release_slot_tool(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool for releasing a booked slot.
    
    Args:
        args: Dictionary containing:
            - date: Date in yyyy-mm-dd format
            - time: Time in hh:mm format
    
    Returns:
        Dictionary with result information:
            - success: Boolean indicating success of the operation
            - released: Boolean indicating if release was successful (if success)
            - error: Error message (if not success)
    """
    try:
        # Extract and validate arguments
        date = args.get('date')
        time = args.get('time')
        
        if not all([date, time]):
            return {
                'success': False,
                'error': 'Missing required parameters: date and time are required'
            }
        
        # Call the calendar function
        released = slot_calendar.release_slot(date, time)
        
        return {
            'success': True,
            'released': released
        }
    except ValueError as e:
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


# Dictionary mapping tool names to their functions
CALENDAR_TOOLS = {
    'next_available_slot': next_available_slot_tool,
    'is_slot_available': is_slot_available_tool,
    'book_slot': book_slot_tool,
    'release_slot': release_slot_tool
}


def execute_calendar_tool(tool_name: str, args_json: str) -> str:
    """
    Execute a calendar tool with the given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        args_json: JSON string containing tool arguments
    
    Returns:
        JSON string with the tool's response
    """
    try:
        # Parse arguments
        args = json.loads(args_json)
        
        # Get the tool function
        tool_func = CALENDAR_TOOLS.get(tool_name)
        
        if not tool_func:
            return json.dumps({
                'success': False,
                'error': f'Unknown tool: {tool_name}'
            })
        
        # Execute the tool
        result = tool_func(args)
        
        # Return result as JSON
        return json.dumps(result)
    except json.JSONDecodeError:
        return json.dumps({
            'success': False,
            'error': 'Invalid JSON arguments'
        })
    except Exception as e:
        return json.dumps({
            'success': False,
            'error': f'Tool execution error: {str(e)}'
        })


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python calendar_tools.py <tool_name> '<json_args>'")
        sys.exit(1)
    
    tool_name = sys.argv[1]
    args_json = sys.argv[2]
    
    result = execute_calendar_tool(tool_name, args_json)
    print(result)
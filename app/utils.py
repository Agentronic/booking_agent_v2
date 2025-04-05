from datetime import datetime, timedelta

def parse_datetime(date_str, time_str=None):
    """Parse date and time strings into a datetime object."""
    if time_str:
        dt_str = f"{date_str} {time_str}"
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    return datetime.strptime(date_str, "%Y-%m-%d")

def format_datetime(dt):
    """Format a datetime object into a readable string."""
    return dt.strftime("%Y-%m-%d %H:%M")

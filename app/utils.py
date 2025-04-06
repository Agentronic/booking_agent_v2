from datetime import datetime, timedelta
from pathlib import Path

def parse_datetime(date_str, time_str=None):
    """Parse date and time strings into a datetime object."""
    if time_str:
        dt_str = f"{date_str} {time_str}"
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    return datetime.strptime(date_str, "%Y-%m-%d")

def format_datetime(dt):
    """Format a datetime object into a readable string."""
    return dt.strftime("%Y-%m-%d %H:%M")

def app_path(*paths):
    """Return the project root directory or join it with additional paths."""
    project_root = Path(__file__).resolve().parents[1]
    return project_root.joinpath(*paths)

# Common directory paths
LOGS_DIR = app_path('logs') 
DATA_DIR = app_path('data')

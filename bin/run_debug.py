#!/usr/bin/env python
import os
import sys
import logging
import signal
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    logger.info("Received signal to exit")
    sys.exit(0)

def main():
    """Debug wrapper to run the app with detailed logging"""
    try:
        # Register signal handler for clean exit
        signal.signal(signal.SIGINT, signal_handler)
        
        logger.info("Starting booking agent application in debug mode")
        
        # Set environment variables
        os.environ["GRADIO_SERVER_PORT"] = "7862"  # Use a different port
        os.environ["PYTHONUNBUFFERED"] = "1"       # Ensure output is not buffered
        
        # Add the parent directory to the path so we can import modules
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Import the app module
        logger.info("Importing app module...")
        import app
        logger.info("Successfully imported app module")
        
        # Run the app with a specific port
        port = int(os.environ.get("GRADIO_SERVER_PORT", 7862))
        logger.info(f"Launching app on port {port}")
        
        # Launch with debug=True to get more information
        app.demo.launch(server_port=port, share=False, debug=True)
        
    except Exception as e:
        logger.error(f"Error running app: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

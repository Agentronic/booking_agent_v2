#!/usr/bin/env python
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test script to check imports"""
    try:
        logger.info("Testing imports for booking agent application")
        
        # Add the parent directory to the path so we can import modules
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.append(project_root)
        
        # Import the necessary modules
        logger.info("Importing gradio")
        import gradio as gr
        logger.info("Gradio imported successfully")
        
        logger.info("Importing autogen")
        import autogen
        logger.info("Autogen imported successfully")
        
        logger.info("Importing slot_calendar_tools")
        import slot_calendar_tools
        logger.info("slot_calendar_tools imported successfully")
        
        logger.info("Importing slot_calendar")
        import slot_calendar
        logger.info("slot_calendar imported successfully")
        
        # Test app module imports
        logger.info("Importing app modules")
        from app.agent import handle_booking_request
        logger.info("app.agent imported successfully")
        
        logger.info("All imports successful!")
        
    except Exception as e:
        logger.error(f"Error importing modules: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

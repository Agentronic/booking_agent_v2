import gradio as gr
import os
import logging
import sys
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Print debug information
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

from app.agent import conversational_round_trip
logger.info("Successfully imported AG2 multi-agent conversation handler")

def chat_interface(message, history):
    # Generate a user ID from the conversation history to maintain context
    user_id = str(hash(str(history))) if history else "default_user"
    
    # Log the message receipt
    logger.info(f"Chat message received: {message}")
    print(f"Processing message: {message}")
    
    try:
        # Get response from centralized conversation handler
        response = conversational_round_trip(message, user_id)
        logger.info("Successfully processed message via centralized service")
        print(f"Response: {response}")
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")
        response = f"I'm sorry, there was an error processing your request: {str(e)}"
    
    # Add messages to history
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response})
    
    return history, ""  # Return empty string to clear the input box

with gr.Blocks() as demo:
    gr.Markdown("# Booking Agent")
    gr.Markdown("""
    Welcome to the Booking Agent! I can help you book appointments for the following services:
    - Haircut (30 min)
    - Massage (60 min)
    - Consultation (45 min)
    
    Try asking about available slots or book a specific time.
    Example: "I'd like to book a haircut tomorrow at 2pm" or "What slots do you have available for a massage?"
    """)
    
    chatbot = gr.Chatbot(height=500, type="messages")
    msg = gr.Textbox(placeholder="Type your message here...", scale=4)
    
    with gr.Row():
        clear = gr.Button("Clear Chat")
        example1 = gr.Button("Check Available Slots")
        example2 = gr.Button("Book a Haircut")
        example3 = gr.Button("Book a Massage")
    
    # Handle message submission
    msg.submit(chat_interface, [msg, chatbot], [chatbot, msg])
    
    # Handle button clicks
    clear.click(lambda: None, None, chatbot, queue=False)
    example1.click(lambda: "What time slots do you have available this week?", None, msg, queue=False)
    example2.click(lambda: "I'd like to book a haircut tomorrow at 10am.", None, msg, queue=False)
    example3.click(lambda: "Can I schedule a massage for Friday afternoon?", None, msg, queue=False)
    
    # Auto-trigger example buttons to submit the message
    for btn in [example1, example2, example3]:
        btn.click(chat_interface, [msg, chatbot], [chatbot, msg], queue=True)

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.environ.get("GRADIO_SERVER_PORT", 7862))
    print(f"Starting Gradio server on port {port}")
    
    try:
        # Launch with minimal settings to ensure it works
        demo.launch(server_port=port, share=False, show_error=True)
    except Exception as e:
        logger.error(f"Failed to launch Gradio server: {e}", exc_info=True)
        print(f"Error launching Gradio: {str(e)}")
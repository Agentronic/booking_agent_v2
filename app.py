import gradio as gr
import os
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Conditionally import the appropriate conversation handler
# Use AG2 by default, fall back to basic_conversation if specified
use_basic = os.environ.get('USE_BASIC_CONVERSATION', 'false').lower() == 'true'

if use_basic:
    from basic_conversation import handle_conversation
    logger.info("Using basic conversation handler")
else:
    try:
        from agent import handle_conversation
        logger.info("Using AG2 multi-agent conversation handler")
    except Exception as e:
        from basic_conversation import handle_conversation
        logger.error(f"Failed to load AG2 agent: {e}. Using basic conversation handler as fallback", exc_info=True)

def chat_interface(message, history):
    # Generate a user ID from the conversation history to maintain context
    # In a real app, this would be a session ID or user ID
    user_id = str(hash(str(history))) if history else "default_user"
    
    # Use the appropriate conversation handler
    logger.info(f"Chat message received: {message}")
    try:
        response = handle_conversation(message, user_id)
        logger.info("Successfully processed message")
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        response = "I'm sorry, there was an error processing your request. Please try again."
    
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response})
    return history, ""  # Return empty string to clear the input box

with gr.Blocks() as demo:
    gr.Markdown("# Booking Agent")
    gr.Markdown("Welcome to the Booking Agent. Ask to book an appointment!")
    
    chatbot = gr.Chatbot(height=400, type="messages")
    msg = gr.Textbox(placeholder="Type your message here...")
    clear = gr.Button("Clear")
    
    msg.submit(chat_interface, [msg, chatbot], [chatbot, msg])
    clear.click(lambda: None, None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch()
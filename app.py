import gradio as gr
from basic_conversation import handle_conversation

def chat_interface(message, history):
    # Use the basic conversation handler
    response = handle_conversation(message)
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
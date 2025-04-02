# Booking Agent

A generic booking agent built with AG2 (AutoGen) that mediates between service providers and clients looking to book appointments. This application demonstrates the use of multi-agent conversations to handle appointment scheduling.

## Features

- Chat interface for user interaction using Gradio
- Multi-agent system with three specialized agents:
  - User Proxy Agent: Represents the human user in the conversation
  - Booking Agent: Coordinates the booking process
  - Service Provider Agent: Provides information about services and availability
- Automated negotiation of suitable time slots
- Calendar integration (planned for future phases)

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create your environment file:
   ```
   cp dot_env.example .env
   ```
   Edit the .env file to add your OpenAI API key.

3. Run the application:
   ```
   python app.py
   ```
   
   To use the basic conversation handler instead of the AG2 multi-agent system:
   ```
   USE_BASIC_CONVERSATION=true python app.py
   ```

4. Open the web interface in your browser (the URL will be displayed in the terminal)

## Project Structure

- `app.py`: Main application file with Gradio web interface
- `agent.py`: AG2 multi-agent implementation with GroupChat
- `PhasedImplementation.md`: Phased development plan
- `architecture.md`: System architecture documentation

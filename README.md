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

2. Run the application:
   ```
   python app.py
   ```

3. Open the web interface in your browser (the URL will be displayed in the terminal)

## Project Structure

- `app.py`: Main application file with Gradio web interface
- `agent.py`: AG2 multi-agent implementation with GroupChat
- `PhasedImplementation.md`: Phased development plan
- `architecture.md`: System architecture documentation

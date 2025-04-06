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
   python bin/web_app.py
   ```
   
   To run the CLI version:
   ```
   python bin/cli_app.py
   ```

4. Open the web interface in your browser (the URL will be displayed in the terminal)

## Project Structure

- `app.py`: Main application file with Gradio web interface
- `app/`: Application source code
  - `agent.py`: AG2 multi-agent implementation with GroupChat
  - `slot_calendar.py`: Calendar functionality
  - `slot_calendar_tools.py`: Tools for calendar operations
- `bin/`: Executable scripts
  - `web_app.py`: Script to run the web interface
  - `cli_app.py`: Command-line interface
  - `run_debug.py`: Debug version of the application
  - `unit-test.py`: Script to run all unit tests
- `test/`: Unit tests
- `doc/`: Documentation
  - `PhasedImplementation.md`: Phased development plan
  - `architecture.md`: System architecture documentation

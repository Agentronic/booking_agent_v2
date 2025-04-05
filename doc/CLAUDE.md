# Claude Code Context for Booking Agent

## Project Overview
- A booking agent system built with AutoGen (AG2) framework
- Implements three specialized agents:
  - User Proxy Agent: Represents the human user
  - Booking Agent: Coordinates the booking process
  - Service Provider Agent: Provides service info and availability
- Uses Gradio for the web interface

## Key Files
- `app.py`: Main application with Gradio interface
- `app/`: Application source code
  - `agent.py`: AG2 multi-agent implementation
  - `simple_agent.py`: Simplified agent implementation
  - `slot_calendar.py`: Calendar functionality
  - `slot_calendar_tools.py`: Tools for calendar operations
- `bin/`: Executable scripts
  - `run_app.py`: Script to run the web interface
  - `cli_app.py`: Command-line interface
  - `run_debug.py`: Debug version of the application
  - `unit-test.py`: Script to run all unit tests
- `test/`: Unit tests

## Development Workflow
1. Run linting: `pylint app/*.py bin/*.py`
2. Run the application: `python bin/run_app.py`
3. Run unit tests: `python bin/unit-test.py`

## Environment Setup
- Copy `dot_env.example` to `.env`
- Configure OpenAI API key in `.env`
- Set `AUTOGEN_USE_DOCKER=False` to run without Docker

## Implementation Status
- Phase 1: ✅ Basic Project Setup and Gradio Chat Interface
- Phase 2: ✅ AG2 Agent Framework Integration
- Phase 3: ⬜ Calendar Query Functionality
- Phase 4: ⬜ Full Booking Functionality
- Phase 5: ⬜ Google Calendar MCP Integration
- Phase 6: ⬜ Polish and Advanced Features

## Technical Details
- Conversation context is maintained between requests
- Three-agent design follows AutoGen best practices
- OpenAI API is used for LLM capabilities
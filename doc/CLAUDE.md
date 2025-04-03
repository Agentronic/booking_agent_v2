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
- `agent.py`: AG2 multi-agent implementation
- `basic_conversation.py`: Fallback conversation handler
- `utils.py`: Utility functions for date/time handling

## Development Workflow
1. Run linting: `pylint *.py`
2. Run the application: `python app.py`
3. Test with: `USE_BASIC_CONVERSATION=true python app.py` for basic mode

## Environment Setup
- Copy `dot_env.example` to `.env`
- Configure OpenAI API key in `.env`
- Set `USE_BASIC_CONVERSATION=false` for AG2 mode
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
- Fallback to basic_conversation if AG2 fails
- Three-agent design follows AutoGen best practices
- OpenAI API is used for LLM capabilities
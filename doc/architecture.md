# Booking Agent Architecture

## Project Overview

The booking agent is designed to be a generic system that:

- Uses **AG2** (AutoGen) for the multi-agent framework
- Provides a **chat interface** for user interaction
- Mediates between **service providers** and **clients** looking to book appointments
- Integrates with **Google Calendar** via MCP (Model Context Protocol)
- Uses **Gradio** for the web interface in the prototype

## What is MCP?

The **Model Context Protocol (MCP)** is an open protocol developed by Anthropic that standardizes how applications provide context to LLMs. It follows a client-server architecture:

- **MCP Clients**: Part of the host application (like Claude or our booking agent) that connects to MCP servers
- **MCP Servers**: Lightweight programs that expose specific capabilities through the standardized protocol
- **Tools**: Functions that MCP servers expose to clients, allowing LLMs to perform actions like creating calendar events
- **Resources**: Data that MCP servers expose to clients, like calendar events

For our Google Calendar integration, we'll use MCP as an intermediary layer. This means:

- Our booking agent won't directly call the Google Calendar API
- Instead, it will communicate with an MCP server that handles the Google Calendar integration
- The MCP server will expose tools like `create_event` and `list_events` that our agent can use

## Architecture Plan

Here's how we're building the booking agent:

### 1. Agent Framework (AG2)
- Set up the core agent system using AG2's multi-agent capabilities
- Define conversation flow and negotiation logic between agents
- Implement three specialized agents:
  - **User Proxy Agent**: Represents the human user in the conversation
  - **Booking Agent**: Coordinates the booking process
  - **Service Provider Agent**: Provides information about services and availability

### 2. MCP Integration
- Use an existing Google Calendar MCP server or build a custom one
- Connect our agent to the MCP server to access calendar functionality
- Implement secure authentication for calendar access

### 3. Web Interface (Gradio)
- Create a simple chat interface using Gradio
- Allow users to interact with the booking agent
- Provide a responsive and intuitive user experience

### 4. Calendar Operations
- Implement calendar querying to find available slots
- Implement booking functionality to create new events
- Add support for modifying and canceling appointments
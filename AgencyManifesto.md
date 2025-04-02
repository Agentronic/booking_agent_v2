# Booking Agent Manifesto

## Core Purpose

This system is a **booking agent** designed to streamline appointment scheduling between service providers and clients.

## Technical Foundation

- Built with **AG2** (AutoGen) multi-agent framework
- Implements a conversational interface using **Gradio**
- Integrates with calendaring systems via **Model Context Protocol (MCP)**

## User Flow

1. **Client Interaction**: User interacts with the agent via a chat interface
2. **Mediation Role**: The agent mediates between a real-world service provider (e.g., a hair salon) and clients seeking appointments
3. **Request Processing**: When a user requests to book a timeslot, the agent initiates a multi-agent conversation
4. **Calendar Integration**: The agent accesses the service provider's calendar via MCP
5. **Negotiation**: The system negotiates a suitable time slot that works for both the client and provider
6. **Confirmation**: Upon agreement, the agent marks the time slot as reserved in the provider's calendar

## Value Proposition

This agent reduces friction in the appointment booking process by:
- Eliminating the need for phone calls or manual scheduling
- Providing 24/7 availability for booking requests
- Optimizing calendar management for service providers
- Creating a seamless experience for clients

# Intelligent Travel Agent
A Large Language Model (LLM)-powered travel agent that uses advanced agentic patterns (ReAct, Reflection) to suggest the best travel plans. The backend is built with FastAPI and supports both live (Amadeus API) and offline (JSON/PDF) data sources for flights, hotels, and activities.

## Features
- Suggests flights, hotels, and activities using LLM reasoning.
- Supports both Amadeus API and local data files (JSON, PDF).
- Modular agentic patterns: ReAct, Reflection, Multi-agent, Tool-using.
- **LangGraph Integration:** Orchestrates complex, stateful multi-agent workflows and reasoning sequences.
- **RAG Pipeline:** Retrieves and injects dynamic context from local documents to enrich LLM prompts and provide accurate, policy-compliant suggestions.
- **MCP:** Exposes application capabilities (like flight search via Amadeus API/JSON and policy search) via standard `fastmcp` servers, allowing LLM clients to seamlessly discover and execute tools using multi-processed endpoints.
- FastAPI interface.

## Supported Agents
The project orchestrates multiple specialized sub-agents to handle different aspects of trip planning:
- **Router Agent:** Acts as the central orchestrator, analyzing user queries and routing them to the appropriate specialized agent.
- **Greeting Agent:** Handles generic requests and initial user interactions.
- **Travel Agent:** Dedicated to flight searching, validation, and itinerary planning using the Amadeus API or local JSON.
- **Flight Policy Agent:** Queries RAG pipelines to return rules and policies (e.g., baggage, cancellation policies) regarding specific flights.
- **Restaurant Agent:** Locates and suggests dining options tailored to the destination and user preferences.
- **Activities Agent:** Suggests local events, landmarks, and activities to build comprehensive daily schedules.

## Requirements
- An [Amadeus self service developer account](https://developers.amadeus.com/self-service) for flight and hotel data
- [Groq](https://groq.com) or [Gemini](https://ai.dev) account for LLM usage (Preferably llama3.3-70B-versatile)
- Local models are also supported (Not Recommended)

## Installation
1. Clone the repository
2. Create a virtual environment within the project folder and run `pip install -r requirements.txt`
3. Navigate to `/src/core` and run `uvicorn interface:app --reload` to host the fastapi interface
4. Open `http://localhost:8000/docs` on your browser and use the Swagger doc to test the features

## Example Usage

### Set your Amadeus access token and Groq API Key
Use the `/set` endpoint to provide your Amadeus and preffered LLM API keys.

### Ask the agent for a travel plan
Use the `/ask` POST method to set the trip details and preferences, and view the response in the response body.

## LICENCE
MIT Licence

Huge thanks to [neural-maze](https://github.com/neural-maze) for [agentic-patterns](https://github.com/neural-maze/agentic-patterns-course), which this application depends on (Licenced under MIT Licence).

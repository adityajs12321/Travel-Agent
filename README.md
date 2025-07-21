# Intelligent Travel Agent
A Large Language Model (LLM)-powered travel agent that uses advanced agentic patterns (ReAct, Reflection) to suggest the best travel plans. The backend is built with FastAPI and supports both live (Amadeus API) and offline (JSON/PDF) data sources for flights, hotels, and activities.

## Features
- Suggests flights, hotels, and activities using LLM reasoning.
- Supports both Amadeus API and local data files (JSON, PDF).
- Modular agentic patterns: ReAct, Reflection, Multi-agent, Tool-using.
- FastAPI interface.

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

# Intelligent Travel Agent
LLM based travel agent that uses ReAct and Reflection pattern to devise the best travel plan, wrapped in FastAPI's interface.

## Requirements
- An [Amadeus self service developer account](https://developers.amadeus.com/self-service) for flight and hotel data
- [Groq](https://groq.com) account for LLM usage (Preferably llama3.3-70B-versatile)

## Installation
1. Clone the repository
2. Create a virtual environment within the project folder and run `pip install -r requirements.txt`
3. Navigate to `/src/core` and run `uvicorn interface:app --reload` to host the fastapi interface
4. Open `http://localhost:8000/docs` on your browser and use the Swagger doc to test the features

## Example Usage

### Set your Amadeus access token and Groq API Key
Use the `/set` POST method to define the `client_id` and `client_secret` for access to Amadeus services and the Groq api key for linking the LLM.

![/set method](https://raw.githubusercontent.com/adityajs12321/Travel-Agent/refs/heads/main/src/imgs/set.png)

### Ask the agent for a travel plan
Use the `/ask` POST method to set the trip details and preferences, and view the response in the response body.

![/ask method](https://raw.githubusercontent.com/adityajs12321/Travel-Agent/refs/heads/main/src/imgs/ask.png)

## LICENCE
MIT Licence

Huge thanks to [neural-maze](https://github.com/neural-maze) for [agentic-patterns](https://github.com/neural-maze/agentic-patterns-course), which this application depends on (Licenced under MIT Licence).

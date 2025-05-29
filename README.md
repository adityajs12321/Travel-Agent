# Intelligent Travel Agent
LLM based travel agent that uses ReAct and Reflection pattern to devise the best travel plan, wrapped in FastAPI's interface.

# Requirements
- An [Amadeus self service developer account](https://developers.amadeus.com/self-service) for flight and hotel data
- Groq account for LLM usage (preferably llama3.3-70B)

# Installation
1. Clone the repository
2. Create a virtual environment within the project folder and run `pip install -r requirements.txt`
3. Navigate to the `core` folder and run `uvicorn interface:app --reload` to host the fastapi interface
4. Open `http://127.0.0.1:8000/docs` on your browser and use the Swagger doc to test the features

# Example Usage
## Set your Amadeus access token
Use the `/set` POST method to define the `client_id` and `client_secret` for access to Amadeues services and the Groq api key for LLM access.

## Ask the agent for a travel plan
Use the `/ask` POST method to set the trip details and preferences

## View your travel plan
Use the `results` GET method to view the results

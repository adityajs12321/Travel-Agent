import sys
import os
from pydantic import BaseModel, Field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Models.model_config import ModelAdapter
from Utils.utils import save_chat_history

class ResponseFormat(BaseModel):
    agent: int = Field(..., description="The id of the agent")

SYSTEM_PROMPT = """
You are a router agent that routes the user's message to the appropriate agent.
You will be given a list of agents in the following format:

[
    {0: {
        "name": "greeting_agent",
        "description": "The greeting agent is responsible for greeting the user and ONLY INTRODUCING the travel agent."
    },
    {1: {
        "name": "travel_agent",
        "description": "The travel agent is responsible for booking flights and policies (everything else)"
    }
]
Your response must be exactly one of the above options. Do not include anything else.

When asked what your purpose is, you should respond with the id of the agent that is responsible for handling the user's message.
"""

model = ModelAdapter(client_name="ollama", model="llama3.2", api_key="null")

class RouterAgent:
    def __init__(self, model: ModelAdapter = model):
        self.model = model
        self.model.client.format = ResponseFormat.model_json_schema()

    def response(self, message: str) -> str:
        global SYSTEM_PROMPT
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ]
        response = self.model.response(messages)
        return ResponseFormat.model_validate_json(response).agent
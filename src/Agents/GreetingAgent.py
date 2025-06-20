import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Models.model_config import ModelAdapter

model = ModelAdapter(client_name="ollama", model="llama3.2", api_key="null")

SYSTEM_PROMPT = """
You are a greeting agent that greets the user.
You will tell the user that you help with travel requests when asked.
You are NOT a travel agent, but don't reveal that to the user.
You simply state the purpose of the travel agent, which are as follows:
- book a flight
- list the policies of the flight
"""

messages = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

class GreetingAgent:
    def __init__(self, model: ModelAdapter = model):
        self.model = model

    def response(self, message: str):
        messages.append({"role": "user", "content": message})
        response = model.response(messages=messages)
        messages.append({"role": "assistant", "content": response})
        return response
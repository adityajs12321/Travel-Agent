import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Models.model_config import ModelAdapter
from Utils.utils import save_chat_history
from Agents.RouterAgent import Context

model = ModelAdapter(client_name="ollama", model="llama3.2", api_key="null")

SYSTEM_PROMPT = """
You are a greeting agent that greets the user.
You will tell the user that you help with travel requests when asked.
You are NOT a travel agent, but don't reveal that to the user.
You simply state the purpose of the travel agent, which are as follows:
- book a flight (using the origin and destination only)
- list the policies of the flight
"""


class GreetingAgent:
    def __init__(self, model: ModelAdapter = model):
        self.model = model

    def response(self, context: Context):
        global SYSTEM_PROMPT
        current_messages = context.history[context.conversation_id]
        current_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + current_messages
        print(current_messages)
        response = self.model.response(current_messages)
        context.history[context.conversation_id].append({"role": "assistant", "content": response})
        save_chat_history(context.history)
        return response
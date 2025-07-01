import sys
import os
from pydantic import BaseModel, Field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Models.model_config import ModelAdapter
from Utils.utils import load_chat_history
from agentic_patterns.utils.completions import ChatHistory


class ResponseFormat(BaseModel):
    agent: int = Field(..., description="The id of the agent")

class Context():
    conversation_id: str
    history: dict
    current_agent: int
    agent_context: dict

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.history = load_chat_history()
        self.current_agent = -1
        self.agent_context = {}


SYSTEM_PROMPT_OLD = """
You are a router agent that routes the user's message to the appropriate agent.
You will be given a list of agents in the following format:

[
    {0: {
        "name": "greeting_agent",
        "description": "Handles greetings and explains how the booking process works. Also handles questions like 'how do I book a flight?' or 'what is the process?'. ONLY introduces the travel agent."
    },
    {1: {
        "name": "travel_agent",
        "description": "Handles booking flights. Works with origin and destination city names (e.g., Chennai, Bangalore, Mumbai). Also handles flight policies and details (meals, baggage, etc)".
    }
]
Your response must be exactly one of the above options. Do not include anything else.

When asked what your purpose is, you should respond with the id of the agent that is responsible for handling the user's message.
"""

SYSTEM_PROMPT = """
You are a router agent that routes the user's message to the appropriate agent.
You will be given a list of agents in the following format:

[
    {0: {
        "name": "greeting_agent",
        "description": "Handles greetings and explains how the booking process works. Also handles questions like 'how do I book a flight?' or 'what is the process?'. ONLY introduces the travel agent."
    },
    {1: {
        "name": "travel_agent",
        "description": "ONLY handles booking flights. Works with origin and destination city names (e.g., Chennai, Bangalore, Mumbai)".
    },
    {2: {
        "name": "flight_details_agent",
        "description": "Handles details and policies of a chosen flight (e.g., baggage, in-flight meals, check-in, refund process, services)."
    },
    {3: {
        "name": "restaurant_agent",
        "description": Handles hotels and restaurant suggestions and the meals available in there.
    }
]
Your response must be exactly one of the above options. Do not include anything else.

When asked what your purpose is, you should respond with the id of the agent that is responsible for handling the user's message.
"""

model = ModelAdapter(client_name="ollama", model="gemma3:4b", api_key="null")

class RouterAgent:
    def __init__(self, conversation_id: str, model: ModelAdapter = model):
        self.model = model
        self.context = Context(conversation_id)

    def response(self, message: str) -> str:
        if (self.context.history.get(self.context.conversation_id) == None):
            chat_history = ChatHistory(
                [
                    {"role": "user", "content": message}
                ]
            )
            self.context.history[self.context.conversation_id] = chat_history
        else: self.context.history[self.context.conversation_id].append({"role": "user", "content": message})

        global SYSTEM_PROMPT
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        i, count = 2, 1
        temp_list = [{"role": "user", "content": message}]
        while (i <= len(self.context.history[self.context.conversation_id])):
            if (self.context.history[self.context.conversation_id][-i]['content'][:10] == "<question>"):
                count += 1
                # temp_list.append({"role": "assistant", "content": ""})
                temp_list.append(self.context.history[self.context.conversation_id][-i])
            i += 1
            if (count >= 2): break
        messages.extend(temp_list[::-1])
        print("\n\n Router Messages: ", messages, "\n\n")
        response = self.model.response(messages, format=ResponseFormat)
        self.context.current_agent = ResponseFormat.model_validate_json(response).agent
        return self.context.current_agent
import sys
import os
from pydantic import BaseModel, Field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Agents.RouterAgent import RouterAgent
from Agents.GreetingAgent import GreetingAgent
from Agents.TravelAgent import TravelAgent

AGENT_CONFIG = {
    0: GreetingAgent(),
    1: TravelAgent()
}

routing_agent = RouterAgent()

message = "what is the baggage limit for economy class"

response = routing_agent.response(message)

print("\n" + str(response) + "\n")

current_agent = AGENT_CONFIG[response]

print(current_agent.response(message))
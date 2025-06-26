import sys
import os

from colorama import Fore

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Agents.RouterAgent import RouterAgent
from Agents.GreetingAgent import GreetingAgent
from Agents.TravelAgent import TravelAgent
from Agents.FlightPolicyAgent import FlightPolicyAgent

conversation_id = "32"

AGENT_CONFIG = {
    0: GreetingAgent(),
    1: TravelAgent(),
    2: FlightPolicyAgent()
}

routing_agent = RouterAgent(conversation_id)

while (True):
    message = input("> ")
    if message == "exit":
        break

    response = routing_agent.response(message)

    print("\n" + str(response) + "\n")

    current_agent = AGENT_CONFIG[routing_agent.context.current_agent]

    print(Fore.GREEN + "\n\n" + current_agent.response(routing_agent.context))
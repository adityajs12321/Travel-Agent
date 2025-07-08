import sys
import os

from colorama import Fore

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Agents.RouterAgent import RouterAgent
from Agents.GreetingAgent import GreetingAgent
from Agents.TravelAgent import TravelAgent
from Agents.FlightPolicyAgent import FlightPolicyAgent
from Agents.RestaurantAgent import RestaurantAgent
from Agents.ActivitiesAgent import ActivitiesAgent
from Models.model_config import ModelAdapter
from Utils.utils import load_chat_history

# temp_chat_history = load_chat_history()

# last_conv_id = list(temp_chat_history.keys())[-1]

# conversation_id = int(last_conv_id) + 1
conversation_id = "4"


_client = ModelAdapter(client_name="gemini", model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))

AGENT_CONFIG = {
    0: GreetingAgent(_client),
    1: TravelAgent(_client),
    2: FlightPolicyAgent(_client),
    3: RestaurantAgent(_client),
    4: ActivitiesAgent(_client)
}

# routing_agent = None
routing_agent = RouterAgent(conversation_id, _client)

while (True):
    message = input("> ")
    if message.lower() == "exit":
        break

    response = routing_agent.response(message)

    print("\n" + str(response) + "\n")

    if (routing_agent.context.current_agent != -1):
        current_agent = AGENT_CONFIG[routing_agent.context.current_agent]
        print(Fore.GREEN + "\n\n" + current_agent.response(routing_agent.context))
    else:
        print("I am strictly a travel agent and cannot help with that.")
        routing_agent.context.history[routing_agent.context.conversation_id] = routing_agent.context.history[routing_agent.context.conversation_id][:-1]

# def set_router_agent(conversation_id: str, client):
#     global routing_agent
#     routing_agent = RouterAgent(conversation_id, client)

# def trip_planning(message: str, client):
#     global routing_agent
#     response = routing_agent.response(message)

#     print("\n" + str(response) + "\n")

#     global AGENT_CONFIG

#     if (routing_agent.context.current_agent != -1):
#         current_agent = AGENT_CONFIG[routing_agent.context.current_agent]
#         current_agent.model = client
#         final_response = current_agent.response(routing_agent.context)
#         print(Fore.GREEN + "\n\n" + final_response)
#         return final_response
#     else:
#         final_response = "I am strictly a travel agent and cannot help with that."
#         print(final_response)
#         routing_agent.context.history[routing_agent.context.conversation_id] = routing_agent.context.history[routing_agent.context.conversation_id][:-1]
#         return final_response
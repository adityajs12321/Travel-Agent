import sys
import os

from colorama import Fore
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Agents.RouterAgent import RouterAgent
from Agents.GreetingAgent import GreetingAgent
from Agents.TravelAgent2 import TravelAgent
from Agents.FlightPolicyAgent import FlightPolicyAgent
from Agents.RestaurantAgent import RestaurantAgent
from Agents.ActivitiesAgent import ActivitiesAgent
from Models.model_config import ModelAdapter
from Utils.utils import load_chat_history
import asyncio

# temp_chat_history = load_chat_history()

# last_conv_id = list(temp_chat_history.keys())[-1]

# conversation_id = int(last_conv_id) + 1
conversation_id = "9"


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

class GraphState(TypedDict):
    conversation_id: str
    message: str
    agent_id: int
    response: str
    
def router_node(state: GraphState):
    agent_id = routing_agent.response(state["message"])
    return {"agent_id": agent_id}

async def call_agent_by_id(agent_id: int):
    global AGENT_CONFIG, _client, routing_agent
    current_agent = AGENT_CONFIG[agent_id]
    current_agent.model = _client
    return await current_agent.response(routing_agent.context)

async def greeting_node(state: GraphState):
    return {"response": await call_agent_by_id(0)}

async def travel_node(state: GraphState):
    return {"response": await call_agent_by_id(1)}

async def flight_policy_node(state: GraphState):
    return {"response": await call_agent_by_id(2)}

async def restaurant_node(state: GraphState):
    return {"response": await call_agent_by_id(3)}

async def activities_node(state: GraphState):
    return {"response": await call_agent_by_id(4)}

async def invalid_request_node(state: GraphState):
    global routing_agent
    final_response = "I am strictly a travel agent and cannot help with that."
    routing_agent.context.history[routing_agent.context.conversation_id] = routing_agent.context.history[routing_agent.context.conversation_id][:-1]
    return {"response": final_response}

def route_to_agent(state: GraphState) -> str:
    mapping = {
        0: "greeting",
        1: "travel",
        2: "flight_policy",
        3: "restaurant",
        4: "activities"
    }
    return mapping.get(state.get("agent_id", -1), "invalid")

workflow = StateGraph(GraphState)

workflow.add_node("router", router_node)
workflow.add_node("greeting", greeting_node)
workflow.add_node("travel", travel_node)
workflow.add_node("flight_policy", flight_policy_node)
workflow.add_node("restaurant", restaurant_node)
workflow.add_node("activities", activities_node)
workflow.add_node("invalid", invalid_request_node)

workflow.add_edge(START, "router")

workflow.add_conditional_edges(
    "router",
    route_to_agent
)

workflow.add_edge("greeting", END)
workflow.add_edge("travel", END)
workflow.add_edge("flight_policy", END)
workflow.add_edge("restaurant", END)
workflow.add_edge("activities", END)
workflow.add_edge("invalid", END)

app = workflow.compile()

async def main():
    while (True):
        message = input("> ")
        if message.lower() == "exit":
            break

        state = {"conversation_id": conversation_id, "message": message, "agent_id": -1, "response": ""}
        result = await app.ainvoke(state)
        
        print(Fore.GREEN + "\n\n" + str(result["response"]))

# asyncio.run(main())

def set_router_agent(conv_id: str, client):
    global routing_agent, _client
    _client = client
    routing_agent = RouterAgent(conv_id, client)
    
    # Update AGENT_CONFIG to use the new client
    global AGENT_CONFIG
    AGENT_CONFIG = {
        0: GreetingAgent(_client),
        1: TravelAgent(_client),
        2: FlightPolicyAgent(_client),
        3: RestaurantAgent(_client),
        4: ActivitiesAgent(_client)
    }

async def trip_planning(message: str, client):
    global routing_agent
    
    state = {"conversation_id": routing_agent.context.conversation_id, "message": message, "agent_id": -1, "response": ""}
    result = await app.ainvoke(state)
    return result["response"]
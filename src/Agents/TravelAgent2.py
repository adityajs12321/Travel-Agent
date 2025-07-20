import sys
import os
import json
from pydantic import BaseModel, Field
from fastmcp import Client

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Models.model_config import ModelAdapter
from agentic_patterns.planning_pattern.react_agent_v2 import ReactAgent
from agentic_patterns.tool_pattern.tool import tool
from RAG.rag import RAG
from Agents.RouterAgent import Context
from RAG.dynamic_context import load_flight_context2
from Utils.utils import save_chat_history
from agentic_patterns.utils.completions import ChatHistory

class NewRequest(BaseModel):
    new_request: int = Field(..., description="The id of the agent")

class ChooseFlight(BaseModel):
    flight_id: int = Field(..., description="The id of the chosen flight")
    flight_details: str = Field(..., description="A natural language response of the details of the chosen flight")

model = ModelAdapter(client_name="ollama", model="gemma3:4b", api_key="null")

SYSTEM_PROMPT_GEMMA = """
You are a travel agent that takes in agent context and calls flight_search_tool by filling it with the agent context.
YOU CAN ONLY SUGGEST NOT BOOK FLIGHTS.

If the user books a new flight, just look it up using flight_search_tool and don' do anything stupid.
If either origin or destination is mentioned, use the context to figure out the most likely value.
"""

SYSTEM_PROMPT = """
You are a travel agent that can ONLY SUGGEST NOT BOOK FLIGHTS.

If the user asks for booking a new flight, just look it up using flight_search_tool, EVEN IF ALL THE PARAMETERS AREN' MET.

If the user asks for a specific flight, use the choose_flight tool and return a natural language response describing the chosen flight.
ONLY CALL ONE TOOL AT A TIME.
"""

SYSTEM_PROMPT_NEW_REQUEST = """
Your job is to identify whether the user is asking for new flight suggestions or questions regarding existing flights and then choose the appropriate agent.
{
    {1: {
        "name": "generic_requests_agent",
        "description": "Handles generic requests (e.g., provide details, etc)"
    },
    {1: {
        "name": "new_flight_request_agent",
        "description": "Looks up flights (e.g., book another flight etc..). Don' call when user asks for a specific flight"
    },
    {2: {
        "name": "existing_flight_request_agent",
        "description": "Deals with existing flight options (e.g., which is the best flight option, which flight is cheaper etc..). Also called when user asks for a specific flight from a list."
    },
}
"""

SYSTEM_PROMPT_EXISTING_REQUEST = """
Your job is to go through given flights and return the flight id and the entire chosen flight details (in natural language) that matches the user's needs.
"""

SYSTEM_PROMPT_OLD= """
You are a travel agent that takes in agent context and calls flight_search_tool by filling it with the agent context.

If the user books a new flight, just look it up using flight_search_tool and don' do anything stupid.
If either origin or destination is mentioned, use the context to figure out the most likely value.
DO NOT RESPOND IN JSON UNLESS ASKED TO.
"""
#Wrap final response in <response></response> tag.

SYSTEM_PROMPT_OLD_2 = """
You are a travel agent that takes user input and calls the flight search tool ONCE after extracting relevant information.
You will then choose (choose NOT book) the best flight provided by the flights list and list the flight details only.

Convert the origin and destination to their respective iataCode. DO NOT USE TOOL FOR IATA CODE.
If either origin or destination is not given, DO NOT ASK THE USER FOR IT, fill them in the flight_search_tool as "NULL".

Once you have the flight details, return it.

If the user asks for the details or policies of the flight (meals, baggage, etc.), you will use the flight_policies_tool to search for the policies and return the relevant policies according to the user's query verbatim.
"""

class AgentContext(BaseModel):
    originLocationCode: str = Field(..., description="The origin airport code")
    destinationLocationCode: str = Field(..., description="The destination airport code")
    departureDate: str = Field(..., description="The date of departure (Should be in YYYY-MM-DD format)")
    adults: str = Field(..., description="The number of adults")
    maxPrice: int = Field(..., description="The max price the flight should cost")
    currencyCode: str = Field(..., description="Currency code (Default is USD)")


@tool
def flight_search_tool(
    originLocationCode: str,
    destinationLocationCode: str,
):
    """
        Gets the flight details provided the given details.

        Args:
            originLocationCode (str): The origin airport code
            destinationLocationCode (str): The destination airport code
        """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up to the common parent directory (src)
    parent_dir = os.path.dirname(current_dir)

    if (originLocationCode == "NULL"):
        return "ERROR : RETURN FINAL RESPONSE STATING THAT ORIGIN IS MISSING, WITHIN <response> </response> tag"
    if (destinationLocationCode == "NULL"):
        return "ERROR : RETURN FINAL RESPONSE STATING THAT DESTINATION IS MISSING, WITHIN <response> </response> tag"

    # Now navigate to the FlightData directory
    file_path = os.path.join(parent_dir, "FlightData", "Flights.json")
    with open(file_path, "r") as f:
        data = json.load(f)
        flights = data["Flights"]
        for flight in flights:
            if (flight["origin"] == originLocationCode and flight["destination"] == destinationLocationCode):
                return {'FLIGHT DETAILS LISTED': flight}
        return "ERROR : No flights found"
tools_list = [flight_search_tool]



TEMP_SYSTEM_PROMPT = """
You are required to extract the origin and destination airport code from the user input. Fill the missing values with 'NULL'. 
Departure date should be in YYYY-MM-DD format
If the user asks for something unrelated to your task, SAY THAT YOU ARE STRICTLY A TRAVEL AGENT AND CANNOT HELP WITH THAT.
"""

temp_messages = [{"role": "system", "content": TEMP_SYSTEM_PROMPT}]

mcp_client = Client("http://127.0.0.1:8000/mcp")


flights_list = []
chosen_flight = {}

class TravelAgent:
    def __init__(self, model: ModelAdapter = model):
        # self.amadeus_client = amadeus_client
        self.model = model

    async def response(self, context: Context):
        global temp_messages, flights_list, chosen_flight, mcp_client

        # temp_messages.append({"role": "user", "content": f"Current agent context: {context.agent_context}"})
        # temp_messages.append(context.history[context.conversation_id][-1])

        # agent_context_params = self.model.response(temp_messages, AgentContext)
        # agent_context_params = AgentContext.model_validate_json(agent_context_params)
        # context.agent_context = dict(agent_context_params)
        # print(context.agent_context)
        # null_keys = [k for k,v in context.agent_context.items() if v == "NULL"]
        # if (null_keys != []):
        #     if (context.agent_context["maxPrice"] == 0): null_keys.append("maxPrice")
        #     temp_messages.append({"role": "user", "content": f"{",".join(null_keys)} is missing, give response in a single sentence asking user to fill it. Don't mention the extracted information"})
        #     response = self.model.response(temp_messages)
        #     temp_messages.append({"role": "assistant", "content": response})
        #     print(f"\n\n temp messages: {temp_messages}")
        #     temp_messages[1:] = []
        #     return response

        # for key in context.agent_context.keys():
        #     if (context.agent_context[key] == "NULL"):
        #         temp_messages.append({"role": "user", "content": f"{key} is missing, give response in a single sentence asking user to fill it. Don't mention the extracted information"})
        #         response = self.model.response(temp_messages)
        #         temp_messages.append({"role": "assistant", "content": response})
        #         return response
        
        _messages = context.history
        _messages[context.conversation_id], flights_list = load_flight_context2(context)
        async with mcp_client:
            await mcp_client.call_tool("set_flights_list", {"_flights_list": flights_list})
        # index = len(_messages[context.conversation_id])
        _messages[context.conversation_id].append({"role": "user", "content": f"Agent Context: {context.agent_context}"})

        react_agent = ReactAgent(tools=tools_list, client=self.model, system_prompt=SYSTEM_PROMPT if self.model.client_name == "gemini" else SYSTEM_PROMPT_GEMMA, add_constraints=self.model.add_constraints, mcp_client=mcp_client, excluded_tools=["set_flights_list"])
            
        response, context.agent_context = await react_agent.run(
            conversation_id=context.conversation_id,
            messages=_messages,
            max_rounds=2,
            save_file=False
        )

        # async with mcp_client:
        #     await mcp_client.call_tool("set_flights_list", {"_flights_list": flights_list})
        # flights_list = tool_call_result[0]
        # context.agent_context = {}
        temp_messages[1:] = []

        print(f"\n\nExample response: {response}")

        context.history[context.conversation_id].append({"role": "assistant", "content": response})
        context.history[context.conversation_id] = ChatHistory(context.history[context.conversation_id])
        save_chat_history(context.history)
        return response
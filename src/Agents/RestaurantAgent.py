import sys
import os
import json
from pydantic import BaseModel, Field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Models.model_config import ModelAdapter
from agentic_patterns.planning_pattern.react_agent_v2 import ReactAgent
from agentic_patterns.tool_pattern.tool import tool
from RAG.rag import RAG
from RAG.dynamic_context import load_restaurant_context
from Agents.RouterAgent import Context
import copy
from Utils.utils import save_chat_history
from agentic_patterns.utils.completions import build_prompt_structure

model = ModelAdapter(client_name="ollama", model="gemma3:4b", api_key="null")

SYSTEM_PROMPT = """
You are a hotel agent that uses the hotel_search_tool and finds the best hotel near the destination.
If user asks for anything specific about a hotel, like meals available in there, use the tool and answer accordingly.

If hotel is already chosen, refer to that for further questions, no need to call any tool.
"""

SYSTEM_PROMPT_NEW_REQUEST = """
Your job is to identify whether the user is asking for new hotel suggestions or questions regarding a hotel already chosen and the choose the appropriate agent.
{
    1: new_hotel_request_agent,
    2: existing_hotel_request_agent
}
"""

class NewRequest(BaseModel):
    new_request: int = Field(..., description="The id of the agent")

hotel_list = []
    
@tool
def hotel_search_tool(
    destinationLocationCode: str
):
    """
        Gets the hotels nearby the destination and returns the price, rating and meals available.

        Args:
            destinationLocationCode (str): The destination in iataCode
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up to the common parent directory (src)
    parent_dir = os.path.dirname(current_dir)

    # Now navigate to the FlightData directory
    file_path = os.path.join(parent_dir, "RestaurantData", "Restaurants.json")
    with open(file_path, "r") as f:
        data = json.load(f)
        hotels = data[destinationLocationCode]
        global hotel_list
        hotel_list = {destinationLocationCode: hotels}
        return hotel_list

tools_list = [hotel_search_tool]

current_hotel = {}

temp_messages = [{"role": "system", "content": SYSTEM_PROMPT_NEW_REQUEST}]

class RestaurantAgent:
    def __init__(self, model: ModelAdapter = model):
        self.model = model

    def response(self, context: Context):
        global current_hotel
        temp_messages.append(context.history[context.conversation_id][-1])
        response = self.model.response(temp_messages, NewRequest)
        new_request = NewRequest.model_validate_json(response).new_request
        print("\nrestaurant agent response", new_request, "\n")

        react_agent = ReactAgent(tools_list, self.model, system_prompt=SYSTEM_PROMPT, add_constraints=self.model.add_constraints)
        _messages = copy.deepcopy(context.history)
        global hotel_list
        _messages[context.conversation_id] = load_restaurant_context(context, current_hotel, hotel_list)
        print(f"\n\n Hotel List: {json.dumps(hotel_list)}\n\n")

        user_prompt = build_prompt_structure(
            prompt=context.history[context.conversation_id][-1]["content"], role="user", tag="question"
        )
        context.history[context.conversation_id][-1] = user_prompt

        response = react_agent.run(
            conversation_id=context.conversation_id,
            messages=_messages,
            max_rounds=10
        )
        if (hotel_list != []): context.history[context.conversation_id].append({"role": "user", "content": f"Hotel List: {json.dumps(hotel_list)}"})
        

        if (new_request == 1): current_hotel = {"role": "assistant", "content": response}
        save_chat_history(context.history)
        return response
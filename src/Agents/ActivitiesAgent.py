import sys
import os
import json
from pydantic import BaseModel, Field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Models.model_config import ModelAdapter
from agentic_patterns.planning_pattern.react_agent_v2 import ReactAgent
from agentic_patterns.tool_pattern.tool import tool
from RAG.rag import RAG
from RAG.dynamic_context import load_activities_context
from Agents.RouterAgent import Context
import copy
from Utils.utils import save_chat_history
from agentic_patterns.utils.completions import build_prompt_structure
from fastmcp import Client

class NewRequest(BaseModel):
    new_request: int = Field(..., description="The id of the agent")

model = ModelAdapter(client_name="ollama", model="gemma3:4b", api_key="null")

SYSTEM_PROMPT = """
You are a hotel agent that uses the hotel_search_tool and finds the best hotel near the destination.
If user asks for anything specific about a hotel, like meals available in there, use the tool and answer accordingly.

If hotel is already chosen, refer to that for further questions, no need to call any tool.
FOCUS ON THE LAST MESSAGE
"""

SYSTEM_PROMPT_NEW_REQUEST = """
Your job is to identify whether the user is asking for new local activities suggestions or questions regarding a activity or tourist spot already chosen and then choose the appropriate agent.
{
    1: new_activities_request_agent,
    2: existing_activity_request_agent
}
"""

activities_list = []
    
@tool
def activities_search_tool(
    destinationLocationCode: str
):
    """
        Gets the local activities in the destination and returns its description among other things.

        Args:
            destinationLocationCode (str): The destination in iataCode
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up to the common parent directory (src)
    parent_dir = os.path.dirname(current_dir)

    # Now navigate to the FlightData directory
    file_path = os.path.join(parent_dir, "ActivitiesData", "Activities.json")
    with open(file_path, "r") as f:
        data = json.load(f)
        activities = data[destinationLocationCode]
        global activities_list
        activities_list = {destinationLocationCode: activities}
        return activities_list

tools_list = [activities_search_tool]

current_activity = {}

temp_messages = [{"role": "system", "content": SYSTEM_PROMPT_NEW_REQUEST}]

mcp_client = Client("http://127.0.0.1:8003/mcp")

class ActivitiesAgent:
    def __init__(self, model: ModelAdapter = model):
        self.model = model

    async def response(self, context: Context):
        global current_activity, activities_list, mcp_client

        temp_messages.append(context.history[context.conversation_id][-1])
        response = self.model.response(temp_messages, NewRequest)
        new_request = NewRequest.model_validate_json(response).new_request
        print("\nrestaurant agent response", new_request, "\n")
        if (new_request == 1): activities_list = []

        react_agent = ReactAgent(tools=tools_list, client=self.model, system_prompt=SYSTEM_PROMPT, add_constraints=self.model.add_constraints, mcp_client=mcp_client)
        _messages = copy.deepcopy(context.history)

        _messages[context.conversation_id] = load_activities_context(context, current_activity, activities_list)
        print(f"\n\n Hotel List: {json.dumps(activities_list)}\n\n")

        user_prompt = build_prompt_structure(
            prompt=context.history[context.conversation_id][-1]["content"], role="user", tag="question"
        )
        context.history[context.conversation_id][-1] = user_prompt

        response, context.agent_context = await react_agent.run(
            conversation_id=context.conversation_id,
            messages=_messages,
            max_rounds=10
        )
        if (activities_list != []): context.history[context.conversation_id].append({"role": "user", "content": f"Activities List: {json.dumps(activities_list)}"})
        

        current_activity = {"role": "assistant", "content": response}
        context.history[context.conversation_id].append(current_activity)
        save_chat_history(context.history)
        return response
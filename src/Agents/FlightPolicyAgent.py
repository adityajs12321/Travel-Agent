import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Models.model_config import ModelAdapter
from agentic_patterns.planning_pattern.react_agent_v2 import ReactAgent
from agentic_patterns.tool_pattern.tool import tool
from RAG.rag import RAG
from Agents.RouterAgent import Context

model = ModelAdapter(client_name="ollama", model="gemma3:4b", api_key="null")

SYSTEM_PROMPT = """
If the user asks for the details or policies of the flight (meals, baggage, etc.), you will use the flight_policies_tool to search for the policies and return the relevant policies according to the user's query verbatim.
"""

SYSTEM_PROMPT_OLD = """
You are a travel agent that takes user input and calls the flight search tool ONCE after extracting relevant information.
You will then choose (choose NOT book) the best flight provided by the flights list and list the flight details only.

Convert the origin and destination to their respective iataCode. DO NOT USE TOOL FOR IATA CODE.
If either origin or destination is not given, DO NOT ASK THE USER FOR IT, fill them in the flight_search_tool as "NULL".

Once you have the flight details, return it.

If the user asks for the details or policies of the flight (meals, baggage, etc.), you will use the flight_policies_tool to search for the policies and return the relevant policies according to the user's query verbatim.
"""

    
@tool
def flight_policies_tool(
    flight_name: str,
    query: str
):
    """
        Gets the flight policies provided the given flight number.

        Args:
            flight_name (str): The airline name (ONLY THE AIRLINE NAME, NOT THE FLIGHT NUMBER)
            query (str): The user's request (copy the user's request exactly word for word)
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up to the common parent directory (src)
    parent_dir = os.path.dirname(current_dir)

    flight_name = "".join(flight_name.split())

    # Now navigate to the FlightData directory
    file_path = os.path.join(parent_dir, "FlightData", "FlightPolicies", f"{flight_name}.pdf")
    
    rag = RAG(file_path)
    search_results = rag.search(query, k=2)

    return list(search_results.keys())[0]

tools_list = [flight_policies_tool]

# temp_messages = [{"role": "system", "content": "You are required to extract the origin and destination airport code from the user input. Fill the missing values with 'NULL'"}]

class FlightPolicyAgent:
    def __init__(self, model: ModelAdapter = model):
        self.model = model

    def response(self, context: Context):
        react_agent = ReactAgent(tools_list, self.model, system_prompt=SYSTEM_PROMPT, add_constraints=self.model.add_constraints)
        response = react_agent.run(
            conversation_id=context.conversation_id,
            messages=context.history,
            max_rounds=10
        )
        return response
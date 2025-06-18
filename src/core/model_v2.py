import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentic_patterns.reflection_pattern.reflection_agent import ReflectionAgent
from agentic_patterns.planning_pattern.react_agent import ReactAgent
from agentic_patterns.tool_pattern.tool import tool
from pydantic import BaseModel, Field
from api_utils.AmadeusAPI import AmadeusClient
from RAG.rag import RAG
from Models.model_config import ModelAdapter

CLIENT_ID = None
CLIENT_SECRET = None
client = None


def set_access_token(client_id, client_secret):
    global client, CLIENT_ID, CLIENT_SECRET
    CLIENT_ID = client_id
    CLIENT_SECRET = client_secret
    try:
        access_token = os.environ.get("AMADEUS_ACCESS_TOKEN")
        if access_token:
            client = AmadeusClient(client_id, client_secret, access_token)
        else:
            client = AmadeusClient(client_id, client_secret)
    except Exception as e:
        print(f"Client failed to connect: {e}")
        client = None

class TripPreferences(BaseModel):
    distance_from_airport: str
    ratings: str

class TripRequest(BaseModel):
    origin: str = Field(..., description="Departure city/airport code")
    destination: str = Field(..., description="Destination city/airport code")
    departure_date: str = Field(..., description="Departure date")
    adults: str = Field(..., description="Number of passengers")
    maxPrice: str = Field(..., description="Maximum price of flight")
    currencyCode: str = Field("USD", description="The currency code")
    hotelPrefs: TripPreferences

@tool
def flight_search_tool(
    originLocationCode: str,
    destinationLocationCode: str,
):
    """
        Gets the flight details provided the given details.

        Args:
            originLocationCode (str): The origin airport code
            destinationLocationCode (str): The origin airport code
        """
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up to the common parent directory (src)
    parent_dir = os.path.dirname(current_dir)

    # Now navigate to the FlightData directory
    file_path = os.path.join(parent_dir, "FlightData", "Flights.json")
    with open(file_path, "r") as f:
        data = json.load(f)
        flights = data["Flights"]
        for flight in flights:
            if (flight["origin"] == originLocationCode and flight["destination"] == destinationLocationCode):
                return flight
        return "No flights found"
    
@tool
def flight_policies_tool(
    flight_name: str,
    query: str
):
    """
        Gets the flight policies provided the given flight number.

        Args:
            flight_name (str): The airline name (ONLY THE AIRLINE NAME, NOT THE FLIGHT NUMBER, AND REMOVE ANY SPACE INBETWEEN)
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

tools_list = [flight_search_tool, flight_policies_tool]

# client = ModelAdapter(client_name="ollama", model="llama3.1:8b", api_key=os.getenv("GEMINI_API_KEY"))
# client = ModelAdapter(client_name="groq", model="llama-3.3-70b-versatile", api_key=os.getenv("GROQ_API_KEY"))
# client = ModelAdapter(client_name="gemini", model="gemini-2.0-flash", api_key=os.getenv("GEMINI_API_KEY"))


class IntelTravelModel:
    def trip_planning(self, conversation_id: str, request: str, client: ModelAdapter):
        """Trip planning using ReAct and Reflection patterns"""

        model = ReactAgent(tools_list, client, system_prompt=client.system_prompt, add_constraints=client.add_constraints)
        response = model.run(
            conversation_id=conversation_id,
            user_msg=request,
            max_rounds=10
        )

        return response
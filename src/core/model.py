import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentic_patterns.reflection_pattern.reflection_agent import ReflectionAgent
from agentic_patterns.planning_pattern.react_agent import ReactAgent
from agentic_patterns.tool_pattern.tool import tool
from pydantic import BaseModel, Field
from api_utils.AmadeusAPI import AmadeusClient

CLIENT_ID = os.environ['AMADEUS_CLIENT_ID']
CLIENT_SECRET = os.environ['AMADEUS_CLIENT_SECRET']
client = None

try:
    access_token = os.environ["AMADEUS_ACCESS_TOKEN"]
    client = AmadeusClient(CLIENT_ID, CLIENT_SECRET, access_token)
except Exception as e:
    print("No access token found")
    client = AmadeusClient(CLIENT_ID, CLIENT_SECRET)
except Exception as e:
    print("Client failed to connect")

class TripRequest(BaseModel):
    origin: str = Field(..., description="Departure city/airport code")
    destination: str = Field(..., description="Destination city/airport code")
    departure_date: str = Field(..., description="Departure date")
    adults: str = Field(..., description="Number of passengers")
    maxPrice: str = Field(..., description="Maximum price of flight")
    currencyCode: str = Field("USD", description="The currency code")

class TravelTools:
    def __init__(self, amadeus_client: AmadeusClient):
        self.amadeus_client = amadeus_client

@tool
def flight_search_tool(
    originLocationCode: str,
    destinationLocationCode: str,
    departureDate: str,
    adults: str,
    maxPrice: str,
    currencyCode: str = "USD"
):
        f"""
        Gets the flight details provided the given details.

        Args:
            originLocationCode (str): The origin airport code
            destinationLocationCode (str): The origin airport code
            departureDate (str): The date of departure (Should be in YYYY-MM-DD format)
            adults (str): The number of adults
            maxPrice (str): The max price the flight should cost
            currencyCode (str): Currency code
        """
        try:
            result = client.search_flights(
                originLocationCode,
                destinationLocationCode,
                departureDate,
                adults,
                maxPrice,
                currencyCode
            )

            flights = []

            i = 5
            for offer in result.get("data", []):
                if (i <= 0):
                    break
                segments = offer['itineraries'][0]['segments']
                final_arrival = segments[-1]['arrival']['iataCode']
                if final_arrival != destinationLocationCode:
                    continue
                i -= 1
                flight_info = {
                    "id": offer['id'],
                    'price': offer['price']['total'],
                    'currency': offer['price']['currency'],
                    'itineraries': []
                }

                for itinerary in offer['itineraries']:
                    itinerary_info = {
                        'duration': itinerary['duration'],
                        'segments': []
                    }

                    for segment in itinerary['segments']:
                        segment_info = {
                            'departure': {
                                'airport': segment['departure']['iataCode'],
                                'time': segment['departure']['at']
                            },
                            'arrival': {
                                'airport': segment['arrival']['iataCode'],
                                'time': segment['arrival']['at']
                            },
                            'airline': segment['carrierCode'],
                            'flight_number': segment['number']
                        }
                        itinerary_info['segments'].append(segment_info)
                    
                    flight_info['itineraries'].append(itinerary_info)
                flights.append(flight_info)
            
            return flights
        except Exception as e:
            print(e)
            print("No Flights found")
            return []
tools_list = [flight_search_tool]

tools = {
    'flight_search_tool': flight_search_tool.fn
}

class IntelTravelModel:
    def trip_planning(self, request: TripRequest):
        """Trip planning using ReAct and Reflection patterns"""

        # flights = tools['flight_search_tool'](
        #     request
        # )

        model = ReactAgent(tools_list)
        response = model.run(
            user_msg=f"""
            Here are the travel details:

            originLocationCode: {request.origin}
            destinationLocationCode: {request.destination}
            departureDate: {request.departure_date}
            adults: {request.adults}
            maxPrice: {request.maxPrice}
            currencyCode: {request.currencyCode}
            """,
            max_rounds=3
        )

        return response

# model_agent = IntelTravelModel()
# trip_request = TripRequest(origin="JFK", 
#                            destination="LAX", 
#                            departure_date="2025-06-04", 
#                            adults="1", 
#                            maxPrice="200",
#                            currencyCode="USD")
# response = model_agent.trip_planning(trip_request)
# print(response)
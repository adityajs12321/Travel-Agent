import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentic_patterns.reflection_pattern.reflection_agent import ReflectionAgent
from agentic_patterns.planning_pattern.react_agent import ReactAgent
from agentic_patterns.tool_pattern.tool import tool
from pydantic import BaseModel, Field
from api_utils.AmadeusAPI import AmadeusClient

CLIENT_ID = None
CLIENT_SECRET = None
client = None

BASE_SYSTEM_PROMPT = """
You are a travel agent that takes user input and calls the flight search tool after extracting relevant information.
You can only suggest travel plans, not book them.
You will then choose (choose not book) the best flight provided by the flights list and list the flight details only
Convert the departureDate for flight search tool to YYYY-MM-DD format
Convert the origin and destination to their respective iataCode
Every parameter is a must and in case a parameter isn't provided by the user, ask for it

If the user asks for hotels, look up hotels near the destination by using the hotel search tool and choose the best hotel to stay in wi.
"""

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

@tool
def hotel_search_tool(
    cityCode: str,
    distance_from_airport: str,
    ratings: str
):
    f"""
        Gets the hotel details provided the given details.

        Args:
            cityCode (str): The destination airport code
            distance_from_airport (str): Max distance between hotel and airport
            ratings (str): The hotel rating the user is looking for. (If multiple are given, wrap them as a string with comma seperated values)
        """
    try:
        response = client.search_hotels(cityCode, distance_from_airport, ratings)
    
        hotels = []

        for hotel in response.get("data", [])[:5]:
            hotelInfo = {
                "name": hotel["name"],
                "hotelId": hotel["hotelId"],
                "distance": hotel["distance"],
                "rating": hotel["rating"]
            }

            hotels.append(hotelInfo)
    
        return hotels
    except Exception as e:
        print(e)
        print("No hotels found")
        return []

tools_list = [flight_search_tool, hotel_search_tool]

class IntelTravelModel:
    def trip_planning(self, conversation_id: int, request: str):
        """Trip planning using ReAct and Reflection patterns"""

        model = ReactAgent(tools_list, system_prompt=BASE_SYSTEM_PROMPT)
        response = model.run(
            conversation_id=conversation_id,
            user_msg=request,
            max_rounds=10
        )

        return response
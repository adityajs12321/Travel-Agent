from agentic_patterns.reflection_pattern.reflection_agent import ReflectionAgent
from agentic_patterns.planning_pattern.react_agent import ReactAgent
from agentic_patterns.tool_pattern.tool import tool
from pydantic import BaseModel, Field
from AmadeusAPI import AmadeusClient

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

    def flight_search_tool(self, trip_request: TripRequest):
        """Tool 1: Available flights search"""
        try:
            result = self.amadeus_client.search_flights(
                trip_request.origin,
                trip_request.destination,
                trip_request.departure_date,
                trip_request.adults,
                trip_request.maxPrice,
                trip_request.currencyCode
            )

            flights = []

            for offer in result.get("data", [])[:5]:
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
            print("No Flights found")
            return []

class IntelTravelModel:
    def __init
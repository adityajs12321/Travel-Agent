import os
import json
import multiprocessing
from fastmcp import FastMCP, Context
from fastmcp.tools import Tool
from fastmcp.tools.tool_transform import ArgTransform
import sys
from pydantic import Field

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RAG.rag import RAG

from api_utils.AmadeusAPI import AmadeusClient
client = AmadeusClient(os.getenv("AMADEUS_CLIENT_ID"), os.getenv("AMADEUS_CLIENT_SECRET"))
flights_list = []

# Args:
# 		originLocationCode (str): The origin airport iataCode, e.g, BLR, JFK (default: "NULL")
# 		destinationLocationCode (str): The destination airport iataCode (default: "NULL")
# 		departureDate (str): The date of departure (Should be in YYYY-MM-DD format) (default: "NULL")
# 		adults (str): The number of adults (default: "NULL")
# 		maxPrice (str): The max price the flight should cost, (default: 0)
# 		currencyCode (str): Currency code (default: USD)

# === Server 1 ===
flight_search_mcp = FastMCP("Flight Agent Tools")

@flight_search_mcp.tool()
def flight_search_tool(
	originLocationCode: str = Field('NUL', description="The origin airport iataCode", examples=["BLR", "TVM"], max_length=3),
	destinationLocationCode: str = Field('NUL', description="The destination airport iataCode", examples=["JFK", "LON"], max_length=3),
	departureDate: str = Field('NULL', description="The date of departure (In YYYY-MM-DD format)"),
	adults: str = Field('NULL', description="The number of adults"),
	maxPrice: str = Field('0', description="The max price the flight should cost"),
	currencyCode: str = Field('USD', description="Currency code")
):
	"""
	Gets the flight details provided the given details.	
	"""

	global flights_list

	agent_context = {"originLocationCode": originLocationCode,
					"destinationLocationCode": destinationLocationCode,
					"departureDate": departureDate,
					"adults": adults,
					"maxPrice": maxPrice,
					"currencyCode": currencyCode}
	
	print(f"\n\nAgent Context: {agent_context}")
	
	null_keys = [k for k,v in agent_context.items() if (v == "NULL" or v == "NUL")]

	if (null_keys != []):
		if (agent_context["maxPrice"] == '0'): null_keys.append("maxPrice")
		return {"tool_results": f"{",".join(null_keys)} is missing, give response in a single sentence asking user to fill it. Don't mention the extracted information", "agent_context": agent_context}

	try:
		result = client.search_flights(
			originLocationCode,
			destinationLocationCode,
			departureDate,
			adults,
			str(maxPrice),
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
			
		flights_list = flights
		return {"tool_results": {'FLIGHT DETAILS LISTED': flights}, "agent_context": agent_context}
	except Exception as e:
		print(e)
		print("No Flights found")
		return {"tool_results": [], "agent_context": agent_context}
	
@flight_search_mcp.tool()
def set_flights_list(_flights_list: list):
	global flights_list
	flights_list = _flights_list

# set_flights_list.disable()
# @flight_search_mcp.tool()
# def set_flights_list():
# 	return "erferf"


@flight_search_mcp.tool()
def choose_flight(chosen_flight_id: str):
	"""
		Chooses a specific flight given the flight details

		Args:
			chosen_flight_id (int): The id of the chosen flight
	"""
	global flights_list
	agent_context = {}
	chosen_flight = list(filter(lambda flight: flight['id'] == str(chosen_flight_id), flights_list))[0]
	return {"tool_results": {'CHOSEN FLIGHT DETAILS': chosen_flight}, "agent_context": agent_context}

# === Server 2 ===
flight_policy_mcp = FastMCP("Flight Policy Tools")

@flight_policy_mcp.tool()
def flight_policies_tool(
	flight_name: str,
	query: str
):
	"""
		Gets the flight policies provided the given flight number.

		Args:
			flight_name (str): The airline's IATA code
			query (str): The user's request (copy the user's request exactly word for word)
	"""
	agent_context = {}
	current_dir = os.path.dirname(os.path.abspath(__file__))

	# Go up to the common parent directory (src)
	parent_dir = os.path.dirname(current_dir)

	flight_name = "".join(flight_name.split())

	# Now navigate to the FlightData directory
	file_path = os.path.join(parent_dir, "FlightData", "FlightPolicies", f"{flight_name}.pdf")
	
	rag = RAG(file_path)
	search_results = rag.search(query, k=2)

	return {"tool_results": list(search_results.keys())[0], "agent_context": agent_context}

# === Server 3 ===
restaurant_mcp = FastMCP("Restaurant tools")

@restaurant_mcp.tool()
def hotel_search_tool(
    destinationLocationCode: str
):
    """
        Gets the hotels nearby the destination and returns the price, rating and meals available.

        Args:
            destinationLocationCode (str): The destination in iataCode. e.g., 'TRV'
    """
    agent_context = {}
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
        return {"tool_results": hotel_list, "agent_context": agent_context}
	
# === Server 4 ===
activities_mcp = FastMCP("Activities tools")

@activities_mcp.tool()
def activities_search_tool(
    destinationLocationCode: str
):
    """
        Gets the local activities in the destination and returns its description among other things.

        Args:
            destinationLocationCode (str): The destination in iataCode. e.g., 'TRV'
    """
    agent_context = {}
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
        return {"tool_results": activities_list, "agent_context": agent_context}

# === Threaded Execution ===
def run_mcp1():
	flight_search_mcp.run(transport="streamable-http", port=8000, path="/mcp")

def run_mcp2():
	flight_policy_mcp.run(transport="streamable-http", port=8001, path="/mcp")

def run_mcp3():
	restaurant_mcp.run(transport="streamable-http", port=8002, path="/mcp")

def run_mcp4():
	activities_mcp.run(transport="streamable-http", port=8003, path="/mcp")

if __name__ == "__main__":
	# Create a Process for each server instead of a Thread
	process_one = multiprocessing.Process(
		target=run_mcp1
	)
	process_two = multiprocessing.Process(
		target=run_mcp2
	)
	process_three = multiprocessing.Process(
		target=run_mcp3
	)
	process_four = multiprocessing.Process(
		target=run_mcp4
	)

	# Start both processes
	process_one.start()
	process_two.start()
	process_three.start()
	process_four.start()

	try:
		process_one.join()
		process_two.join()
		process_three.join()
		process_four.join()
	except KeyboardInterrupt:
		print("\nShutting down servers...")
		process_one.terminate()
		process_two.terminate()
		process_three.terminate()
		process_four.terminate()

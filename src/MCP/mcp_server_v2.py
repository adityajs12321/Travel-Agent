import os
import json
import multiprocessing
from fastmcp import FastMCP
from fastmcp.tools import Tool
from fastmcp.tools.tool_transform import ArgTransform
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RAG.rag import RAG

# === Server 1 ===
flight_search_mcp = FastMCP("Flight Agent Tools")

@flight_search_mcp.tool()
def flight_search_tool_base(
	originLocationCode: str,
	destinationLocationCode: str,
	departureDate: str,
	adults: str,
	maxPrice: str,
	currencyCode: str,
	client
):
	"""
	Gets the flight details provided the given details.

	Args:
		originLocationCode (str): The origin airport code
		destinationLocationCode (str): The origin airport code
		departureDate (str): The date of departure (Should be in YYYY-MM-DD format)
		adults (str): The number of adults
		maxPrice (str): The max price the flight should cost
		currencyCode (str): Currency code (Default is USD)
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
	
flight_search_tool = Tool.from_tool(
    flight_search_tool_base,
    name="flight_search_tool",
    transform_args={
        "client": ArgTransform(
            hide=True,
            default=None
        )
    }
)

# === Server 2 ===
mcp2 = FastMCP("Flight Policy Tools")

@mcp2.tool()
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

# === Threaded Execution ===
def run_mcp1():
	mcp.run(transport="streamable-http", port=8000, path="/mcp")

def run_mcp2():
	mcp2.run(transport="streamable-http", port=8001, path="/mcp")

if __name__ == "__main__":
	# Create a Process for each server instead of a Thread
	process_one = multiprocessing.Process(
		target=run_mcp1
	)
	process_two = multiprocessing.Process(
		target=run_mcp2
	)

	# Start both processes
	process_one.start()
	process_two.start()

	try:
		process_one.join()
		process_two.join()
	except KeyboardInterrupt:
		print("\nShutting down servers...")
		process_one.terminate()
		process_two.terminate()

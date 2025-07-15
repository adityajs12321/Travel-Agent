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
mcp = FastMCP("Flight Agent Tools")

@mcp.tool()
def flight_search_tool_base(originLocationCode: str, destinationLocationCode: str, optional: str):
    """
    Gets the flight details provided the given details.

    Args:
        originLocationCode (str): The origin airport code
        destinationLocationCode (str): The destination airport code
    """

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    file_path = os.path.join(parent_dir, "FlightData", "Flights.json")

    if originLocationCode == "NULL":
        return "<response>ERROR: ORIGIN IS MISSING</response>"
    if destinationLocationCode == "NULL":
        return "<response>ERROR: DESTINATION IS MISSING</response>"

    with open(file_path, "r") as f:
        data = json.load(f)
        for flight in data["Flights"]:
            if flight["origin"] == originLocationCode and flight["destination"] == destinationLocationCode:
                return {"FLIGHT DETAILS LISTED": flight}
        return "<response>ERROR: No flights found</response>"
    
new_tool = Tool.from_tool(
    flight_search_tool_base,
    name="flight_search_tool",
    transform_args={
        "optional": ArgTransform(
            hide=True,
            default="lmfao"
        )
    }
)
mcp.add_tool(new_tool)

flight_search_tool_base.disable()

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

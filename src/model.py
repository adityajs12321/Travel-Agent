from langchain_groq import ChatGroq
from agentic_patterns.reflection_pattern.reflection_agent import ReflectionAgent
from agentic_patterns.planning_pattern.react_agent import ReactAgent
from agentic_patterns.tool_pattern.tool import tool
from api_calling import return_results

# agent = ReflectionAgent()

# generation_system_prompt = """You are a Python Programmer tasked with generating high quality code
#     Your task is to generate the best possible code for the user. If the user provides critique,
#     respond with a revised version of the previous code
# """

# reflection_system_prompt = """You are an experienced computer scientist, tasked with providing critique and recommendations for the provided code"""

# response = agent.run(
#     user_msg="Generate C code that implements the merge sort algorithm",
#     generation_system_prompt=generation_system_prompt,
#     reflection_system_prompt=reflection_system_prompt,
#     n_steps=3,
# )

# print(response)

@tool
def get_flight_details(originLocationCode: str, destinationLocationCode: str, departureDate: str, adults: str, maxPrice: str, currencyCode: str):
    """
    Gets the flight details provided the given details.

    Args:
        originLocationCode (str): The origin airport code
        destinationLocationCode (str): The origin airport code
        departureDate (str): The date of departure (Should be in YYYY-MM-DD format)
        adults (str): The number of adults
        maxPrice (str): The max price the flight should cost
        currencyCode (str): Currency code
    """
    print(return_results(originLocationCode, destinationLocationCode, departureDate, adults, maxPrice, currencyCode))


agent = ReactAgent(get_flight_details)
response = agent.run(
    "i want to book a flight from JFK to Los Angeles on 2025-6-4 for 1 adult. price should not exceed 200 and the currency code is USD",
    max_rounds=3
)
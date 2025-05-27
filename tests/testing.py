import os
from agentic_patterns.tool_pattern.tool import tool

@tool
def return_results():
    print("wefwf")

print(return_results.name)
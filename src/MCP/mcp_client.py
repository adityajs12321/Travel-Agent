import json
from fastmcp import Client
import asyncio

mcp_client2 = Client("http://127.0.0.1:8000/mcp")
# print(mcp_client2.is_connected())

async def return_tools():
    async with mcp_client2:
        tools = await mcp_client2.list_tools()
        tool_definitions = [tool.model_dump() for tool in tools]
        print(tool_definitions)

asyncio.run(return_tools())
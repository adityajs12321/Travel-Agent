import sys
import os

from colorama import Fore

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Agents.RouterAgent import RouterAgent
from Agents.GreetingAgent import GreetingAgent
from Agents.TravelAgent import TravelAgent
from agentic_patterns.utils.completions import ChatHistory
from Utils.utils import load_chat_history

conversation_id = "15"
chat_history_ids = load_chat_history()

AGENT_CONFIG = {
    0: GreetingAgent(),
    1: TravelAgent() 
}

routing_agent = RouterAgent()

message = "book a flight from chennai"

if (chat_history_ids.get(conversation_id) == None):
    chat_history = ChatHistory(
        [
            {"role": "user", "content": message}
        ]
    )
    chat_history_ids[conversation_id] = chat_history
else: chat_history_ids[conversation_id].append({"role": "user", "content": message})

response = routing_agent.response(message)

print("\n" + str(response) + "\n")

current_agent = AGENT_CONFIG[response]

print(Fore.GREEN + "\n\n" + current_agent.response(chat_history_ids, conversation_id))
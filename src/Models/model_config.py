from groq import Groq
from google import genai
from langchain_community.chat_models.ollama import ChatOllama
import lmstudio as lms
from ollama import chat

BASE_SYSTEM_PROMPT = """
You are a travel agent that takes user input and calls the flight search tool after extracting relevant information.
You can only suggest travel plans, not book them.
You will then choose (choose not book) the best flight provided by the flights list and list the flight details only.
Convert the origin and destination to their respective iataCode.
Both origin and destination are required.

If the user asks for the details or policies of the flight (meals, baggage, etc.), you will use the flight_policies_tool to search for the policies and return the relevant policies according to the user's query verbatim.
"""

# OLLAMA_SYSTEM_PROMPT = """
# You are a travel agent that does two independent things:

# 1. If the user asks to book a flight, call the flight search tool after extracting relevant information, then return the best flight.
# You can only suggest travel plans, not book them.
# Convert the origin and destination to their respective iataCode.
# Both origin and destination are required.

# 2. If and ONLY IF the user asks for the details or policies of the flight (meals, baggage, etc.), you will use the flight_policies_tool to search for the policies and return the relevant policies according to the user's query.

# ALWAYS FOCUS ON THE LAST MESSAGE. FINAL RESPONSE MUST ANSWER THE USER'S QUERY.
# """

OLLAMA_SYSTEM_PROMPT = """
You are a travel agent that does two independent things:

1. If the user asks to book a flight, call the flight search tool after extracting relevant information, then return the best flight.
You can only suggest travel plans, not book them.
Convert the origin and destination to their respective iataCode.
Both origin and destination are required.

2. If and ONLY IF the user asks for the details or policies of the flight (meals, baggage, etc.), you will use the flight_policies_tool to search for the policies and return the relevant policies according to the user's query.

ALWAYS FOCUS ON THE LAST MESSAGE. FINAL RESPONSE MUST ANSWER THE USER'S QUERY. DO NOT MIX UP OTHER ANSWERS WITH CURRENT ANSWER.
"""

def groq_response(client, messages: list, model: str) -> str:
    response = client.chat.completions.create(messages=messages, model=model)
    return str(response.choices[0].message.content)

def gemini_response(client, messages: list, model: str) -> str:
    chat_history = []
    for message in messages[:len(messages) - 1]:
        chat_history.append(
            {
                "role": "model" if (message["role"] == "system" or message["role"] == "assistant") else message["role"],
                "parts": [
                    {
                        "text": message["content"]
                    }
                ]
            }
        )
    print(chat_history)
    chat = client.chats.create(model=model, history=chat_history)
    response = chat.send_message(messages[-1]["content"])
    return response.text

def ollama_response(client, messages: list, model: str) -> str:
    client.model = model
    response = client.invoke(messages)
    if (model == "qwen3"):
        # return str(response.content)[19:]
        return str(response.content)
    return response.content

def lmstudio_response(client, messages: list, model: str) -> str:
    client.model = model
    messages[-1]["content"] = messages[-1]["content"] + " /no_think"
    response = client.respond({"messages": messages})
    return response.content

MODEL_CONFIGS = {
    "groq": {
        "client_name": "groq",
        "client": Groq(),
        "response_generator": groq_response,
        "system_prompt": BASE_SYSTEM_PROMPT
    },
    "gemini": {
        "client_name": "gemini",
        "client": genai.Client(),
        "response_generator": gemini_response,
        "system_prompt": BASE_SYSTEM_PROMPT
    },
    "ollama": {
        "client_name": "ollama",
        # "client": ChatOllama(num_ctx=4096, temperature=0.1, top_k=75, top_p=0.65),
        "client": ChatOllama,
        # "client_settings": {
        #     "num_ctx": 4096, 
        #     "temperature": 0.1, 
        #     "top_k": 80, 
        #     "top_p": 0.65
        # },
        "client_settings": {
            "num_ctx": 4096, 
            "temperature": 0.1, 
            "top_k": 80, 
            "top_p": 0.65
        },
        # "client": ChatOllama(num_ctx=4096, temperature=0.1, top_k=100, top_p=0.65),
        "response_generator": ollama_response,
        "system_prompt": OLLAMA_SYSTEM_PROMPT
    }
    # "lmstudio": {
    #     "client_name": "lmstudio",
    #     "client": lms.llm(config={"contextLength": 4096}),
    #     "response_generator": lmstudio_response
    # }
}

class ModelAdapter:    
    def __init__(
        self,
        client_name: str,
        api_key: str,
        model: str,
        system_prompt: str = "",
    ):
        self.client_name = client_name
        self.api_key = api_key
        self.model = model
        self.client = MODEL_CONFIGS[client_name]["client"](**MODEL_CONFIGS[client_name]["client_settings"])
        self.add_constraints = True
        if self.client_name == "groq":
            self.client.api_key = self.api_key
        elif self.client_name == "gemini":
            self.client._api_client.api_key = self.api_key
        elif self.client_name == "ollama":
            self.add_constraints = False
            self.client.model = self.model
        self.system_prompt = MODEL_CONFIGS[client_name]["system_prompt"]

    def response(self, messages: list) -> str:
        return MODEL_CONFIGS[self.client_name]["response_generator"](self.client, messages, self.model)
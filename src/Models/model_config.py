from groq import Groq
from google import genai
from langchain_community.chat_models.ollama import ChatOllama
import lmstudio as lms

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
        return str(response.content)[19:]
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
        "response_generator": groq_response
    },
    "gemini": {
        "client_name": "gemini",
        "client": genai.Client(),
        "response_generator": gemini_response
    },
    "ollama": {
        "client_name": "ollama",
        "client": ChatOllama(num_ctx=4096),
        "response_generator": ollama_response
    },
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
    ):
        self.client_name = client_name
        self.api_key = api_key
        self.model = model
        self.client = MODEL_CONFIGS[client_name]["client"]
        if self.client_name == "groq":
            self.client.api_key = self.api_key
        elif self.client_name == "gemini":
            self.client._api_client.api_key = self.api_key
        elif self.client_name == "ollama":
            self.client.model = self.model

    def response(self, messages: list) -> str:
        return MODEL_CONFIGS[self.client_name]["response_generator"](self.client, messages, self.model)
        

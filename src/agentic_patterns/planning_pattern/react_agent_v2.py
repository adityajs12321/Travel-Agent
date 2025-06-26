import json
from typing import Union
from pathlib import Path

from colorama import Fore

from agentic_patterns.tool_pattern.tool import Tool
from agentic_patterns.tool_pattern.tool import validate_arguments
from agentic_patterns.utils.completions import build_prompt_structure
from agentic_patterns.utils.completions import ChatHistory
from agentic_patterns.utils.completions import completions_create
from agentic_patterns.utils.completions import update_chat_history
from agentic_patterns.utils.extraction import extract_tag_content


BASE_SYSTEM_PROMPT = """
You are a travel agent that takes user input and calls the flight search tool after extracting relevant information.
You can only suggest travel plans, not book them.
You will then choose (choose not book) the best flight provided by the flights list and list the flight details only
Convert the departureDate for flight search tool to YYYY-MM-DD format
Convert the origin and destination to their respective iataCode
Every parameter is a must and in case a parameter isn't provided by the user, ask for it

If the user asks for hotels, look up hotels near the destination by using the hotel search tool and choose the best hotel to stay in wi.
"""


REACT_SYSTEM_PROMPT = """
You operate by running a loop with the following steps: Thought, Action, Observation.
You are provided with function signatures within <tools></tools> XML tags.
You may call one or more functions to assist with the user query. Don' make assumptions about what values to plug
into functions. Pay special attention to the properties 'types'. You should use those types as in a Python dict.

For each function call return a json object with function name and arguments within <tool_call></tool_call> XML tags as follows:

<tool_call>
{"name": <function-name>,"arguments": <args-dict>, "id": <monotonically-increasing-id>}
</tool_call>

Here are the available tools / actions:

<tools>
%s
</tools>

Example session:

<question>What's the current temperature in Madrid?</question>
<thought>I need to get the current weather in Madrid</thought>
<tool_call>{"name": "get_current_weather","arguments": {"location": "Madrid", "unit": "celsius"}, "id": 0}</tool_call>

You will be called again with this:

<observation>{0: {"temperature": 25, "unit": "celsius"}}</observation>

You then output:

<response>The current temperature in Madrid is 25 degrees Celsius</response>

Additional constraints:

- If the user asks you something unrelated to any of the tools above, say that you are strictly a travel agent and you can't help with that.
"""

additional_constraints = "- You can answer greet and info responses, like 'Hello, how can I help you today?' or 'I'm here to help you with your travel plans."

# chat_history = ChatHistory(
#     [
#         build_prompt_structure(
#             prompt=BASE_SYSTEM_PROMPT,
#             role="system",
#         )
#     ]
# )

def save_chat_history(chat_history_ids: dict, file_path: str = "chat_history.json") -> None:
    """
    Save chat history to a JSON file.
    
    Args:
        chat_history_ids (dict): Dictionary containing chat histories
        file_path (str): Path to save the JSON file
    """
    # Convert chat history to serializable format
    serializable_history = {}
    for conv_id, history in chat_history_ids.items():
        serializable_history[str(conv_id)] = history.to_dict()
    
    with open(file_path, 'w') as f:
        json.dump(serializable_history, f)

def load_chat_history(file_path: str = "chat_history.json") -> dict:
    """
    Load chat history from a JSON file.
    
    Args:
        file_path (str): Path to load the JSON file from
        
    Returns:
        dict: Dictionary containing chat histories
    """
    if not Path(file_path).exists():
        print(Fore.RED + "No chat history file found")
        return {}
        
    with open(file_path, 'r') as f:
        serialized_history = json.load(f)
        print(Fore.GREEN + "Successfully loaded chat history")
    
    # Convert back to ChatHistory objects
    chat_history_ids = {}
    for conv_id, history_dict in serialized_history.items():
        chat_history_ids[conv_id] = ChatHistory.from_dict(history_dict)
    
    return chat_history_ids

class ReactAgent:
    """
    A class that represents an agent using the ReAct logic that interacts with tools to process
    user inputs, make decisions, and execute tool calls. The agent can run interactive sessions,
    collect tool signatures, and process multiple tool calls in a given round of interaction.

    Attributes:
        client (Groq): The Groq client used to handle model-based completions.
        model (str): The name of the model used for generating responses. Default is "llama-3.3-70b-versatile".
        tools (list[Tool]): A list of Tool instances available for execution.
        tools_dict (dict): A dictionary mapping tool names to their corresponding Tool instances.
    """

    def __init__(
        self,
        tools: Union[Tool, list[Tool]],
        client,
        system_prompt: str = BASE_SYSTEM_PROMPT,
        add_constraints: bool = True
    ) -> None:
        self.client = client
        self.system_prompt = system_prompt
        self.tools = tools if isinstance(tools, list) else [tools]
        self.tools_dict = {tool.name: tool for tool in self.tools}
        self.add_constraints = add_constraints

    def add_tool_signatures(self) -> str:
        """
        Collects the function signatures of all available tools.

        Returns:
            str: A concatenated string of all tool function signatures in JSON format.
        """
        return "".join([tool.fn_signature for tool in self.tools])

    def process_tool_calls(self, tool_calls_content: list) -> dict:
        """
        Processes each tool call, validates arguments, executes the tools, and collects results.

        Args:
            tool_calls_content (list): List of strings, each representing a tool call in JSON format.

        Returns:
            dict: A dictionary where the keys are tool call IDs and values are the results from the tools.
        """
        observations = {}
        for tool_call_str in tool_calls_content:
            tool_call = json.loads(tool_call_str)
            tool_name = tool_call["name"]
            tool = self.tools_dict.get(tool_name)

            print(Fore.GREEN + f"\nUsing Tool: {tool_name}")

            # Validate and execute the tool call
            validated_tool_call = validate_arguments(
                tool_call, json.loads(tool.fn_signature)
            )
            print(Fore.GREEN + f"\nTool call dict: \n{validated_tool_call}")

            result = tool.run(**validated_tool_call["arguments"])
            print(Fore.GREEN + f"\nTool result: \n{result}")

            # Store the result using the tool call ID
            observations[validated_tool_call["id"]] = result

        return observations

    def run(
        self,
        conversation_id: str,
        messages: dict,
        max_rounds: int = 10,
        summarise: bool = False,
        save_file: bool = True
    ) -> str:
        """
        Executes a user interaction session, where the agent processes user input, generates responses,
        handles tool calls, and updates chat history until a final response is ready or the maximum
        number of rounds is reached.

        Args:
            user_msg (str): The user's input message to start the interaction.
            max_rounds (int, optional): Maximum number of interaction rounds the agent should perform. Default is 10.

        Returns:
            str: The final response generated by the agent after processing user input and any tool calls.
        """

        user_prompt = build_prompt_structure(
            prompt=messages[conversation_id][-1]["content"], role="user", tag="question"
        )
        global additional_constraints
        if self.tools:
            self.system_prompt += (
                "\n" + REACT_SYSTEM_PROMPT % self.add_tool_signatures() + (additional_constraints if self.add_constraints else "")
            )


        messages[conversation_id] = [build_prompt_structure(prompt=self.system_prompt, role="system")] + messages[conversation_id]
        messages[conversation_id][-1] = user_prompt

        # Summarising the context

        if (summarise):
            if (len(messages[conversation_id]) >= 6):
                _message = json.dumps(messages[conversation_id][1:-1])
                summarisation_messages = [
                    {"role": "system", "content": "Your job is to summarise the user's input in about 100 words"},
                    {"role": "user", "content": _message}
                ]
                summarised_context = completions_create(self.client, summarisation_messages)
                messages[conversation_id][1:-1] = [{"role": "assistant", "content": summarised_context}]

        if self.tools:
            # Run the ReAct loop for max_rounds
            for _ in range(max_rounds):

                completion = completions_create(self.client, messages[conversation_id])
                
                response = extract_tag_content(str(completion), "response")
                if response.found:
                    messages[conversation_id] = messages[conversation_id][1:]
                    messages[conversation_id] = ChatHistory(messages[conversation_id])
                    if (save_file): save_chat_history(messages)
                    return response.content[0]

                thought = extract_tag_content(str(completion), "thought")
                tool_calls = extract_tag_content(str(completion), "tool_call")

                update_chat_history(messages[conversation_id], completion, "assistant")

                if (thought.found): print(Fore.MAGENTA + f"\nThought: {thought.content[0]}")

                if tool_calls.found:
                    observations = self.process_tool_calls(tool_calls.content)
                    print(Fore.BLUE + f"\nObservations: {observations}")
                    update_chat_history(messages[conversation_id], f"{observations}", "user")
                    # chat_history_ids[conversation_id].append(user_prompt)

        # Save chat history after each interaction
        messages[conversation_id] = messages[conversation_id][1:]
        messages[conversation_id] = ChatHistory(messages[conversation_id])
        if (save_file): save_chat_history(messages)
        return completions_create(self.client, messages[conversation_id])
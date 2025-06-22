import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from colorama import Fore
from pathlib import Path
from agentic_patterns.utils.completions import ChatHistory

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
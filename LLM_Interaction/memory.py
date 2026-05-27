# Memory and conversation storage
import json
import os
from datetime import datetime

CONVERSATION_FILE = "data/conversation_history.json"

def save_conversation(user_message, agent_response):
    """Save conversation to file"""
    os.makedirs("data", exist_ok=True)
    
    history = load_conversation_history()
    
    history.append({
        "timestamp": datetime.now().isoformat(),
        "user": user_message,
        "agent": agent_response
    })
    
    with open(CONVERSATION_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def load_conversation_history():
    """Load conversation history from file"""
    if os.path.exists(CONVERSATION_FILE):
        try:
            with open(CONVERSATION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def clear_history():
    """Clear conversation history"""
    if os.path.exists(CONVERSATION_FILE):
        os.remove(CONVERSATION_FILE)
    print("Conversation history cleared")

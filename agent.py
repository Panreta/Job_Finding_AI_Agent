# Main agent orchestrator - this is what you run
import json
from llm import ask_llama
from tools import TOOLS, execute_tool
from memory import save_conversation, load_conversation_history

def run_agent():
    """Main agent loop"""
    print("Job Search Agent Started!")
    print("Type 'quit' to exit\n")
    
    conversation_history = load_conversation_history()
    
    while True:
        user_input = input("You: \n")
        
        if user_input.lower() == 'quit':
            print("Goodbye! Remember to rock today!")
            break
        
        prompt = build_prompt(user_input, conversation_history)
        
        response = ask_llama(prompt)
        
        # Check if LLM wants to use a tool
        if "[TOOL:" in response:
            tool_name, tool_args = parse_tool_call(response)
            
            tool_result = execute_tool(tool_name, tool_args)
            
            # Send result back to LLM
            followup_prompt = f"Tool '{tool_name}' returned: {tool_result}\n\nNow respond to the user."
            response = ask_llama(followup_prompt)
        
        print(f"Agent: {response}\n")
        
        # Save to memory
        save_conversation(user_input, response)
        conversation_history.append({"user": user_input, "agent": response})

def build_prompt(user_input, history):
    tools_description = "\n".join([f"- {name}: {info['description']}" for name, info in TOOLS.items()])
    
    history_text = "\n".join([f"User: {h['user']}\nAgent: {h['agent']}" for h in history[-5:]])
    
    prompt = f"""You are a job search assistant agent. You can use tools to help the user.

    Available tools:
    {tools_description}

    To use a tool, respond with: [TOOL: tool_name] {{"arg1": "value1", "arg2": "value2"}}

    Conversation history:
    {history_text}

    User: {user_input}
    Agent:"""
    
    return prompt

def parse_tool_call(response):
    """Extract tool name and arguments from LLM response"""
    try:
        # Simple parsing: [TOOL: search_jobs] {"keywords": "python", "location": "Seattle"}
        tool_part = response.split("[TOOL:")[1].split("]")[0].strip()
        args_part = response.split("]")[1].strip()

        tool_args = json.loads(args_part) if args_part else {}
        
        return tool_part, tool_args
    except:
        return None, {}

if __name__ == "__main__":
    run_agent()
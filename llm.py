"""
Ollama communication module.
Sends prompts to a local LLaMA model and returns the generated response.
"""

import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

def ask_llama(prompt, stream=True):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,"prompt": prompt,"stream": stream},
            timeout=120, #  "If Ollama doesn't respond within 120 seconds (2 minutes),
            # stop waiting and raise an error."
            stream=stream
        )
        
        if response.status_code == 200: # When you make an HTTP request, the server responds with a status code 

            # 404: Not Found, 500: Internal Server Error, 505: HTTP Version Not Supported
            full_response = ""
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    full_response += chunk.get("response", "")
                    if chunk.get("done"):
                        break
            return full_response.strip()
        else:
            return f"Error: Ollama returned status {response.status_code}"
    
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Is it running? (ollama serve)"
    except Exception as e:
        return f"Error: {str(e)}"

def test_ollama():
    """Test if Ollama is working"""
    prompt = "To be or not to be"
    response = ask_llama(prompt)
    print(f"Ollama test: {response}")
    return "working" in response.lower()

if __name__ == "__main__":
    if test_ollama():
        print("Ollama is working!")
    else:
        print("Ollama connection failed")
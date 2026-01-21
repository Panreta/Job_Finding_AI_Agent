# Ollama communication module
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

def ask_llama(prompt, stream=False):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": stream
            },
            timeout=120 #  "If Ollama doesn't respond within 120 seconds (2 minutes), stop waiting and raise an error."
        )
        
        if response.status_code == 200: # When you make an HTTP request, the server responds with a status code 

            # 404: Not Found, 500: Internal Server Error, 505: HTTP Version Not Supported
            result = response.json()
            return result.get('response', '').strip()
        else:
            return f"Error: Ollama returned status {response.status_code}"
    
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Is it running? (ollama serve)"
    except Exception as e:
        return f"Error: {str(e)}"

def test_ollama():
    """Test if Ollama is working"""
    response = ask_llama("Say 'Hello! I am working!' if you can read this.")
    print(f"Ollama test: {response}")
    return "working" in response.lower()

if __name__ == "__main__":
    # Test the connection
    if test_ollama():
        print("✓ Ollama is working!")
    else:
        print("✗ Ollama connection failed")
import requests
import json

# Configuration
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3"  # or "llama3"

class LLMService:
    def __init__(self):
        print(f"Initializing LLM Service using Ollama ({MODEL_NAME})...")
        self._check_ollama_connection()

    def _check_ollama_connection(self):
        try:
            # Check if model exists, if not, trigger pull (optional, or just let generate fail)
            # Simple check: just see if we can connect to tags endpoint
            requests.get("http://localhost:11434/api/tags")
            print("Connected to Ollama successfully.")
        except requests.exceptions.ConnectionError:
            print("WARNING: Could not connect to Ollama. Make sure it is running!")

    def generate_response(self, prompt: str, system_prompt: str = None):
        if not system_prompt:
            system_prompt = "You are a helpful legal assistant. Answer the question based on the provided context."
        
        full_prompt = f"<|system|>\n{system_prompt}<|end|>\n<|user|>\n{prompt}<|end|>\n<|assistant|>"
        
        payload = {
            "model": MODEL_NAME,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "num_ctx": 4096
            }
        }

        try:
            response = requests.post(OLLAMA_API_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
        except Exception as e:
            return f"Error communicating with Ollama: {str(e)}. Is Ollama running?"

llm_service = LLMService()

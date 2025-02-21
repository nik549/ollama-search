import requests
import json
from simplesearch import SimpleSearch

class ChatWrapper:
    def __init__(self):
        self.cloud_service_url = "http://localhost:8000"
        self.ollama_url = "http://localhost:11434/api/chat"
        self.available_models = self.get_available_models()
        self.current_model = None
        self.simple_search = None

    def get_available_models(self):
        """Fetch available models."""
        try:
            response = requests.get("http://localhost:11434/api/tags")
            response.raise_for_status()
            return [model['name'] for model in response.json()['models']]
        except Exception as e:
            print(f"Error getting models: {e}")
            return []

    def select_model(self):
        """Allow user to select a model."""
        if not self.available_models:
            print("No models available. Please install models first.")
            return False

        print("\nAvailable models:")
        for i, model in enumerate(self.available_models, 1):
            print(f"{i}. {model}")

        while True:
            try:
                choice = int(input("\nSelect model (number): "))
                if 1 <= choice <= len(self.available_models):
                    self.current_model = self.available_models[choice - 1]
                    print(f"Selected model: {self.current_model}")
                    self.simple_search = SimpleSearch(
                        self.cloud_service_url, self.ollama_url, self.current_model
                    )
                    return True
                print("Invalid selection. Try again.")
            except ValueError:
                print("Please enter a valid number.")

    def call_ollama(self, query):
        """Send regular queries directly to Ollama and stream response."""
        payload = {
            "model": self.current_model,
            "messages": [{"role": "user", "content": query}],
            "stream": True  # Enable streaming
        }
        try:
            with requests.post(
                self.ollama_url, json=payload, headers={"Content-Type": "application/json"}, stream=True
            ) as response:
                response.raise_for_status()
                print("\n", end="")  # Start new line before streaming
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        print(content, end="", flush=True)  # Print streaming output
                print("\n")  # Ensure the output ends cleanly
        except Exception as e:
            print(f"Error calling Ollama: {e}")

    def process_query(self, query):
        """Decide query handling method."""
        if query.startswith('/'):
            return self.simple_search.process_query(query)  # Handle special `/` queries
        return self.call_ollama(query)  # Send regular queries directly to Ollama

    def start_chat(self):
        """Start the chat loop."""
        if not self.select_model():
            return

        print("\nChat started. Type '//exit' to quit.")
        while True:
            try:
                query = input("\n>>> ")
                if query == "//exit":
                    print("Exiting...")
                    break

                if not query.strip():
                    continue

                print("\nProcessing...")
                self.process_query(query)

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"\nError: {e}")

if __name__ == "__main__":
    try:
        wrapper = ChatWrapper()
        wrapper.start_chat()
    except Exception as e:
        print(f"Initialization error: {e}")

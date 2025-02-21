import requests
import json
import re

class SimpleSearch:
    def __init__(self, cloud_service_url, ollama_url, current_model):
        self.cloud_service_url = cloud_service_url
        self.ollama_url = ollama_url
        self.current_model = current_model

    def call_ollama(self, prompt, stream=False):
        """Calls Ollama API and handles both streaming and non-streaming responses."""
        payload = {
            "model": self.current_model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": stream
        }
        try:
            if stream:
                with requests.post(
                    self.ollama_url, json=payload, headers={"Content-Type": "application/json"}, stream=True
                ) as response:
                    response.raise_for_status()
                    print("\n", end="")  # Ensure clean output before streaming
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            print(content, end="", flush=True)  # Print streamed content
                            full_response += content
                    print("\n")  # Ensure clean output after streaming
                    return full_response
            else:
                response = requests.post(
                    self.ollama_url, json=payload, headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                return result.get("message", {}).get("content", "")
        except Exception as e:
            print(f"Error calling Ollama: {e}")
            return ""

    def get_search_context(self, search_query):
        """Fetch search results from the cloud service and return URLs and summarized content."""
        try:
            response = requests.post(
                f"{self.cloud_service_url}/process",
                json={"query": search_query},
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("success"):
                return [], "No relevant information found."

            contexts = result.get('data', [])
            if not contexts:
                return [], "No relevant information found."

            urls = [context['url'] for context in contexts]
            context_str = "\n\n".join(
                f"{c['url']}\n{c['content']}" for c in contexts
            )

            return urls, context_str
        except Exception as e:
            return [], f"Error during search: {e}"

    def process_query(self, query):
        """Handles queries that start with '/' by generating search queries, fetching results, streaming summaries, and responding."""
        query = query[1:].strip()  # Remove the '/' and trim whitespace
        if not query:
            print("❌ Error: Query cannot be empty.")
            return None

        # Step 1: Generate 3 Google search queries using Ollama
        prompt_generate = (
            "Based on the following user query, generate three Google search queries "
            "that would help understand the query better. Provide each query enclosed in double quotes.\n\n"
            f"User query: {query}"
        )
        ollama_response = self.call_ollama(prompt_generate)

        # Extract search queries from Ollama's response
        search_queries = re.findall(r'"([^"]+)"', ollama_response)
        if len(search_queries) != 3:
            print("⚠️ Search queries not in expected format. Answering directly.")
            return self.call_ollama(query, stream=True)

        # Display "Generated search queries:"
        print("\n📌 **Generated search queries:**")
        for sq in search_queries:
            print(f"- {sq}")

        summaries = []
        formatted_answers = []

        # Step 2: Get search results and stream summaries
        for i, sq in enumerate(search_queries, 1):
            print(f"\n📖 **Google Query {i}:** {sq}")

            urls, context_str = self.get_search_context(sq)
            print("🔗 **Links:**")
            if urls:
                for url in urls:
                    print(f"- {url}")
            else:
                print("No links found.")

            # Start streaming summary immediately
            print("📝 **Summary:** ", end="", flush=True)
            summary = self.call_ollama(
                f"Summarize the following search results:\n\n{context_str}",
                stream=True
            )
            summaries.append(summary)

        # Step 3: Prepare the final prompt
        final_prompt = f"📌 **User Query:** {query}\n\n"
        for i, summary in enumerate(summaries, start=1):
            final_prompt += f"\n🔎 **Query {i}:** {search_queries[i-1]}\n📄 **Summary:** {summary}\n"
        final_prompt += "\n✍️ **Now, think deeply and provide a detailed answer based on the provided information.**"

        print("\n🤖 **Generating final response...**")
        return self.call_ollama(final_prompt, stream=True)  # STREAM FINAL ANSWER

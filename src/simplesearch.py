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
        """Fetch search results from the cloud service and return URLs and content."""
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
            # Extract just titles and snippets to reduce content size
            processed_content = []
            for c in contexts:
                # Extract first 2-3 sentences or ~150 characters max from content
                content_preview = ' '.join(c['content'].split('.')[:2]) + '.'
                if len(content_preview) > 150:
                    content_preview = content_preview[:147] + '...'
                processed_content.append(f"{c['url']}\n{content_preview}")
                
            context_str = "\n\n".join(processed_content)
            return urls, context_str
        except Exception as e:
            return [], f"Error during search: {e}"

    def process_query(self, query):
        """Handles queries starting with '/' by generating search queries and fetching condensed results."""
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

        # Step 2: Collect all search results in an optimized format
        all_urls = []
        all_contexts = []
        
        for i, sq in enumerate(search_queries, 1):
            print(f"\n📖 **Google Query {i}:** {sq}")

            urls, context_str = self.get_search_context(sq)
            all_urls.extend(urls)
            all_contexts.append(f"Search Query: {sq}\n{context_str}")
            
            print("🔗 **Links:**")
            if urls:
                for url in urls:
                    print(f"- {url}")
            else:
                print("No links found.")

        # Step 3: Prepare the final prompt with clear instructions to reduce hallucination
        final_prompt = (
            f"📌 **User Query:** {query}\n\n"
            f"📚 **Search Context:**\n\n{' '.join(all_contexts)}\n\n"
            f"🔍 **Instructions:**\n"
            f"1. Use ONLY information from the provided search results to answer the query\n"
            f"2. If the search results don't contain enough information, acknowledge this limitation\n"
            f"3. DO NOT make up information not present in the search results\n"
            f"4. Cite sources when possible using [URL] notation\n\n"
            f"✍️ **Please provide a factual answer to the original query based STRICTLY on the provided information.**"
        )

        print("\n🤖 **Generating final response...**")
        return self.call_ollama(final_prompt, stream=True)
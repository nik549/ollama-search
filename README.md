Ollama Search Integration
This project integrates multiple tools and services—including Ollama and Searxng—to provide a search solution for ollama.

Prerequisites
Before you begin, ensure you have the following installed and configured:

Ollama
Deno
Docker
Searxng
Ensure Searxng is running on port 3001 with JSON format enabled.
Installation
Clone the Repository

bash
Copy
Edit
git clone https://github.com/nik549/ollama-search-.git
Install Python Dependencies

Navigate to the project directory and install the required Python package:

bash
Copy
Edit
pip install requests
Running the Application
Make sure the prerequisites are running as specified:

Searxng is running on port 3001.
Ollama is active.
Then, run the project components in the following order:

Run the Deno Script

bash
Copy
Edit
deno run search.ts
Run the Python Application

bash
Copy
Edit
python app.py

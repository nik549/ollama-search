# Ollama Search Integration

This project integrates multiple tools and services—including Ollama and Searxng—to provide a search solution for ollama.

## Prerequisites

Before you begin, ensure you have the following installed and configured:

- **Ollama**
- **Deno**
- **Docker**
- **Searxng**  
  Ensure Searxng is running on port `3001` with JSON format enabled.

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/nik549/ollama-search.git
   ```

2. **Install Python Dependencies**

   Navigate to the project directory and install the required Python package:

   ```bash
   pip install requests
   ```

## Running the Application

Make sure the prerequisites are running as specified:

- **Searxng** is running on port `3001`.
- **Ollama** is active.

Then, run the project components in the following order:

1. **Run the Deno Script**

   ```bash
   deno run search.ts
   ```

2. **Run the Python Application**

   ```bash
   python app.py
   ```

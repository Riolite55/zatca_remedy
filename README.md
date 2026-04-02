# Remedy AI Agent MVP

This is a local AI MVP that bridges a custom Python agent with a mock BMC Remedy REST API using the Model Context Protocol (MCP). The agent leverages PydanticAI and Gemini to reason over ticket data securely and effectively.

## Architecture
1. **Mock Remedy API (`mock_remedy.py`)**: A local FastAPI server simulating a Remedy REST API. It serves JWT tokens and raw ticket JSON data.
2. **MCP Proxy (`remedy_mcp.py`)**: A `FastMCP` server bridging the AI with the internal API. Exposes the `get_all_tickets()` tool.
3. **Agent UI (`app.py`)**: A `Streamlit` interface integrating `PydanticAI` (powered by Gemini). It orchestrates tool-calling and user interaction.

## Getting Started

1. Set up your API key:
   - Edit the `.env` file and insert your actual `GEMINI_API_KEY`.

2. Run the MVP:
   ```bash
   ./start.sh
   ```

3. Open the Streamlit URL provided in the terminal (usually `http://localhost:8501`).

4. Ask questions! Some examples:
   - "How many open tickets do we have?"
   - "Give me a summary of tickets for Project_Alpha and highlight any blocked ones."
   - "Which tickets are High priority?"

## Troubleshooting
- **API Key Invalid:** Make sure your Gemini API Key in the `.env` file is correct and active.
- **Port Conflict:** Ensure port `8080` (for the mock server) and port `8501` (for Streamlit) are not currently in use by other processes.# zatca_remedy

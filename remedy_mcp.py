import os
import httpx
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

# We initialize FastMCP, which easily creates an MCP server exposing Python functions as tools
mcp = FastMCP("RemedyLocal")

REMEDY_URL = os.getenv("REMEDY_BASE_URL", "http://127.0.0.1:8080/api/arsys/v1")

async def get_auth_token() -> str:
    """Helper function to fetch an authentication token from the Remedy REST API."""
    login_url = REMEDY_URL.replace("/api/arsys/v1", "/api/jwt/login")
    async with httpx.AsyncClient() as client:
        # Provide dummy credentials for mock server
        data = {"username": "AgentUser", "password": "password"}
        response = await client.post(login_url, data=data)
        response.raise_for_status()
        # Clean the response. The FastAPI mock returns a JSON string like "mock-jwt-token-778899"
        # Real remedy returns plain text token
        return response.text.strip('"')

@mcp.tool()
async def get_all_tickets() -> str:
    """
    Fetches all incidents/tickets from the local Remedy system.
    Returns the raw JSON data of all incidents as a string, which can be filtered by the AI.
    """
    token = await get_auth_token()
    headers = {"Authorization": f"AR-JWT {token}"}
    
    async with httpx.AsyncClient() as client:
        # Standard endpoint for getting Incidents
        endpoint = f"{REMEDY_URL}/entry/HPD:IncidentInterface"
        response = await client.get(endpoint, headers=headers)
        response.raise_for_status()
        
        # We return the raw string so the LLM has all the data to filter and analyze.
        return response.text

if __name__ == "__main__":
    # Start the MCP server. `stdio` transport is the default for FastMCP.
    mcp.run()
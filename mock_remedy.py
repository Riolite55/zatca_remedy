from fastapi import FastAPI, HTTPException, Header
import uvicorn
from typing import Optional

app = FastAPI(title="Mock Remedy REST API")

MOCK_TOKEN = "mock-jwt-token-778899"

@app.post("/api/jwt/login")
async def login():
    # Remedy typically returns the token as a plain string in the response body
    return MOCK_TOKEN

@app.get("/api/arsys/v1/entry/HPD:IncidentInterface")
async def get_incidents(authorization: Optional[str] = Header(None)):
    # Simple validation of the AR-JWT token
    if not authorization or authorization != f"AR-JWT {MOCK_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Return a mocked set of tickets
    return {
        "entries": [
            {
                "values": {
                    "Incident Number": "INC000000000001",
                    "Status": "New",
                    "Description": "User cannot login to the VPN",
                    "Priority": "High",
                    "Categorization Tier 1": "Network",
                    "Project_ID": "Project_Alpha"
                }
            },
            {
                "values": {
                    "Incident Number": "INC000000000002",
                    "Status": "Assigned",
                    "Description": "Requesting access to Project Alpha resources",
                    "Priority": "Medium",
                    "Categorization Tier 1": "Access",
                    "Project_ID": "Project_Alpha"
                }
            },
            {
                "values": {
                    "Incident Number": "INC000000000003",
                    "Status": "Pending",
                    "Description": "Server performance degraded",
                    "Priority": "Critical",
                    "Categorization Tier 1": "Hardware",
                    "Project_ID": "Project_Beta"
                }
            },
            {
                "values": {
                    "Incident Number": "INC000000000004",
                    "Status": "Resolved",
                    "Description": "Password reset for active directory",
                    "Priority": "Low",
                    "Categorization Tier 1": "Account",
                    "Project_ID": "Project_Alpha"
                }
            },
            {
                "values": {
                    "Incident Number": "INC000000000005",
                    "Status": "Pending",
                    "Description": "Awaiting vendor response for replacement switch",
                    "Priority": "High",
                    "Categorization Tier 1": "Hardware",
                    "Project_ID": "Project_Alpha"
                }
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

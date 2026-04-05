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
    
    # Return a mocked set of tickets matching real Remedy column names
    return {
        "entries": [
            {
                "values": {
                    "INCIDENT_NUMBER": "INC678916",
                    "STATUS_DESCRIPTION": "Assigned",
                    "DESCRIPTION": "User cannot login to the VPN",
                    "PRIORITY_DESCRIPTION": "Medium",
                    "CATEGORIZATION_TIER_1": "Network",
                    "ASSIGNED_GROUP": "Service Desk"
                }
            },
            {
                "values": {
                    "INCIDENT_NUMBER": "INC666735",
                    "STATUS_DESCRIPTION": "In Progress",
                    "DESCRIPTION": "Requesting access to project resources",
                    "PRIORITY_DESCRIPTION": "Medium",
                    "CATEGORIZATION_TIER_1": "Application Support  - دعم التطبيقات",
                    "ASSIGNED_GROUP": "Nibras 1 - L2"
                }
            },
            {
                "values": {
                    "INCIDENT_NUMBER": "INC661217",
                    "STATUS_DESCRIPTION": "Resolved",
                    "DESCRIPTION": "Server performance degraded",
                    "PRIORITY_DESCRIPTION": "Low",
                    "CATEGORIZATION_TIER_1": "IT Infrastructure And Systems",
                    "ASSIGNED_GROUP": "E-invoicing L2"
                }
            },
            {
                "values": {
                    "INCIDENT_NUMBER": "INC700001",
                    "STATUS_DESCRIPTION": "Closed",
                    "DESCRIPTION": "Password reset for active directory",
                    "PRIORITY_DESCRIPTION": "Low",
                    "CATEGORIZATION_TIER_1": "Service Desk",
                    "ASSIGNED_GROUP": "Service Desk"
                }
            },
            {
                "values": {
                    "INCIDENT_NUMBER": "INC700002",
                    "STATUS_DESCRIPTION": "Canceled",
                    "DESCRIPTION": "Awaiting vendor response for replacement switch",
                    "PRIORITY_DESCRIPTION": "Medium",
                    "CATEGORIZATION_TIER_1": "IT Field Operations Support",
                    "ASSIGNED_GROUP": "Field Support - PNU"
                }
            }
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

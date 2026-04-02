import os
import sqlite3
import pandas as pd
import uuid
import json
from datetime import datetime
from typing import Literal, Optional, List, Any, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Remedy AI Analyst API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------
# Define the Structured Output Schema
# -----------------------------------------
class ChartDef(BaseModel):
    title: str = Field(description="The title of the visual element.")
    type: Literal["metric", "table", "bar", "pie", "line"] = Field(
        description="The type of visualization to render. Use 'metric' for single numbers, 'table' for raw rows, and others for charts."
    )
    sql_query: str = Field(description="A completely valid SQLite query that returns the exact data needed for this chart.")
    x_col: Optional[str] = Field(description="The exact name of the column in the SQL result to use for the X-axis (labels/categories). Required for bar, pie, and line charts.")
    y_col: Optional[str] = Field(description="The exact name of the column in the SQL result to use for the Y-axis (values/counts). Required for bar, pie, and line charts.")

class RemedyDashboard(BaseModel):
    message: str = Field(description="A brief analytical summary answering the user's question, placed at the top of the dashboard.")
    charts: List[ChartDef] = Field(description="A list of 1 to 3 charts/metrics to display to support the analysis.")

# -----------------------------------------
# PydanticAI Agent Setup
# -----------------------------------------
db_schema = """
TABLE: hpd_help_desk (BMC Remedy Incident Table)
- Entry_ID (TEXT PRIMARY KEY)
- Incident_ID (TEXT) e.g., 'INC000000000001'
- Submit_Date (DATETIME) e.g., '2023-10-25 14:00:00'
- Closed_Date (DATETIME)
- Target_Date (DATETIME) - Expected SLA resolution
- Status (TEXT) e.g., 'New', 'Assigned', 'In Progress', 'Pending', 'Resolved', 'Closed', 'Cancelled'
- Status_Reason (TEXT)
- Priority (TEXT) e.g., 'Critical', 'High', 'Medium', 'Low'
- Urgency (TEXT)
- Impact (TEXT)
- Assigned_Group (TEXT) e.g., 'Service Desk', 'Network Ops'
- Assignee_Login_ID (TEXT)
- First_Name (TEXT) - Customer First Name
- Last_Name (TEXT) - Customer Last Name
- Company (TEXT) - Customer Company
- VIP (TEXT) - e.g., 'Yes' or 'No'
- Incident_Type (TEXT)
- Reported_Source (TEXT)
- Person_ID (TEXT) - FK to ctm_people
- SLM_Status (TEXT) e.g., 'Service Targets Met', 'Service Targets Breached'

TABLE: hpd_worklog (Incident Activity/Notes)
- Work_Log_ID (TEXT PRIMARY KEY)
- Submit_Date (DATETIME)
- Submitter (TEXT)
- Incident_Number (TEXT) - FK to hpd_help_desk.Incident_ID
- Summary (TEXT)
- Notes (TEXT)
- Activity_Type (TEXT) e.g., 'General Information', 'Resolution Communications'

TABLE: ctm_people (Users/Staff Information)
- Person_ID (TEXT PRIMARY KEY)
- Login_ID (TEXT)
- Company (TEXT)
- Department (TEXT)
- First_Name (TEXT)
- Last_Name (TEXT)
- Email_Address (TEXT)
- Phone_Number_Business (TEXT)
- VIP (TEXT) - e.g., 'Yes' or 'No'

TABLE: ctm_support_group_assoc (Support Group Mappings)
- Support_Group_Assoc_LookUp_ID (TEXT PRIMARY KEY)
- Support_Group_Name (TEXT)
- Full_Name (TEXT)
- Person_ID (TEXT) - FK to ctm_people

TABLE: sys_status_reason (Lookup for Status Reasons)
- Status_Reason_ID (TEXT PRIMARY KEY)
- Status_Reason_Menu_Item (TEXT)
"""

agent = Agent(
    'gemini-2.5-flash',
    output_type=RemedyDashboard,
    system_prompt=(
        "You are an expert Data Analyst and AI Assistant for BMC Remedy ITSM. "
        "Your goal is to answer user questions about IT tickets, statuses, SLA delays, group performance, etc. "
        "You MUST translate their request into a valid, beautiful analytical dashboard response. "
        "You have access to a local SQLite database representing 5 relational tables: "
        "hpd_help_desk, hpd_worklog, ctm_people, ctm_support_group_assoc, and sys_status_reason.\n\n"
        f"Database Schema:\n{db_schema}\n\n"
        "Guidelines:\n"
        "1. You MUST use the `execute_sql` tool to query the database and find the EXACT numbers or insights BEFORE constructing your final response.\n"
        "2. The `message` field of your response MUST include the actual data values you found (e.g., 'There are exactly 13 pending tickets for SecOps.'). Do not just say 'Here is the summary'.\n"
        "3. Write highly accurate SQLite queries.\n"
        "4. JOIN tables when necessary (e.g. hpd_help_desk.Person_ID = ctm_people.Person_ID, or hpd_help_desk.Incident_ID = hpd_worklog.Incident_Number).\n"
        "5. If the user asks for a total count, include a 'metric' chart type (returns 1 row, 1 column).\n"
        "6. If they ask for a breakdown (e.g., 'by priority'), use a 'bar' or 'pie' chart.\n"
        "7. If they ask for a list of specific tickets, use a 'table'.\n"
        "8. Always use `AS count` or similar aliases in your SQL to make columns predictable.\n"
        "9. Do not wrap column names in quotes unless necessary."
    )
)

@agent.tool_plain
def execute_sql(query: str) -> str:
    """Execute a SQLite query against the Remedy ITSM database. Use this tool to fetch actual answers BEFORE generating the final response."""
    conn = sqlite3.connect('remedy_mock.db')
    try:
        df = pd.read_sql_query(query, conn)
        # Limit results to avoid massive JSON blobs causing token limits
        res = df.head(50).to_json(orient='records')
        return str(res) if res is not None else "[]"
    except Exception as e:
        return f"SQL Error: {e}"
    finally:
        conn.close()

# -----------------------------------------
# Helper Functions
# -----------------------------------------
def run_sql(query: str) -> List[Dict[str, Any]]:
    """Executes a SQL query against the mock Remedy database and returns a list of dicts."""
    conn = sqlite3.connect('remedy_mock.db')
    try:
        df = pd.read_sql_query(query, conn)
        return df.to_dict(orient='records')
    finally:
        conn.close()

# -----------------------------------------
# Authentication Dependencies
# -----------------------------------------
import jwt
from passlib.context import CryptContext
from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart, ToolCallPart, ToolReturnPart
import json

SECRET_KEY = "supersecretremedykey"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid auth credentials")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid auth credentials")

# -----------------------------------------
# API Endpoints
# -----------------------------------------
class ChatRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None

    
class ChartResponse(BaseModel):
    title: str
    type: str
    sql_query: str
    x_col: Optional[str]
    y_col: Optional[str]
    data: List[Dict[str, Any]] # Raw data for the frontend to render

class ChatResponse(BaseModel):
    message: str
    charts: List[ChartResponse]
    session_id: str

class AuthRequest(BaseModel):
    username: str
    password: str

@app.post("/api/auth/register")
async def register(user: AuthRequest):
    conn = sqlite3.connect('remedy_mock.db')
    c = conn.cursor()
    try:
        user_id = str(uuid.uuid4())
        hashed = get_password_hash(user.password)
        c.execute("INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
                  (user_id, user.username, hashed, datetime.now().isoformat()))
        conn.commit()
        token = jwt.encode({"sub": user_id}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer", "username": user.username}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()

@app.post("/api/auth/login")
async def login(user: AuthRequest):
    conn = sqlite3.connect('remedy_mock.db')
    c = conn.cursor()
    try:
        c.execute("SELECT id, password_hash FROM users WHERE username = ?", (user.username,))
        row = c.fetchone()
        if not row or not verify_password(user.password, row[1]):
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        token = jwt.encode({"sub": row[0]}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer", "username": user.username}
    finally:
        conn.close()

@app.get("/api/sessions")
async def get_sessions(user_id: str = Depends(get_current_user)):
    conn = sqlite3.connect('remedy_mock.db')
    try:
        df = pd.read_sql_query("SELECT id, title, created_at, updated_at FROM chat_sessions WHERE user_id = ? ORDER BY updated_at DESC", conn, params=[user_id])
        return df.to_dict(orient='records')
    finally:
        conn.close()

@app.get("/api/sessions/{session_id}")
async def get_session_history(session_id: str, user_id: str = Depends(get_current_user)):
    conn = sqlite3.connect('remedy_mock.db')
    try:
        # Verify ownership
        c = conn.cursor()
        c.execute("SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
        if not c.fetchone():
            raise HTTPException(status_code=403, detail="Not authorized or session doesn't exist")

        df = pd.read_sql_query("SELECT role, content, charts_json FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC", conn, params=[session_id])
        history_records = df.to_dict(orient='records')
        history = []
        for row in history_records:
            charts_json = row['charts_json']
            charts = json.loads(charts_json) if charts_json else []
            history.append({
                "role": row['role'],
                "content": row['content'],
                "charts": charts
            })
        return {"history": history}
    finally:
        conn.close()

# Simple in-memory mapping from session_id to Pydantic AI message history
session_histories: Dict[str, List[ModelMessage]] = {}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, user_id: str = Depends(get_current_user)):
    conn = sqlite3.connect('remedy_mock.db')
    c = conn.cursor()
    try:
        session_id = request.session_id
        is_new_session = False
        
        # 1. Initialize or find session
        if not session_id:
            is_new_session = True
            session_id = str(uuid.uuid4())
            # Use up to 10 words (or 60 chars) for a more descriptive title, allowing the UI to truncate naturally
            raw_title = request.prompt.strip()
            title = " ".join(raw_title.split()[:10])
            if len(title) > 60:
                title = title[:57] + "..."
            c.execute("INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                     (session_id, user_id, title, datetime.now().isoformat(), datetime.now().isoformat()))
        else:
            # Verify ownership
            c.execute("SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
            if not c.fetchone():
                raise HTTPException(status_code=403, detail="Not authorized")
            c.execute("UPDATE chat_sessions SET updated_at = ? WHERE id = ?", (datetime.now().isoformat(), session_id))

        # 2. Save User Prompt to DB
        msg_id = str(uuid.uuid4())
        c.execute("INSERT INTO chat_messages (id, session_id, role, content, charts_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                 (msg_id, session_id, "user", request.prompt, None, datetime.now().isoformat()))
        conn.commit()

        # 3. Run the agent with history (from in-memory cache for now to avoid reconstructing Pydantic Objects)
        history = session_histories.get(session_id, [])
        result = await agent.run(request.prompt, message_history=history)
        
        # Save updated history back to cache
        session_histories[session_id] = result.all_messages()
        dashboard: RemedyDashboard = result.output
        
        # 4. Execute SQL for each chart to populate data
        populated_charts = []
        for chart in dashboard.charts:
            try:
                data = run_sql(chart.sql_query)
            except Exception as e:
                print(f"SQL Error: {e} for query: {chart.sql_query}")
                data = [] 
                
            populated_charts.append(
                ChartResponse(
                    title=chart.title,
                    type=chart.type,
                    sql_query=chart.sql_query,
                    x_col=chart.x_col,
                    y_col=chart.y_col,
                    data=data
                )
            )
            
        # 5. Save AI Response to DB
        ai_msg_id = str(uuid.uuid4())
        charts_json = json.dumps([c.model_dump() for c in populated_charts])
        c.execute("INSERT INTO chat_messages (id, session_id, role, content, charts_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                 (ai_msg_id, session_id, "assistant", dashboard.message, charts_json, datetime.now().isoformat()))
        conn.commit()
            
        return ChatResponse(
            message=dashboard.message,
            charts=populated_charts,
            session_id=session_id
        )
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

class DashboardCreate(BaseModel):
    name: str

class DashboardUpdate(BaseModel):
    name: str

class SessionUpdate(BaseModel):
    title: str

class WidgetCreate(BaseModel):
    title: str
    type: str
    sql_query: str
    x_col: Optional[str] = None
    y_col: Optional[str] = None

class WidgetUpdate(BaseModel):
    title: str

@app.patch("/api/sessions/{session_id}")
async def update_session(session_id: str, update: SessionUpdate, user_id: str = Depends(get_current_user)):
    conn = sqlite3.connect('remedy_mock.db')
    c = conn.cursor()
    try:
        c.execute("SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
        if not c.fetchone():
            raise HTTPException(status_code=403, detail="Not authorized")
            
        c.execute("UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?", 
                  (update.title, datetime.now().isoformat(), session_id))
        conn.commit()
        return {"status": "success", "title": update.title}
    finally:
        conn.close()

@app.patch("/api/dashboards/{dashboard_id}")
async def update_dashboard(dashboard_id: str, update: DashboardUpdate, user_id: str = Depends(get_current_user)):
    conn = sqlite3.connect('remedy_mock.db')
    c = conn.cursor()
    try:
        c.execute("SELECT id FROM dashboards WHERE id = ? AND user_id = ?", (dashboard_id, user_id))
        if not c.fetchone():
            raise HTTPException(status_code=403, detail="Not authorized")
            
        c.execute("UPDATE dashboards SET name = ? WHERE id = ?", 
                  (update.name, dashboard_id))
        conn.commit()
        return {"status": "success", "name": update.name}
    finally:
        conn.close()

@app.post("/api/dashboards")
async def create_dashboard(request: DashboardCreate, user_id: str = Depends(get_current_user)):
    conn = sqlite3.connect('remedy_mock.db')
    c = conn.cursor()
    try:
        dash_id = str(uuid.uuid4())
        c.execute("INSERT INTO dashboards (id, user_id, name, created_at) VALUES (?, ?, ?, ?)", 
                 (dash_id, user_id, request.name, datetime.now().isoformat()))
        conn.commit()
        return {"id": dash_id, "name": request.name}
    finally:
        conn.close()

@app.get("/api/dashboards")
async def get_dashboards(user_id: str = Depends(get_current_user)):
    conn = sqlite3.connect('remedy_mock.db')
    try:
        df = pd.read_sql_query("SELECT id, name FROM dashboards WHERE user_id = ? ORDER BY created_at DESC", conn, params=[user_id])
        return df.to_dict(orient='records')
    finally:
        conn.close()

@app.post("/api/dashboards/{dashboard_id}/widgets")
async def add_widget(dashboard_id: str, widget: WidgetCreate, user_id: str = Depends(get_current_user)):
    conn = sqlite3.connect('remedy_mock.db')
    c = conn.cursor()
    try:
        # Verify dashboard ownership
        c.execute("SELECT id FROM dashboards WHERE id = ? AND user_id = ?", (dashboard_id, user_id))
        if not c.fetchone():
            raise HTTPException(status_code=403, detail="Not authorized")

        widget_id = str(uuid.uuid4())
        c.execute("""
            INSERT INTO dashboard_widgets 
            (id, dashboard_id, title, type, sql_query, x_col, y_col) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (widget_id, dashboard_id, widget.title, widget.type, widget.sql_query, widget.x_col, widget.y_col))
        conn.commit()
        return {"status": "success", "id": widget_id}
    finally:
        conn.close()

@app.patch("/api/dashboards/{dashboard_id}/widgets/{widget_id}")
async def update_widget(dashboard_id: str, widget_id: str, update: WidgetUpdate, user_id: str = Depends(get_current_user)):
    conn = sqlite3.connect('remedy_mock.db')
    c = conn.cursor()
    try:
        # Verify dashboard ownership
        c.execute("SELECT id FROM dashboards WHERE id = ? AND user_id = ?", (dashboard_id, user_id))
        if not c.fetchone():
            raise HTTPException(status_code=403, detail="Not authorized")

        c.execute("UPDATE dashboard_widgets SET title = ? WHERE id = ? AND dashboard_id = ?", 
                  (update.title, widget_id, dashboard_id))
        conn.commit()
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail="Widget not found")
        return {"status": "success", "title": update.title}
    finally:
        conn.close()

@app.get("/api/dashboards/{dashboard_id}/refresh")
async def refresh_dashboard(dashboard_id: str, user_id: str = Depends(get_current_user)):
    conn = sqlite3.connect('remedy_mock.db')
    try:
        # Verify ownership
        c = conn.cursor()
        c.execute("SELECT id FROM dashboards WHERE id = ? AND user_id = ?", (dashboard_id, user_id))
        if not c.fetchone():
            raise HTTPException(status_code=403, detail="Not authorized")

        df = pd.read_sql_query("SELECT * FROM dashboard_widgets WHERE dashboard_id = ?", conn, params=[dashboard_id])
        widgets = df.to_dict(orient='records')
        
        refreshed_widgets = []
        for w in widgets:
            try:
                data = run_sql(w['sql_query'])
            except Exception as e:
                print(f"Error refreshing widget {w['id']}: {e}")
                data = []
            w['data'] = data
            refreshed_widgets.append(w)
            
        return refreshed_widgets
    finally:
        conn.close()



@app.post("/api/simulate-activity")
async def simulate_activity():
    """Simulates Remedy activity so the dashboard refresh shows live data changing."""
    import random
    conn = sqlite3.connect('remedy_mock.db')
    c = conn.cursor()
    try:
        # 1. Close a random 'Pending' or 'In Progress' ticket
        c.execute("SELECT Incident_ID FROM hpd_help_desk WHERE Status IN ('Pending', 'In Progress') ORDER BY RANDOM() LIMIT 1")
        row = c.fetchone()
        if row:
            inc_id = row[0]
            c.execute("UPDATE hpd_help_desk SET Status = 'Resolved', Closed_Date = ? WHERE Incident_ID = ?", 
                     (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), inc_id))
            # Add a worklog for the resolution
            wl_id = f"WL{str(uuid.uuid4())[:8]}"
            c.execute("""
                INSERT INTO hpd_worklog (Work_Log_ID, Submit_Date, Submitter, Incident_Number, Summary, Notes, Activity_Type)
                VALUES (?, ?, 'System', ?, 'Auto-resolved by simulation', 'Fixed issue.', 'Resolution Communications')
            """, (wl_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), inc_id))

        # 2. Open a new 'Critical' ticket
        new_inc_id = f"INC{str(random.randint(900000, 999999)).zfill(12)}"
        c.execute("""
            INSERT INTO hpd_help_desk 
            (Entry_ID, Incident_ID, Submit_Date, Status, Priority, Summary, Incident_Type, Reported_Source)
            VALUES (?, ?, ?, 'New', 'Critical', 'URGENT: Database offline (Simulation)', 'User Service Restoration', 'System Alert')
        """, (f"ENT{random.randint(90000, 99999)}", new_inc_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        conn.commit()
        return {"status": "Simulated 1 resolved ticket and 1 new critical ticket."}
    finally:
        conn.close()

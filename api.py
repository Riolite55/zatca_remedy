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

# Auto-setup database on import (creates app tables + imports Excel data if needed)
from setup_db import create_db as _setup_db, DB_PATH as _DB_PATH
if not os.path.exists(_DB_PATH):
    _setup_db()

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
    follow_up: str = Field(description="A single natural follow-up question that logically continues from the current analysis. This will be appended to your message, so make it relevant and specific.")

# -----------------------------------------
# PydanticAI Agent Setup
# -----------------------------------------
db_schema = """
TABLE: hpd_help_desk (BMC Remedy Incident Table — 2000 real tickets, single table)

-- Identity & Source
- TICKET_SOURCE (TEXT)
- ENTRY_ID (TEXT) - Internal entry ID
- INCIDENT_NUMBER (TEXT) e.g., 'INC678916'

-- Submitter & Dates
- SUBMITTER (TEXT)
- ORIGINAL_DATE (INTEGER)
- SUBMIT_DATE (TIMESTAMP)
- SUBMIT_DATE_DATE (TIMESTAMP) - Date-only version
- SUBMIT_DATE_TIMESTAMP (TEXT)
- LAST_GROUP_ASSIGNED_DATE (REAL)
- LAST_GROUP_ASSIGNED_DATE_DATE (TIMESTAMP)
- LAST_GROUP_ASSIGNED_DATE_TIMESTAMP (TEXT)
- REPORTED_DATE (INTEGER)
- REPORTED_DATE_DATE (TIMESTAMP)
- REPORTED_DATE_TIMESTAMP (TEXT)

-- Modification
- LAST_MODIFIED_BY (TEXT)
- LAST_MODIFIED_DATE (INTEGER)
- LAST_MODIFIED_DATE_DATE (TIMESTAMP)
- LAST_MODIFIED_DATE_TIMESTAMP (TEXT)

-- Status & Classification
- STATUS (INTEGER) - Numeric code. Use STATUS_DESCRIPTION for text.
- STATUS_DESCRIPTION (TEXT) e.g., 'Assigned', 'In Progress', 'Resolved', 'Closed', 'Canceled'
- PREVIOUSSTATUS (REAL)
- STATUS_REASON (REAL)
- STATUS_REASON_DESC (TEXT)
- PRIORITY (INTEGER) - Numeric code. Use PRIORITY_DESCRIPTION for text.
- PRIORITY_DESCRIPTION (TEXT) e.g., 'Medium', 'Low'
- PRIORITY_WEIGHT (INTEGER)
- URGENCY (INTEGER) - Numeric code (3000, 4000)
- IMPACT (INTEGER) - Numeric code (3000, 4000)
- CATEGORIZATION_TIER_1 (TEXT) e.g., 'Application Support', 'Service Desk', 'Network'
- CATEGORIZATION_TIER_2 (TEXT)
- CATEGORIZATION_TIER_3 (TEXT)
- PRODUCT_CATEGORIZATION_TIER_1 (TEXT)
- PRODUCT_CATEGORIZATION_TIER_2 (TEXT)
- PRODUCT_CATEGORIZATION_TIER_3 (TEXT)
- REPORTED_SOURCE (INTEGER) - Numeric code. Use REPORTED_SOURCE_DESC for text.
- REPORTED_SOURCE_DESC (TEXT) e.g., 'CRM', 'Diwan', 'Web', 'Email', 'SolarWinds', 'Systems Management'
- TICKETTYPE (INTEGER)
- SERVICE_TYPE (INTEGER)
- CURRENTSTAGENUMBER (INTEGER)
- STAGECONDITION (TEXT)
- GAZT_CAN_UPDATE_PRIORITY (REAL)
- GAZT_COUNTED__C (INTEGER)
- GAZT_CURRENTINCIDENTSCOUNT2 (REAL)

-- Description & Resolution
- DESCRIPTION (TEXT) - Ticket description/summary
- DETAILED_DECRIPTION (TEXT)
- RESOLUTION (TEXT)
- RESOLUTION_CATEGORY (TEXT)
- REASON_DESCRIPTION (TEXT)
- REASON_CODE (TEXT)

-- Assignment
- ASSIGNED_GROUP (TEXT) e.g., 'Service Desk', 'E-invoicing L2', 'Nibras 1 - L2'
- ASSIGNED_GROUP_ID (TEXT)
- ASSIGNEE (TEXT) - Assigned person name
- ASSIGNEE_LOGIN_ID (TEXT)
- ASSIGNEE_ID (TEXT)
- ASSIGNEE_GROUPS (TEXT)
- ASSIGNEE_SELECT_FORM (TEXT)
- ASSIGNED_SUPPORT_COMPANY (TEXT)
- ASSIGNED_SUPPORT_ORGANIZATION (TEXT)
- OWNER_GROUP (TEXT)
- OWNER_GROUP_ID (TEXT)
- OWNER_SUPPORT_COMPANY (TEXT)
- OWNER_SUPPORT_ORGANIZATION (TEXT)
- SUPPORT_GROUP_ROLE (TEXT)
- ENABLE_ASSIGNMENT_ENGINE (INTEGER)
- ASSIGN_TO_VENDOR (INTEGER)
- ESCHAT_SET_AUTO_ASSIGN (INTEGER)

-- Customer / Requester Info
- FIRST_NAME (TEXT)
- LAST_NAME (TEXT)
- REQUESTER_NAME (TEXT) - Full requester name
- COMPANY (TEXT)
- ORGANIZATION (TEXT)
- CONTACT_COMPANY (TEXT)
- CONTACT_CLIENT_TYPE (INTEGER)
- CONTACT_SENSITIVITY (INTEGER)
- COUNTRY (TEXT)
- STATE_PROVINCE (REAL)
- CITY (TEXT)
- REGION (TEXT)
- SITE (TEXT)
- SITE_ID (TEXT)
- SITE_GROUP (TEXT)
- PERSON_ID (TEXT)
- LOGIN_ID (TEXT)
- CUSTOMER_LOGIN_ID (TEXT)
- CORPORATE_ID (TEXT)
- INTERNET_E_MAIL (TEXT)
- PHONE_NUMBER (TEXT)
- VIP (INTEGER) - 0 or 1
- FLAG_CREATE_REQUEST (INTEGER)

-- Direct Contact Info
- DIRECT_CONTACT_FIRST_NAME (TEXT)
- DIRECT_CONTACT_LAST_NAME (TEXT)
- DIRECT_CONTACT_COMPANY (TEXT)
- DIRECT_CONTACT_ORGANIZATION (TEXT)
- DIRECT_CONTACT_PHONE_NUMBER (TEXT)
- DIRECT_CONTACT_SITE (TEXT)
- DIRECT_CONTACT_PERSON_ID (TEXT)
- DIRECT_CONTACT_REGION (TEXT)
- DIRECT_CONTACT_SITE_GROUP (TEXT)
- DIRECT_CONTACT_LOGIN_ID (TEXT)
- DIRECT_CONTACT_INTERNET_E_MAIL (TEXT)
- DIRECT_CONTACT_CORPORATE_ID (TEXT)

-- SLA & SLM
- SLM_STATUS (INTEGER) - Numeric code. Use SLM_STATUS_DESCRIPTION for text.
- SLM_STATUS_DESCRIPTION (TEXT) e.g., 'Within Service Target', 'Service Target Breached'
- SLM_PRIORITY (INTEGER)
- SLA_RESPONSE_STATUS (TEXT) e.g., 'Met', 'Missed', 'In Process', 'Missed Goal'
- SLA_RESOLUTION_STATUS (TEXT) e.g., 'Met', 'Missed', 'In Process', 'Missed Goal'
- TCS_SLA_RESPONSE_STATUS (TEXT)
- TCS_SLA_RESOLUTION_STATUS (TEXT)
- SLA_RES_BUSINESS_HOUR_SECONDS (INTEGER)
- SLA_RESPONDED (REAL)
- SLA_HOLD (INTEGER)
- OLA_HOLD (INTEGER)
- SLMEVENTLOOKUPTBLKEYWORD (TEXT)
- SLMLOOKUPTBLKEYWORD (TEXT)
- LOOKUPKEYWORD (TEXT)
- ONWER_GROUP_USES_SLA (REAL)

-- Work In Progress Dates
- FIRSTWIPDATE (REAL)
- FIRSTWIPDATE_DATE (TIMESTAMP)
- FIRSTWIPDATE_TIMESTAMP (TEXT)
- LASTWIPDATE (REAL)
- LASTWIPDATE_DATE (TIMESTAMP)
- LASTWIPDATE_TIMESTAMP (TEXT)

-- Resolution & Closure Dates
- LAST_RESOLVED_DATE (REAL)
- LAST_RESOLVED_DATE_DATE (TIMESTAMP)
- LAST_RESOLVED_DATE_TIMESTAMP (TEXT)
- CLOSED_DATE (REAL)
- CLOSED_DATE_DATE (TIMESTAMP)
- CLOSED_DATE_TIMESTAMP (TEXT)
- RE_OPENED_DATE (REAL)
- RE_OPENED_DATE_DATE (TIMESTAMP)
- RE_OPENED_DATE_TIMESTAMP (TEXT)
- REOPEN_DATE (TIMESTAMP)

-- Transfers & Escalation
- GROUP_TRANSFERS (INTEGER)
- TOTAL_TRANSFERS (INTEGER)
- INDIVIDUAL_TRANSFERS (INTEGER)
- TOTAL_ESCALATION_LEVEL (INTEGER)
- TOTAL_OLA_RESOLUTION_ESC_LEVEL (INTEGER)
- TOTAL_OLA_ACKNOWLEDGEESC_LEVEL (INTEGER)
- ESCALATED_ (INTEGER)
- REASSIGNED_FROM_DIFFRENT_ORGAN (INTEGER)
- PREV_SUPPORT_ORGANIZATION (TEXT)
- FIRST_SUPPORT_ORGANIZATION (TEXT)
- ORGANIZATION_REASSIGN_DATE (TIMESTAMP)
- ORGANIZATION_REASSIGN_DATE_DATE (TIMESTAMP)
- ORGANIZATION_REASSIGN_DATE_TIMESTAMP (TEXT)

-- Aging & Reopen
- INCIDENT_AGING (INTEGER) - Age in days
- INCIDENT_AGING_HOUR (INTEGER)
- INCIDENT_AGING_MIN (INTEGER)
- REOPEN_COUNT (INTEGER)
- INC_REOPEN_COUNT (INTEGER)

-- Effort & Time
- EFFORTDURATIONHOUR (REAL)
- EFFORT_TIME_SPENT_MINUTES (INTEGER)
- TOTAL_TIME_SPENT (INTEGER)
- INCAUTOCLOSERESOLVED_SEC (INTEGER)
- LAST_DATE_DURATION_CALCULATED (INTEGER)
- LAST_DATE_D_C_DATE (TIMESTAMP)
- LAST_DATE_D_C_TIMESTAMP (TEXT)

-- Escalation Notifications
- ASSIGNEE_REMINDER_SENT (TEXT)
- SECTION_HEAD_ESCALATION_SENT (TEXT)
- DIRECTOR_ESCALATION_SENT (TEXT)

-- Communication Counts
- OUTBOUND (INTEGER)
- INBOUND (INTEGER)

-- Template & Wizard
- HPD_TEMPLATE_ID (TEXT)
- Z1D_TEMPLATE_NAME (TEXT)
- CREATED_FROM_TEMPLATE (INTEGER)
- CREATED_FROM_FLAG (REAL)
- ABYDOS_USE_WIZARD_ (INTEGER)
- ABYDOS_TASKS_GENERATED (INTEGER)
- ABYDOS_AUDITFLAG (INTEGER)
- CREATE_IMPACTED_AREA_FROM_CUST (INTEGER)
- SHOW_FOR_PROCESS (TEXT)
- Z1D_VISPROCESSFLOWVIEW (TEXT)

-- Miscellaneous
- DR (INTEGER)
- EH (INTEGER)
- RETURN_CODE (REAL)
- UNKNOWNUSER (INTEGER)
- WEB_INCIDENT_ID (TEXT)
- TOTAL_FIELDS_COUNT (INTEGER)
- Z1D_TOTALCRITICALINCIDENTSCOUN (REAL)
- SRID (TEXT)
- SRD_INSTANCE_ID (TEXT)
- INFRASTRUCTUREEVENTTYPE (INTEGER)
- RELATED_INC (REAL)
- RELATED_PBI (REAL)
- RELATED_CRQ (REAL)
- SECURITY_TECHNOLOGY (TEXT)

-- Port / Location
- PORT_REGION (TEXT)
- PORT_CLASSFICATION (TEXT)
- PORT_NAME (TEXT)

IMPORTANT: STATUS, PRIORITY, URGENCY, IMPACT, SLM_STATUS, REPORTED_SOURCE, and VIP are numeric codes.
Always use the corresponding _DESCRIPTION / _DESC columns for human-readable text in WHERE clauses and display.
"""

agent = Agent(
    'gemini-2.5-flash',
    output_type=RemedyDashboard,
    system_prompt=(
        "You are an expert Data Analyst and AI Assistant for BMC Remedy ITSM. "
        "Your goal is to answer user questions about IT tickets, statuses, SLA delays, group performance, etc. "
        "You MUST translate their request into a valid, beautiful analytical dashboard response. "
        "You have access to a local SQLite database with a single table: hpd_help_desk (2000 real incident tickets).\n\n"
        f"Database Schema:\n{db_schema}\n\n"
        "Guidelines:\n"
        "1. You MUST use the `execute_sql` tool to query the database and find the EXACT numbers or insights BEFORE constructing your final response.\n"
        "2. The `message` field of your response MUST include the actual data values you found (e.g., 'There are exactly 13 pending tickets for SecOps.'). Do not just say 'Here is the summary'.\n"
        "3. Write highly accurate SQLite queries against the single hpd_help_desk table.\n"
        "4. STATUS, PRIORITY, URGENCY, IMPACT, SLM_STATUS, REPORTED_SOURCE, and VIP are numeric codes. Always use the _DESCRIPTION/_DESC columns for filtering and display (e.g., STATUS_DESCRIPTION = 'Closed', not STATUS = 'Closed').\n"
        "5. If the user asks for a total count, include a 'metric' chart type (returns 1 row, 1 column).\n"
        "6. If they ask for a breakdown (e.g., 'by priority'), use a 'bar' or 'pie' chart.\n"
        "7. If they ask for a list of specific tickets, use a 'table'.\n"
        "8. Always use `AS count` or similar aliases in your SQL to make columns predictable.\n"
        "9. Do not wrap column names in quotes unless necessary.\n"
        "10. You MUST always include a single relevant follow-up question in the `follow_up` field. It should logically follow from the current analysis — the one question the user would most naturally want to ask next. IMPORTANT: The follow-up is displayed separately by the UI — do NOT mention it in your `message` field. Your message should only contain the analytical answer."
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
        df = df.fillna("")  # Replace NaN with empty string for JSON safety
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

def get_user_info(user_id: str) -> Dict[str, Any]:
    """Get role and department for a user."""
    conn = sqlite3.connect('remedy_mock.db')
    try:
        c = conn.cursor()
        c.execute("SELECT role, department FROM users WHERE id = ?", (user_id,))
        row = c.fetchone()
        if not row:
            return {"role": "admin", "department": None}
        return {"role": row[0], "department": row[1]}
    finally:
        conn.close()

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
    follow_up: str = ""

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
        c.execute("INSERT INTO users (id, username, password_hash, role, department, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_id, user.username, hashed, "admin", None, datetime.now().isoformat()))
        conn.commit()
        token = jwt.encode({"sub": user_id}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer", "username": user.username, "role": "admin", "department": None}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()

@app.post("/api/auth/login")
async def login(user: AuthRequest):
    conn = sqlite3.connect('remedy_mock.db')
    c = conn.cursor()
    try:
        c.execute("SELECT id, password_hash, role, department FROM users WHERE username = ?", (user.username,))
        row = c.fetchone()
        if not row or not verify_password(user.password, row[1]):
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        token = jwt.encode({"sub": row[0]}, SECRET_KEY, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer", "username": user.username, "role": row[2], "department": row[3]}
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
            charts = json.loads(charts_json) if isinstance(charts_json, str) else []
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

        # 3. Run the agent with history, injecting department context if applicable
        user_info = get_user_info(user_id)
        department = user_info.get("department")
        prompt = request.prompt
        if department:
            dept_display = department.replace("_", " ")
            prompt = f"[STRICT ACCESS CONTROL: This user is a manager of the '{department}' department ONLY. You MUST always include WHERE ASSIGNED_GROUP = '{department}' in every SQL query. If the user asks about other departments, groups, or data outside '{department}', politely decline and say: 'You only have access to {dept_display} data. Please contact an administrator for cross-department analytics.' NEVER generate SQL without filtering by ASSIGNED_GROUP = '{department}'.]\n\n{request.prompt}"

        history = session_histories.get(session_id, [])
        result = await agent.run(prompt, message_history=history)
        
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
            session_id=session_id,
            follow_up=dashboard.follow_up
        )
        
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
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



@app.get("/api/persona/kpis")
async def get_persona_kpis(user_id: str = Depends(get_current_user)):
    """Returns predefined KPI data scoped to the user's department (or global for admin)."""
    user_info = get_user_info(user_id)
    department = user_info["department"]
    conn = sqlite3.connect('remedy_mock.db')
    try:
        if department:
            # Scoped KPIs for department manager
            df_total = pd.read_sql_query("SELECT COUNT(*) as value FROM hpd_help_desk WHERE ASSIGNED_GROUP = ?", conn, params=[department])
            df_open = pd.read_sql_query("SELECT COUNT(*) as value FROM hpd_help_desk WHERE ASSIGNED_GROUP = ? AND STATUS_DESCRIPTION NOT IN ('Closed','Resolved','Canceled')", conn, params=[department])
            df_sla_within = pd.read_sql_query("SELECT COUNT(*) as value FROM hpd_help_desk WHERE ASSIGNED_GROUP = ? AND SLM_STATUS_DESCRIPTION = 'Within Service Target'", conn, params=[department])
            df_sla_breached = pd.read_sql_query("SELECT COUNT(*) as value FROM hpd_help_desk WHERE ASSIGNED_GROUP = ? AND SLM_STATUS_DESCRIPTION = 'Service Target Breached'", conn, params=[department])
            df_top_assignee = pd.read_sql_query("SELECT ASSIGNEE as name, COUNT(*) as count FROM hpd_help_desk WHERE ASSIGNED_GROUP = ? AND ASSIGNEE IS NOT NULL AND ASSIGNEE != '' GROUP BY ASSIGNEE ORDER BY count DESC LIMIT 1", conn, params=[department])

            total = int(df_total.iloc[0]['value'])
            sla_within = int(df_sla_within.iloc[0]['value'])
            sla_breached = int(df_sla_breached.iloc[0]['value'])
            sla_total = sla_within + sla_breached
            sla_rate = round((sla_within / sla_total * 100), 1) if sla_total > 0 else 100.0

            kpis = [
                {"label": "Total Tickets", "value": total, "type": "number"},
                {"label": "Open Tickets", "value": int(df_open.iloc[0]['value']), "type": "number"},
                {"label": "SLA Met Rate", "value": f"{sla_rate}%", "type": "percentage"},
                {"label": "SLA Breaches", "value": sla_breached, "type": "number"},
                {"label": "Top Assignee", "value": f"{df_top_assignee.iloc[0]['name'].strip()} ({int(df_top_assignee.iloc[0]['count'])})" if not df_top_assignee.empty else "N/A", "type": "text"},
            ]
        else:
            # Global KPIs for admin
            df_total = pd.read_sql_query("SELECT COUNT(*) as value FROM hpd_help_desk", conn)
            df_open = pd.read_sql_query("SELECT COUNT(*) as value FROM hpd_help_desk WHERE STATUS_DESCRIPTION NOT IN ('Closed','Resolved','Canceled')", conn)
            df_sla_breached = pd.read_sql_query("SELECT COUNT(*) as value FROM hpd_help_desk WHERE SLM_STATUS_DESCRIPTION = 'Service Target Breached'", conn)
            df_top_group = pd.read_sql_query("SELECT ASSIGNED_GROUP as name, COUNT(*) as count FROM hpd_help_desk GROUP BY ASSIGNED_GROUP ORDER BY count DESC LIMIT 1", conn)
            df_breach_group = pd.read_sql_query("SELECT ASSIGNED_GROUP as name, COUNT(*) as count FROM hpd_help_desk WHERE SLM_STATUS_DESCRIPTION = 'Service Target Breached' GROUP BY ASSIGNED_GROUP ORDER BY count DESC LIMIT 1", conn)

            kpis = [
                {"label": "Total Tickets", "value": int(df_total.iloc[0]['value']), "type": "number"},
                {"label": "Open Tickets", "value": int(df_open.iloc[0]['value']), "type": "number"},
                {"label": "SLA Breaches", "value": int(df_sla_breached.iloc[0]['value']), "type": "number"},
                {"label": "Busiest Group", "value": f"{df_top_group.iloc[0]['name']} ({int(df_top_group.iloc[0]['count'])})" if not df_top_group.empty else "N/A", "type": "text"},
                {"label": "Top Breaching Group", "value": f"{df_breach_group.iloc[0]['name']} ({int(df_breach_group.iloc[0]['count'])})" if not df_breach_group.empty else "None", "type": "text"},
            ]

        return {"kpis": kpis, "department": department, "role": user_info["role"]}
    finally:
        conn.close()

@app.get("/api/persona/suggestions")
async def get_persona_suggestions(user_id: str = Depends(get_current_user)):
    """Returns predefined suggested questions based on user's role/department."""
    user_info = get_user_info(user_id)
    department = user_info["department"]

    if department:
        dept_display = department.replace("_", " ")
        suggestions = [
            f"How many {dept_display} tickets are still open?",
            f"Show me ticket volume by assignee for my team",
            f"Which tickets have breached SLA in my department?",
            f"Break down {dept_display} tickets by status",
            f"List recent resolved tickets in my department",
        ]
    else:
        suggestions = [
            "Show me ticket breakdown by department",
            "Which groups have SLA breaches?",
            "What's the overall ticket status distribution?",
            "Show me the top 10 oldest unresolved tickets",
            "Compare SLA performance across all groups",
        ]

    return {"suggestions": suggestions, "department": department, "role": user_info["role"]}

@app.post("/api/simulate-activity")
async def simulate_activity():
    """Simulates Remedy activity so the dashboard refresh shows live data changing."""
    import random
    conn = sqlite3.connect('remedy_mock.db')
    c = conn.cursor()
    try:
        # 1. Resolve a random 'Assigned' or 'In Progress' ticket
        c.execute("SELECT INCIDENT_NUMBER FROM hpd_help_desk WHERE STATUS_DESCRIPTION IN ('Assigned', 'In Progress') ORDER BY RANDOM() LIMIT 1")
        row = c.fetchone()
        if row:
            inc_num = row[0]
            c.execute("""UPDATE hpd_help_desk
                         SET STATUS = 4, STATUS_DESCRIPTION = 'Resolved',
                             CLOSED_DATE_DATE = ?, LAST_RESOLVED_DATE_DATE = ?
                         WHERE INCIDENT_NUMBER = ?""",
                     (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S'), inc_num))

        # 2. Open a new ticket
        new_inc_num = f"INC{random.randint(900000, 999999)}"
        c.execute("""
            INSERT INTO hpd_help_desk
            (ENTRY_ID, INCIDENT_NUMBER, SUBMIT_DATE, SUBMIT_DATE_DATE,
             STATUS, STATUS_DESCRIPTION, PRIORITY, PRIORITY_DESCRIPTION,
             DESCRIPTION, REPORTED_SOURCE_DESC)
            VALUES (?, ?, ?, ?, 1, 'Assigned', 2, 'Medium',
                    'URGENT: Database offline (Simulation)', 'Web')
        """, (f"ENT{random.randint(90000, 99999)}", new_inc_num,
              datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
              datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

        conn.commit()
        return {"status": "Simulated 1 resolved ticket and 1 new ticket."}
    finally:
        conn.close()

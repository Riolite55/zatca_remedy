import streamlit as st
import os
import sqlite3
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from pydantic_ai import Agent

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Remedy Analyst AI (PoC)", page_icon="📊", layout="wide")

# Check for API Key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_gemini_api_key_here":
    st.warning("⚠️ Please set your GEMINI_API_KEY in the .env file.")
    st.stop()
os.environ["GOOGLE_API_KEY"] = api_key

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
        "1. Write highly accurate SQLite queries.\n"
        "2. JOIN tables when necessary (e.g. hpd_help_desk.Person_ID = ctm_people.Person_ID, or hpd_help_desk.Incident_ID = hpd_worklog.Incident_Number).\n"
        "3. If the user asks for a total count, include a 'metric' chart type (returns 1 row, 1 column).\n"
        "4. If they ask for a breakdown (e.g., 'by priority'), use a 'bar' or 'pie' chart.\n"
        "5. If they ask for a list of specific tickets, use a 'table'.\n"
        "6. Always use `AS count` or similar aliases in your SQL to make columns predictable.\n"
        "7. Do not wrap column names in quotes unless necessary."
    )
)

# -----------------------------------------
# Helper Functions
# -----------------------------------------
def run_sql(query: str) -> pd.DataFrame:
    """Executes a SQL query against the mock Remedy database and returns a Pandas DataFrame."""
    conn = sqlite3.connect('remedy_mock.db')
    try:
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()

# Initialize session state for memory
if "pydantic_messages" not in st.session_state:
    st.session_state.pydantic_messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------------------
# Streamlit UI
# -----------------------------------------
st.title("📊 Remedy ITSM Analytics PoC (Text-to-SQL)")
st.markdown("Ask anything about your tickets. The AI will instantly generate SQL queries, fetch the data, and build an interactive dashboard!")

# Sidebar Schema
with st.sidebar:
    st.header("Database Schema")
    st.code(db_schema, language='sql')
    st.caption("This is a simplified representation of the BMC Remedy HPD:Help Desk form.")

# Suggested Prompts
st.markdown("### Try asking:")
cols = st.columns(4)
prompts = [
    "Show me a breakdown of all Open vs Resolved tickets in a pie chart.",
    "Which Support Group has the most breached SLAs?",
    "Show me the count of High and Critical priority tickets that are currently 'Pending'.",
    "List the top 5 oldest unresolved tickets."
]
for i, col in enumerate(cols):
    if col.button(prompts[i], key=f"btn_{i}"):
        st.session_state.current_prompt = prompts[i]

def render_dashboard(dashboard: RemedyDashboard):
    """Helper function to render the UI components for a RemedyDashboard"""
    st.write(dashboard.message)
    
    if dashboard.charts:
        chart_cols = st.columns(len(dashboard.charts))
        
        for idx, chart in enumerate(dashboard.charts):
            with chart_cols[idx]:
                st.subheader(chart.title)
                
                try:
                    df = run_sql(chart.sql_query)
                    
                    if chart.type == 'metric':
                        value = df.iloc[0, 0] if not df.empty else 0
                        st.metric(label="", value=value)
                        
                    elif chart.type == 'table':
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                    elif chart.type in ['bar', 'pie', 'line']:
                        if df.empty:
                            st.warning("No data found for this chart.")
                        else:
                            x = chart.x_col if chart.x_col in df.columns else df.columns[0]
                            y = chart.y_col if chart.y_col in df.columns else df.columns[1]
                            
                            if chart.type == 'bar':
                                fig = px.bar(df, x=x, y=y)
                            elif chart.type == 'pie':
                                fig = px.pie(df, names=x, values=y, hole=0.3)
                            else: 
                                fig = px.line(df, x=x, y=y)
                                
                            st.plotly_chart(fig, use_container_width=True)
                except Exception as sql_e:
                    st.error(f"SQL Error: {sql_e}")
                
                with st.expander("View Generated SQL"):
                    st.code(chart.sql_query, language='sql')

# Render historical chats
for turn in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(turn["user"])
    with st.chat_message("assistant"):
        render_dashboard(turn["dashboard"])

user_input = st.chat_input("Enter your analytical question here...")

if "current_prompt" in st.session_state:
    user_input = st.session_state.current_prompt
    del st.session_state.current_prompt

if user_input:
    st.chat_message("user").write(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("Generating SQL and analyzing Remedy data..."):
            try:
                # Run the agent using the accumulated message history
                result = agent.run_sync(user_input, message_history=st.session_state.pydantic_messages)
                dashboard: RemedyDashboard = result.output
                
                # Update the message history with this turn so context is preserved for the next question
                st.session_state.pydantic_messages = result.all_messages()
                
                # Add to Streamlit UI chat history for re-rendering on reload
                st.session_state.chat_history.append({"user": user_input, "dashboard": dashboard})
                
                # Render the dynamic charts
                render_dashboard(dashboard)
                                
            except Exception as e:
                st.error(f"Error analyzing request: {e}")

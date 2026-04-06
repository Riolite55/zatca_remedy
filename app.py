import streamlit as st
import os
import sqlite3
import pandas as pd
from dotenv import load_dotenv
from pydantic_ai import Agent

# Load environment variables
load_dotenv()

# Auto-setup database on startup
from setup_db import create_db as _setup_db, DB_PATH
if not os.path.exists(DB_PATH):
    _setup_db()

st.set_page_config(page_title="Remedy AI Support Agent", page_icon="🎫")
st.title("🎫 Remedy AI Support Agent")

# Check for API Key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_gemini_api_key_here":
    st.warning("⚠️ Please set your GEMINI_API_KEY in the .env file.")
    st.stop()
os.environ["GOOGLE_API_KEY"] = api_key

# -----------------------------------------
# Database Schema for the Agent
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

# -----------------------------------------
# PydanticAI Agent Setup (queries real DB directly)
# -----------------------------------------
agent = Agent(
    'gemini-2.5-flash',
    system_prompt=(
        "You are a Support Manager AI and Data Analyst for BMC Remedy ITSM. "
        "You have access to a local SQLite database with a single table: hpd_help_desk (2000 real incident tickets). "
        "Use the `execute_sql` tool to query the database and answer user questions about tickets, statuses, SLA, group performance, etc. "
        "Always query the database before answering — never guess or make up data.\n\n"
        f"Database Schema:\n{db_schema}\n\n"
        "Guidelines:\n"
        "1. Use the `execute_sql` tool to find exact answers before responding.\n"
        "2. STATUS, PRIORITY, URGENCY, IMPACT, SLM_STATUS, REPORTED_SOURCE, and VIP are numeric codes. "
        "Always use the _DESCRIPTION/_DESC columns for filtering and display.\n"
        "3. Provide concise, helpful summaries based on the data you find.\n"
        "4. Do not wrap column names in quotes unless necessary."
    )
)

@agent.tool_plain
def execute_sql(query: str) -> str:
    """Execute a SQLite query against the Remedy ITSM database. Use this to fetch real data before answering."""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(query, conn)
        res = df.head(50).to_json(orient='records')
        return str(res) if res is not None else "[]"
    except Exception as e:
        return f"SQL Error: {e}"
    finally:
        conn.close()

# -----------------------------------------
# Session State
# -----------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pydantic_messages" not in st.session_state:
    st.session_state.pydantic_messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about Remedy tickets..."):
    # Add user message to state
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process assistant response
    with st.chat_message("assistant"):
        with st.spinner("Querying Remedy data..."):
            try:
                result = agent.run_sync(prompt, message_history=st.session_state.pydantic_messages)
                st.session_state.pydantic_messages = result.all_messages()

                st.markdown(result.output)
                st.session_state.messages.append({"role": "assistant", "content": result.output})
            except Exception as e:
                st.error(f"Error: {e}")

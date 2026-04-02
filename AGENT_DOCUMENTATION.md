# ZATCA Remedy AI Analyst: Agent Documentation

This document outlines the architecture, capabilities, database schema, and behavioral guidelines of the ZATCA Remedy AI Analyst. It serves as a comprehensive guide for understanding how the AI agent processes natural language, retrieves ITSM data, and generates dynamic BI dashboards.

---

## 1. High-Level Architecture

The AI Agent acts as an intelligent **Text-to-SQL Bridge** between the user and the BMC Remedy ITSM database.

1. **User Interface (Next.js):** The user types a natural language question in the Chat Canvas.
2. **Orchestration Layer (FastAPI & PydanticAI):** The request, along with the user's conversation history, is routed to the Python backend. PydanticAI manages the state, enforces the structured output schema, and holds the strict instructions (System Prompt).
3. **Intelligence Engine (Gemini 2.5):** The LLM receives the prompt and the database schema. It reasons about the request, decides what data is needed, writes a highly optimized SQLite query, and selects the best visual representation (Metric, Table, Bar, Pie, or Line chart).
4. **Execution Engine (Python/Pandas):** The FastAPI backend intercepts the AI's generated SQL, executes it safely against the local SQLite database (`remedy_mock.db`), and appends the raw JSON data to the response.
5. **Rendering (Recharts/Tailwind):** The frontend receives the structured payload and instantly renders interactive, ZATCA-branded dashboards.

---

## 2. Database Schema (Queryable Tables)

The Agent has full visibility into 5 relational tables mimicking the standard BMC Remedy AR System structure:

### `hpd_help_desk` (Core Incidents)
*The central table for all tickets.*
* **Keys:** `Entry_ID` (PK), `Incident_ID` (e.g., 'INC000000000001'), `Person_ID` (FK to Users)
* **Timestamps:** `Submit_Date`, `Closed_Date`, `Target_Date` (SLA deadline)
* **Categorization:** `Status`, `Status_Reason`, `Priority`, `Urgency`, `Impact`, `Incident_Type`
* **Assignment:** `Assigned_Group`, `Assignee_Login_ID`
* **Customer Info:** `First_Name`, `Last_Name`, `Company`, `VIP` (Yes/No)
* **SLM:** `SLM_Status` (e.g., 'Service Targets Met', 'Service Targets Breached')

### `hpd_worklog` (Activity & Notes)
*Tracks updates, logs, and communications on incidents.*
* **Keys:** `Work_Log_ID` (PK), `Incident_Number` (FK to hpd_help_desk.Incident_ID)
* **Details:** `Submitter`, `Submit_Date`, `Summary`, `Notes`, `Activity_Type` (e.g., 'Resolution Communications')

### `ctm_people` (Users & Staff)
*Directory of all employees and requesters.*
* **Keys:** `Person_ID` (PK), `Login_ID`
* **Details:** `First_Name`, `Last_Name`, `Email_Address`, `Phone_Number_Business`
* **Organization:** `Company`, `Department`, `VIP`

### `ctm_support_group_assoc` (Support Mappings)
*Maps staff to specific IT support groups.*
* **Keys:** `Support_Group_Assoc_LookUp_ID` (PK), `Person_ID` (FK to ctm_people)
* **Details:** `Support_Group_Name`, `Full_Name`

### `sys_status_reason` (Lookup Table)
*Maps status reason codes to readable text.*
* **Keys:** `Status_Reason_ID` (PK)
* **Details:** `Status_Reason_Menu_Item`

---

## 3. Agent Behavior & Functionality

The agent is strictly instructed to act as a **Data Analyst for BMC Remedy ITSM**. It handles different types of inputs as follows:

### A. SQL-Related Analytical Questions
When asked to count, list, or compare ticket data, the agent dynamically generates a `RemedyDashboard` object.
* **Metric Outputs:** Used for total counts (e.g., "How many open tickets?"). The agent writes SQL returning a single row/column.
* **Table Outputs:** Used for lists (e.g., "List the last 5 critical incidents"). The agent writes a standard `SELECT` query returning multiple rows.
* **Chart Outputs (Bar/Pie/Line):** Used for breakdowns (e.g., "Show me tickets by Priority"). The agent uses `GROUP BY` and `COUNT()` in SQL, ensuring it maps an `x_col` (the category) and a `y_col` (the count) for the UI to render.

### B. General ITSM Questions
If a user asks a general question (e.g., *"What is the difference between Priority and Urgency in Remedy?"*), the agent uses its base LLM knowledge to provide a professional, text-based explanation. It will bypass generating SQL charts entirely and simply return an informative paragraph in the chat.

### C. Irrelevant or Malicious Questions
* **Guardrails:** If asked about topics outside of IT Service Management, data analytics, or the provided schema (e.g., *"Write a poem about cats"*, or *"How do I bake a cake?"*), the agent is instructed to politely refuse and steer the conversation back to Remedy Analytics.
* **SQL Injection Prevention:** The agent is restricted to generating `SELECT` queries. The backend execution layer strictly uses `pandas.read_sql_query`, which mitigates destructive commands (like `DROP TABLE` or `DELETE`), protecting the underlying database.

### D. Conversational Memory
The agent remembers previous turns. If a user asks, *"Show me all pending tickets"*, and then follows up with *"Which of those are assigned to Network Ops?"*, the agent automatically rewrites the SQL query to include both the `Status='Pending'` constraint from the first question and the `Assigned_Group='Network Ops'` constraint from the second.

---

## 4. Sample Questions

Here is a list of questions you can ask the agent to test its capabilities:

### Simple Metrics (Single Numbers)
* *"How many tickets are currently in the system?"*
* *"Count the number of Critical priority incidents."*
* *"How many SLAs have been breached?"*

### Breakdowns (Pie & Bar Charts)
* *"Show me a pie chart of all open tickets broken down by Support Group."*
* *"Give me a bar chart of incidents grouped by Categorization (Incident Type)."*
* *"Show the distribution of SLA Statuses for tickets assigned to the Service Desk."*

### Multi-Table Joins (Complex Queries)
* *"List the names, emails, and ticket summaries for all VIP users who have an open ticket."* *(Joins `hpd_help_desk` and `ctm_people`)*
* *"Which Support Group has the most unresolved tickets?"* *(Aggregates `hpd_help_desk`)*
* *"Show me the Worklog notes for Incident INC000000000014."* *(Queries `hpd_worklog`)*
* *"How many tickets reported by Acme Corp employees are currently pending?"*

### Trend Analysis (Line Charts)
* *"Show me a line chart of tickets submitted per day over the last month."* *(Uses SQLite date functions to group by `Submit_Date`)*

---
*Generated for the ZATCA Remedy AI Analyst PoC.*
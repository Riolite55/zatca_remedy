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

## 2. Database Schema (Queryable Table)

The Agent has full visibility into a single table containing real BMC Remedy incident data (2000 tickets, 189 columns):

### `hpd_help_desk` (All Incidents)
*The single source of truth for all ticket data — imported from real Remedy export.*

* **Identity:** `ENTRY_ID`, `INCIDENT_NUMBER` (e.g., 'INC678916')
* **Timestamps:** `SUBMIT_DATE`, `SUBMIT_DATE_DATE`, `CLOSED_DATE_DATE`, `LAST_RESOLVED_DATE_DATE`, `REPORTED_DATE_DATE`, `RE_OPENED_DATE_DATE`
* **Status:** `STATUS` (integer), `STATUS_DESCRIPTION` (text: 'Assigned', 'In Progress', 'Resolved', 'Closed', 'Canceled')
* **Priority:** `PRIORITY` (integer), `PRIORITY_DESCRIPTION` (text: 'Medium', 'Low')
* **Classification:** `URGENCY` (integer), `IMPACT` (integer), `CATEGORIZATION_TIER_1/2/3`, `REPORTED_SOURCE_DESC`
* **Description:** `DESCRIPTION`, `DETAILED_DECRIPTION`, `RESOLUTION`, `RESOLUTION_CATEGORY`
* **Assignment:** `ASSIGNED_GROUP` (e.g., 'Service Desk', 'E-invoicing L2'), `ASSIGNEE`, `ASSIGNEE_LOGIN_ID`, `ASSIGNED_SUPPORT_ORGANIZATION`
* **Customer:** `FIRST_NAME`, `LAST_NAME`, `REQUESTER_NAME`, `COMPANY`, `ORGANIZATION`, `VIP` (0/1), `INTERNET_E_MAIL`
* **SLA:** `SLM_STATUS_DESCRIPTION` ('Within Service Target', 'Service Target Breached'), `SLA_RESPONSE_STATUS`, `SLA_RESOLUTION_STATUS` ('Met', 'Missed', 'In Process')
* **Transfers:** `GROUP_TRANSFERS`, `TOTAL_TRANSFERS`, `INDIVIDUAL_TRANSFERS`
* **Aging:** `INCIDENT_AGING` (days), `REOPEN_COUNT`

> **IMPORTANT:** `STATUS`, `PRIORITY`, `URGENCY`, `IMPACT`, `SLM_STATUS`, `REPORTED_SOURCE`, and `VIP` are **numeric codes**. Always use the corresponding `_DESCRIPTION` / `_DESC` columns for human-readable text in queries.

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
* *"Count the number of tickets with breached SLAs."*
* *"How many tickets are currently assigned?"*

### Breakdowns (Pie & Bar Charts)
* *"Show me a pie chart of tickets broken down by STATUS_DESCRIPTION."*
* *"Give me a bar chart of incidents grouped by CATEGORIZATION_TIER_1."*
* *"Show the distribution of SLA Resolution Statuses for tickets assigned to Service Desk."*

### Detailed Queries
* *"List the INCIDENT_NUMBER, REQUESTER_NAME, and DESCRIPTION for all VIP tickets."*
* *"Which ASSIGNED_GROUP has the most unresolved tickets?"*
* *"How many tickets have been reopened (REOPEN_COUNT > 0)?"*
* *"Show me the top 10 longest-aging open tickets."*

### Trend Analysis (Line Charts)
* *"Show me a line chart of tickets submitted per day over the last month."* *(Uses SQLite date functions to group by `SUBMIT_DATE_DATE`)*

---
*Generated for the ZATCA Remedy AI Analyst PoC.*
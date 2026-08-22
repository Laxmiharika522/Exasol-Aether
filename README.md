# Aether – Enterprise Data Steward & Multi-Agent BI Copilot

**Exasol AI Build Challenge 2026 | Autonomous Agents Track**

A multi-agent system that allows non-technical stakeholders (managers, CFOs, operations leads) to ask complex analytical questions in plain English. Specialized agents collaborate using **Exasol Personal** via the Model Context Protocol (MCP) to discover schemas, generate safe SQL, enforce governance, and produce executive-ready insights with visualizations.

---

## Current Status (16 August 2026)

- [x] Exasol Personal (Nano) running locally via Starter Kit
- [x] Sample datasets loaded (TPCH is the primary retail/supply-chain dataset)
- [x] Python connection to Exasol working (`pyexasol`)
- [x] MCP Server installed and validated
- [x] Project structure created
- [x] **Schema Agent** implemented (discovers tables/columns)
- [x] **SQL Agent** implemented (natural language to SQL, conversational memory)
- [x] **Governance Agent** implemented (enforces read-only, security checks)
- [x] **Storyteller Agent** implemented (dynamic JSON charting, executive insights)
- [x] **Orchestrator** implemented (routes multi-agent pipeline)
- [x] **Frontend (Streamlit)** implemented (Enterprise UI, Chat UI, Groq Whisper STT)
- [ ] AWS deployment (pending)

---

## Project Structure

```
Aether/
├── agents/
│   ├── schema_agent.py          ✅ Done
│   ├── sql_agent.py             ✅ Done (Conversational Memory)
│   ├── governance_agent.py      ✅ Done
│   ├── storyteller_agent.py     ✅ Done (Dynamic JSON Charts)
│   └── orchestrator.py          ✅ Done
├── core/
├── utils/
│   └── db.py                    ✅ Done
├── frontend/
│   └── app.py                   ✅ Done (Voice STT + Enterprise UI)
├── docs/
├── tests/
├── scripts/
├── .env.example
├── requirements.txt
├── test_connection.py
├── test_schema_agent.py
└── README.md
```

---

## Prerequisites

- Docker Desktop running
- Exasol Starter Kit installed and running (`exakit status` should show "running")
- Python 3.10+
- **Groq API Key** (for SQL Agent LLM and Whisper STT)

---

## Setup Instructions

1. Clone / open the project folder
2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create `.env` file from the example:
   ```bash
   copy .env.example .env
   ```
   *Fill in your Exasol credentials and `GROQ_API_KEY`.*
5. Run the Enterprise Application:
   ```bash
   streamlit run frontend/app.py
   ```

---

## Available Data (TPCH Schema)

Main tables we will use:

- TPCH.CUSTOMER
- TPCH.ORDERS
- TPCH.LINEITEM
- TPCH.PART
- TPCH.SUPPLIER
- TPCH.NATION
- TPCH.REGION
- TPCH.PARTSUPP

---

## Team Division (Suggested)

| Role | Responsibility | Status |
| --- | --- | --- |
| Schema Agent | Discover schemas, tables, columns | ✅ Done |
| SQL Agent | Generate and execute SQL queries (with conversational memory) | ✅ Done |
| Governance Agent | Safety checks, PII redaction, read-only | ✅ Done |
| Storyteller Agent | Analyze results + output Dynamic Chart JSON spec | ✅ Done |
| Orchestrator | Plan and coordinate all agents, manage chat history | ✅ Done |
| Frontend | Enterprise Chat Interface, Whisper Voice STT, Dynamic Plotly | ✅ Done |

---

## Next Steps

- Move the system to AWS before final submission (Dockerize the frontend)
- Prepare a video recording demonstrating Voice Queries and Memory

---

## Notes

- All database access currently goes through `utils/db.py`
- Passwords must never be committed — use `.env`
- Primary dataset for the demo will be **TPCH**

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
- [x] Schema Agent implemented and tested
- [ ] SQL Agent
- [ ] Governance Agent
- [ ] Storyteller Agent
- [ ] Orchestrator
- [ ] Frontend (Streamlit)
- [ ] AWS deployment (later)

---

## Project Structure

```
Aether/
├── agents/
│   ├── schema_agent.py          ✅ Done
│   ├── sql_agent.py
│   ├── governance_agent.py
│   ├── storyteller_agent.py
│   └── orchestrator.py
├── core/
├── utils/
│   └── db.py                    ✅ Done
├── frontend/
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

---

## Setup Instructions

1. Clone / open the project folder
2. Create and activate virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Create `.env` file from the example:
   ```powershell
   copy .env.example .env
   ```
   Then fill in the real passwords.
5. Test the connection:
   ```powershell
   python test_connection.py
   ```
6. Test the Schema Agent:
   ```powershell
   python test_schema_agent.py
   ```

---

## Available Data (TPCH Schema)

Main tables we will use:

- `TPCH.CUSTOMER`
- `TPCH.ORDERS`
- `TPCH.LINEITEM`
- `TPCH.PART`
- `TPCH.SUPPLIER`
- `TPCH.NATION`
- `TPCH.REGION`
- `TPCH.PARTSUPP`

---

## Team Division (Suggested)

| Role                    | Responsibility                              | Status     |
|-------------------------|---------------------------------------------|------------|
| Schema Agent            | Discover schemas, tables, columns           | ✅ Done    |
| SQL Agent               | Generate and execute SQL queries            | Pending    |
| Governance Agent        | Safety checks, PII redaction, read-only     | Pending    |
| Storyteller Agent       | Analyze results + create summary + charts   | Pending    |
| Orchestrator            | Plan and coordinate all agents              | Pending    |
| Frontend                | Streamlit chat interface                    | Pending    |

---

## Next Steps

1. Implement remaining agents
2. Connect agents using LangGraph
3. Build a simple Streamlit UI
4. Prepare strong demo questions on TPCH data
5. Move the system to AWS before final submission

---

## Notes

- All database access currently goes through `utils/db.py`
- Passwords must never be committed — use `.env`
- Primary dataset for the demo will be **TPCH**

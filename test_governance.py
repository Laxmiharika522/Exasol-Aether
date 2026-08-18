from agents.governance_agent import GovernanceAgent

agent = GovernanceAgent()

test_queries = [
    "SELECT * FROM TPCH.CUSTOMER LIMIT 5",
    "DELETE FROM TPCH.CUSTOMER",
    "DROP TABLE TPCH.ORDERS",
    "SELECT C_NAME, C_PHONE FROM TPCH.CUSTOMER",
    "UPDATE TPCH.CUSTOMER SET C_NAME = 'Hacked'"
]

for sql in test_queries:
    result = agent.review_query(sql)
    status = "APPROVED" if result["approved"] else "BLOCKED"
    print(f"\n{status}: {result['reason']}")
    print(f"SQL: {sql[:60]}...")
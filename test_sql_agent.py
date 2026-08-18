from agents.sql_agent import SQLAgent

agent = SQLAgent()

questions = [
    "Compare total revenue by region",
    "Who are the top 10 customers by total spend?",
    "Which suppliers have the highest order volume?",
    "Show average order value by nation"
]

for q in questions:
    print(f"\n{'='*60}")
    print(f"Question: {q}")
    result = agent.run(q)
    
    if result["success"]:
        print(f"Rows returned: {result['row_count']}")
        print("First 5 rows:")
        for row in result["data"][:5]:
            print(row)
    else:
        print("Error:", result["error"])

agent.close()
print("\nDone.")
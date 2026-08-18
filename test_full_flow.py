from agents.sql_agent import SQLAgent
from agents.governance_agent import GovernanceAgent
from agents.storyteller_agent import StorytellerAgent

sql_agent = SQLAgent()
gov_agent = GovernanceAgent()
story_agent = StorytellerAgent()

question = "Compare total revenue by region"

print(f"Question: {question}\n")

# 1. Generate SQL
sql = sql_agent.generate_sql(question)
print("Generated SQL:")
print(sql)

# 2. Governance check
review = gov_agent.review_query(sql)
print(f"\nGovernance: {'APPROVED' if review['approved'] else 'BLOCKED'}")
print(f"Reason: {review['reason']}")

if review["approved"]:
    # 3. Execute
    result = sql_agent.execute_query(sql)
    
    # 4. Create summary
    summary = story_agent.generate_summary(question, result)
    print("\n" + "="*50)
    print(summary)

sql_agent.close()
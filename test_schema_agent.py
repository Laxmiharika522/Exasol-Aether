from agents.schema_agent import SchemaAgent

agent = SchemaAgent()

print("=== Schemas ===")
print(agent.list_schemas())

print("\n=== TPCH Tables ===")
tables = agent.list_tables("TPCH")
for t in tables:
    print(t)

agent.close()
print("\nDone.")
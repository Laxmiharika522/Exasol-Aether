from agents.orchestrator import Orchestrator

orch = Orchestrator()

questions = [
    "Compare total revenue by region",
    "Who are the top 10 customers by total spend?"
]

for q in questions:
    print("\n" + "="*70)
    response = orch.answer(q)
    
    if response["success"]:
        print(response["summary"])
    else:
        print("Failed:", response.get("error"))

orch.close()
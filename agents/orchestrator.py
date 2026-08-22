from agents.schema_agent import SchemaAgent
from agents.sql_agent import SQLAgent
from agents.governance_agent import GovernanceAgent
from agents.storyteller_agent import StorytellerAgent

class Orchestrator:
    """
    Coordinates all agents to answer a user question.
    """

    def __init__(self):
        self.schema_agent = SchemaAgent()
        self.sql_agent = SQLAgent()
        self.governance_agent = GovernanceAgent()
        self.storyteller_agent = StorytellerAgent()

    def answer(self, question: str, chat_history: list = None) -> dict:
        """
        Full multi-agent pipeline.
        Returns a structured response.
        """
        print(f"\n[Orchestrator] Received question: {question}")

        # Step 1: Schema discovery (basic for now)
        print("[Orchestrator] Calling Schema Agent...")
        schemas = self.schema_agent.list_schemas()
        tables = self.schema_agent.list_tables("TPCH")
        schema_context = f"Available schemas: {schemas}\nTPCH tables: {tables}"

        # Step 2: Generate SQL
        print("[Orchestrator] Calling SQL Agent...")
        sql = self.sql_agent.generate_sql(question, schema_context, chat_history)
        print(f"[Orchestrator] Generated SQL:\n{sql}")

        # Step 3: Governance check
        print("[Orchestrator] Calling Governance Agent...")
        review = self.governance_agent.review_query(sql, question)
        
        if not review["approved"]:
            print(f"[Orchestrator] Query BLOCKED: {review['reason']}")
            return {
                "success": False,
                "question": question,
                "error": review["reason"],
                "sql": sql
            }

        print("[Orchestrator] Query APPROVED by Governance")

        # Step 4: Execute query
        print("[Orchestrator] Executing query on Exasol...")
        result = self.sql_agent.execute_query(sql)

        if not result["success"]:
            return {
                "success": False,
                "question": question,
                "error": result.get("error"),
                "sql": sql
            }

        # Step 5: Generate summary and chart metadata
        print("[Orchestrator] Calling Storyteller Agent...")
        story_result = self.storyteller_agent.generate_summary(question, result)

        print("[Orchestrator] Done.\n")

        return {
            "success": True,
            "question": question,
            "sql": sql,
            "row_count": result["row_count"],
            "data": result["data"],
            "columns": result.get("columns", []),
            "summary": story_result.get("summary", "Done."),
            "chart_config": story_result.get("chart", None)
        }

    def close(self):
        self.schema_agent.close()
        self.sql_agent.close()
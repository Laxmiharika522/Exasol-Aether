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
        import time
        def safe_log(msg):
            try:
                print(msg)
            except UnicodeEncodeError:
                print(msg.encode('ascii', 'backslashreplace').decode('ascii'))

        safe_log(f"\n[Orchestrator] Received question: {question}")
        timings = {}

        # Step 1: Schema discovery
        safe_log("[Orchestrator] Calling Schema Agent...")
        start_time = time.time()
        schemas = self.schema_agent.list_schemas()
        tables = self.schema_agent.list_tables("TPCH")
        timings["schema"] = int((time.time() - start_time) * 1000)
        schema_context = f"Available schemas: {schemas}\nTPCH tables: {tables}"

        # Step 2: Generate SQL
        safe_log("[Orchestrator] Calling SQL Agent...")
        start_time = time.time()
        sql = self.sql_agent.generate_sql(question, schema_context, chat_history)
        timings["sql"] = int((time.time() - start_time) * 1000)
        safe_log(f"[Orchestrator] Generated SQL:\n{sql}")

        # Step 3: Governance check
        safe_log("[Orchestrator] Calling Governance Agent...")
        start_time = time.time()
        review = self.governance_agent.review_query(sql, question)
        timings["governance"] = int((time.time() - start_time) * 1000)
        
        if not review["approved"]:
            print(f"[Orchestrator] Query BLOCKED: {review['reason']}")
            return {
                "success": False,
                "question": question,
                "error": review["reason"],
                "sql": sql,
                "timings": timings
            }

        safe_log("[Orchestrator] Query APPROVED by Governance")

        # Step 4: Execute query
        safe_log("[Orchestrator] Executing query on Exasol...")
        start_time = time.time()
        result = self.sql_agent.execute_query(sql)
        timings["execution"] = int((time.time() - start_time) * 1000)

        if not result["success"]:
            return {
                "success": False,
                "question": question,
                "error": result.get("error"),
                "sql": sql,
                "timings": timings
            }

        # Step 5: Generate summary and chart metadata
        safe_log("[Orchestrator] Calling Storyteller Agent...")
        start_time = time.time()
        story_result = self.storyteller_agent.generate_summary(question, result)
        timings["storyteller"] = int((time.time() - start_time) * 1000)

        safe_log("[Orchestrator] Done.\n")

        return {
            "success": True,
            "question": question,
            "sql": sql,
            "row_count": result["row_count"],
            "data": result["data"],
            "columns": result.get("columns", []),
            "summary": story_result.get("summary", "Done."),
            "chart_config": story_result.get("chart", None),
            "timings": timings
        }

    def close(self):
        self.schema_agent.close()
        self.sql_agent.close()
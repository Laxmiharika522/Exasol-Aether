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

    def answer(self, question: str) -> str:
        """
        High-level flow (to be improved later):
        1. Understand the question
        2. Discover relevant schema
        3. Generate SQL
        4. Governance check
        5. Execute
        6. Create summary
        """
        # Placeholder for now
        return f"Orchestrator received question: {question}\n(Full multi-agent flow coming next)"

    def close(self):
        self.schema_agent.close()
        self.sql_agent.close()
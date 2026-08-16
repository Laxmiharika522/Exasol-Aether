class StorytellerAgent:
    """
    Analyzes query results and creates a simple summary.
    Later we will add charts and better insights.
    """

    def generate_summary(self, question: str, data: list) -> str:
        if not data:
            return "No data was returned for this question."

        summary = f"Based on the question: '{question}'\n\n"
        summary += f"I found {len(data)} rows of results.\n"
        summary += "Here are the first few results:\n\n"

        for i, row in enumerate(data[:5]):
            summary += f"{i+1}. {row}\n"

        return summary
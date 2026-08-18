class StorytellerAgent:
    """
    Takes query results and creates a clear executive summary.
    """

    def generate_summary(self, question: str, result: dict) -> str:
        """
        Create a readable summary from the SQL result.
        """
        if not result.get("success"):
            return f"I couldn't answer the question because of an error:\n{result.get('error', 'Unknown error')}"

        data = result.get("data", [])
        row_count = result.get("row_count", 0)

        if row_count == 0:
            return "No data was found for your question."

        # Start building the summary
        summary = f"**Question:** {question}\n\n"
        summary += f"I found **{row_count}** results.\n\n"

        # Show top results in a clean way
        summary += "**Key Results:**\n"

        for i, row in enumerate(data[:5], 1):
            # Convert row to a readable string
            if len(row) == 2:
                summary += f"{i}. {row[0]} → {row[1]}\n"
            else:
                summary += f"{i}. {row}\n"

        if row_count > 5:
            summary += f"\n... and {row_count - 5} more rows."

        summary += "\n\n**Summary:** The data has been successfully retrieved from Exasol and is ready for analysis."

        return summary
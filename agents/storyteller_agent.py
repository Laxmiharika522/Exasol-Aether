import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class StorytellerAgent:
    """
    Takes query results and creates a clear executive summary and chart recommendation
    using Groq LLM.
    """

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = "openai/gpt-oss-120b"

        self.system_prompt = """You are an Executive Business Analyst. 
You are given a user question, and the resulting data (columns and up to 10 sample rows).
Your job is to:
1. Write a 1-2 sentence executive summary of the findings.
2. Recommend the best chart type to visualize this data (bar, line, pie, or scatter).
3. Identify which column should be the X-axis (usually categorical or time), and which should be the Y-axis (must be numeric).

You MUST return your response as a strict JSON object with this exact schema:
{
    "summary": "Your executive summary...",
    "chart": {
        "type": "bar|line|pie|scatter",
        "x": "COLUMN_NAME",
        "y": "COLUMN_NAME"
    }
}
If there is no logical chart to make (e.g. only 1 column, or no numeric data), set chart to null.
Do NOT include any markdown blocks (like ```json), just output the raw JSON.
"""

    def generate_summary(self, question: str, result: dict) -> dict:
        """
        Create an AI summary and chart config from the SQL result.
        Returns a dict.
        """
        if not result.get("success"):
            return {
                "summary": f"I couldn't answer the question because of an error:\n{result.get('error', 'Unknown error')}",
                "chart": None
            }

        data = result.get("data", [])
        columns = result.get("columns", [])
        row_count = result.get("row_count", 0)

        if row_count == 0:
            return {
                "summary": "No data was found matching your question.",
                "chart": None
            }

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Truncate data for the LLM to avoid token limits
            sample_data = data[:10]
            
            prompt_content = f"Question: {question}\n\nColumns: {columns}\nSample Data: {sample_data}\nTotal Rows: {row_count}"
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt_content}
                ],
                "temperature": 0.1
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            raw_content = response.json()["choices"][0]["message"]["content"].strip()
            
            # Clean up potential markdown formatting from LLM
            raw_content = raw_content.replace("```json", "").replace("```", "").strip()
            
            return json.loads(raw_content)
            
        except Exception as e:
            print(f"[StorytellerAgent] Error generating summary: {e}")
            # Fallback
            return {
                "summary": f"Data retrieved successfully. Found {row_count} records.",
                "chart": None
            }
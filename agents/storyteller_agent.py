import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class StorytellerAgent:
    """
    Takes query results and creates a clear executive summary and chart recommendation
    using Groq LLM dynamically.
    """

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]

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
        Create an AI summary and chart config from the SQL result dynamically.
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

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Truncate data for the LLM to avoid token limits
        sample_data = data[:10]
        prompt_content = f"Question: {question}\n\nColumns: {columns}\nSample Data: {sample_data}\nTotal Rows: {row_count}"
        
        for model in self.models:
            try:
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt_content}
                    ],
                    "temperature": 0.1
                }
                
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=15
                )
                if response.status_code == 429:
                    continue
                response.raise_for_status()
                
                raw_content = response.json()["choices"][0]["message"]["content"].strip()
                # Clean markdown formatting and normalize unicode
                raw_content = re.sub(r"^```(?:json)?\s*", "", raw_content, flags=re.IGNORECASE)
                raw_content = re.sub(r"\s*```$", "", raw_content)
                raw_content = raw_content.replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '-')
                
                # Extract first JSON object
                json_match = re.search(r"\{.*\}", raw_content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                return json.loads(raw_content)
                
            except Exception as e:
                continue

        # Dynamic fallback if all LLM endpoints fail
        return self._infer_fallback_story(question, data, columns, row_count)

    def _infer_fallback_story(self, question: str, data: list, columns: list, row_count: int) -> dict:
        """Deterministically infer the best chart config and executive summary from data."""
        if not data or not columns:
            return {
                "summary": f"Data retrieved successfully. Found {row_count} records.",
                "chart": None
            }

        # Find X and Y candidates
        x_col = columns[0]
        y_col = None

        # Look for a numeric column for Y
        for i, col in enumerate(columns):
            # Check if values in column i are numeric
            is_num = False
            for row in data[:5]:
                val = row[i] if i < len(row) else None
                if val is not None:
                    try:
                        float(str(val).replace('$', '').replace(',', ''))
                        is_num = True
                        break
                    except ValueError:
                        pass
            if is_num and i > 0 and y_col is None:
                y_col = col

        if y_col is None and len(columns) > 1:
            y_col = columns[1]

        chart_config = None
        if x_col and y_col:
            chart_type = "bar"
            x_upper = x_col.upper()
            q_lower = question.lower()

            if any(k in x_upper for k in ["YEAR", "DATE", "MONTH", "DAY", "TIME"]):
                chart_type = "line"
            elif row_count <= 6 and any(k in (x_upper + " " + q_lower) for k in ["STATUS", "FLAG", "PRIORITY", "NULL", "SHARE", "PERCENT"]):
                chart_type = "pie"

            chart_config = {
                "type": chart_type,
                "x": x_col,
                "y": y_col
            }

        # Build clean summary
        summary = f"Analysis returned {row_count} record{'s' if row_count != 1 else ''} across {', '.join(columns)}."
        if len(data) > 0 and y_col:
            try:
                top_row = data[0]
                summary = f"Top result: {top_row[0]} with {y_col.replace('_', ' ').title()} of {top_row[1]}. Generated analytical breakdown across {row_count} data points."
            except Exception:
                pass

        return {
            "summary": summary,
            "chart": chart_config
        }
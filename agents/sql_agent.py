import os
import re
import time
import requests
from utils.db import get_connection
from dotenv import load_dotenv

load_dotenv()

class SQLAgent:
    """
    100% LLM-powered SQL Agent using Groq.
    Generates dynamic, dialect-accurate Exasol SQL for the TPCH dataset.
    """

    def __init__(self):
        self.conn = get_connection()
        self.api_key = os.getenv("GROQ_API_KEY")
        self.models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]

        self.system_prompt = """You are an expert SQL generator for Exasol database.
You only generate clean, correct, read-only SQL queries for the TPCH schema.

Available tables and important columns:
- TPCH.CUSTOMER (C_CUSTKEY, C_NAME, C_ADDRESS, C_NATIONKEY, C_PHONE, C_ACCTBAL, C_MKTSEGMENT)
- TPCH.ORDERS (O_ORDERKEY, O_CUSTKEY, O_ORDERSTATUS, O_TOTALPRICE, O_ORDERDATE, O_ORDERPRIORITY)
- TPCH.LINEITEM (L_ORDERKEY, L_PARTKEY, L_SUPPKEY, L_LINENUMBER, L_QUANTITY, L_EXTENDEDPRICE, L_DISCOUNT, L_TAX, L_RETURNFLAG, L_LINESTATUS, L_SHIPDATE, L_COMMITDATE, L_RECEIPTDATE, L_SHIPMODE)
- TPCH.PART (P_PARTKEY, P_NAME, P_MFGR, P_BRAND, P_TYPE, P_SIZE, P_CONTAINER, P_RETAILPRICE)
- TPCH.SUPPLIER (S_SUPPKEY, S_NAME, S_ADDRESS, S_NATIONKEY, S_PHONE, S_ACCTBAL)
- TPCH.PARTSUPP (PS_PARTKEY, PS_SUPPKEY, PS_AVAILQTY, PS_SUPPLYCOST)
- TPCH.NATION (N_NATIONKEY, N_NAME, N_REGIONKEY)
- TPCH.REGION (R_REGIONKEY, R_NAME)

Rules:
- Only generate SELECT queries
- Use proper JOINs and explicit table aliases for all columns
- Prefer ROUND() for currency and percentages
- Net revenue formula: ROUND(SUM(l.L_EXTENDEDPRICE * (1 - l.L_DISCOUNT)), 2)
- Exasol Reserved Words: NEVER use reserved keywords like YEAR, DATE, MONTH, DAY, RANK, ORDER, USER, SCHEMA as unquoted column aliases. Always use aliases like ORDER_YEAR, ORDER_DATE, REVENUE_RANK, TABLE_SCHEMA, etc.
- Exasol Date Math: Do NOT use DATEDIFF. Use DAYS_BETWEEN(date1, date2) to get the difference in days. Use YEAR(date_column) for year extraction.
- Type Safety: C_CUSTKEY is an INTEGER. C_NAME is a VARCHAR (e.g., 'Customer#00000123'). NEVER compare C_CUSTKEY to a string. Filter using C_NAME for text.
- Exasol System Metadata: If asked about database metadata (tables, columns, types), query EXA_ALL_COLUMNS, EXA_ALL_TABLES, or EXA_SCHEMAS. Note: schema column is COLUMN_SCHEMA, table column is COLUMN_TABLE, column name is COLUMN_NAME, data type is COLUMN_TYPE, and nullability is COLUMN_IS_NULLABLE. If asked about schemas, query EXA_SCHEMAS (column SCHEMA_NAME).
- Return ONLY the raw SQL query, nothing else
- No explanations, no markdown blocks, no commentary
"""

    def _clean_sql(self, raw_sql: str) -> str:
        """Strip markdown tags, normalize unicode characters, and trim whitespace."""
        cleaned = re.sub(r"^```(?:sql)?\s*", "", raw_sql.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        # Normalize non-breaking hyphens and smart quotes to standard ASCII
        cleaned = (cleaned
                   .replace('\u2011', '-')
                   .replace('\u2013', '-')
                   .replace('\u2014', '-')
                   .replace('\u2018', "'")
                   .replace('\u2019', "'")
                   .replace('\u201c', '"')
                   .replace('\u201d', '"'))
        return cleaned.strip()

    def generate_sql(self, question: str, schema_context: str = "", chat_history: list = None) -> str:
        """Generate SQL dynamically using LLM with multi-model failover."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Inject conversational history safely (ensure content is always a clean string)
        if chat_history:
            for msg in chat_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if isinstance(content, dict):
                    content = content.get("summary") or content.get("sql") or str(content)
                elif not isinstance(content, str):
                    content = str(content)
                if content.strip():
                    messages.append({"role": role, "content": content.strip()})
        
        messages.append({"role": "user", "content": f"Question: {question}\n\nGenerate the Exasol SQL query:"})
        
        # Try models in sequence with retry on rate limit
        for model in self.models:
            for attempt in range(2):
                try:
                    payload = {
                        "model": model,
                        "messages": messages,
                        "temperature": 0.0
                    }
                    resp = requests.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=15
                    )
                    if resp.status_code == 429:
                        time.sleep(1)
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    raw_sql = data["choices"][0]["message"]["content"]
                    sql = self._clean_sql(raw_sql)
                    return sql
                except Exception as e:
                    time.sleep(0.5)
                    continue

        return "SELECT 1"

    def execute_query(self, sql: str) -> dict:
        """Execute SQL on Exasol."""
        try:
            stmt = self.conn.execute(sql)
            result = stmt.fetchall()
            columns = stmt.column_names()
            return {
                "success": True,
                "sql": sql,
                "data": result,
                "columns": columns,
                "row_count": len(result)
            }
        except Exception as e:
            return {
                "success": False,
                "sql": sql,
                "error": str(e)
            }

    def run(self, question: str, schema_context: str = "") -> dict:
        sql = self.generate_sql(question, schema_context)
        return self.execute_query(sql)

    def close(self):
        self.conn.close()
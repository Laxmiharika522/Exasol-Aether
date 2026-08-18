import os
from openai import OpenAI
from utils.db import get_connection
from dotenv import load_dotenv

load_dotenv()

class SQLAgent:
    """
    LLM-powered SQL Agent using Groq.
    Generates Exasol-compatible SQL for the TPCH dataset.
    """

    def __init__(self):
        self.conn = get_connection()
        
        self.client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        
        self.model = "openai/gpt-oss-20b"

        self.system_prompt = """You are an expert SQL generator for Exasol database.
You only generate clean, correct, read-only SQL queries for the TPCH schema.

Available tables and important columns:

TPCH.CUSTOMER (C_CUSTKEY, C_NAME, C_ADDRESS, C_NATIONKEY, C_PHONE, C_ACCTBAL, C_MKTSEGMENT)
TPCH.ORDERS (O_ORDERKEY, O_CUSTKEY, O_ORDERSTATUS, O_TOTALPRICE, O_ORDERDATE, O_ORDERPRIORITY)
TPCH.LINEITEM (L_ORDERKEY, L_PARTKEY, L_SUPPKEY, L_LINENUMBER, L_QUANTITY, L_EXTENDEDPRICE, L_DISCOUNT, L_TAX, L_RETURNFLAG, L_LINESTATUS)
TPCH.PART (P_PARTKEY, P_NAME, P_MFGR, P_BRAND, P_TYPE, P_SIZE, P_CONTAINER, P_RETAILPRICE)
TPCH.SUPPLIER (S_SUPPKEY, S_NAME, S_ADDRESS, S_NATIONKEY, S_PHONE, S_ACCTBAL)
TPCH.PARTSUPP (PS_PARTKEY, PS_SUPPKEY, PS_AVAILQTY, PS_SUPPLYCOST)
TPCH.NATION (N_NATIONKEY, N_NAME, N_REGIONKEY)
TPCH.REGION (R_REGIONKEY, R_NAME)

Rules:
- Only generate SELECT queries
- Use proper JOINs
- Always use table aliases
- Prefer ROUND() for money values
- Return ONLY the SQL query, nothing else
- No explanations, no markdown, no ```sql
"""

    def generate_sql(self, question: str, schema_context: str = "") -> str:
        """Generate SQL using Groq LLM."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Question: {question}\n\nGenerate the SQL query:"}
                ],
                temperature=0.1
            )
            
            sql = response.choices[0].message.content.strip()
            sql = sql.replace("```sql", "").replace("```", "").strip()
            return sql
            
        except Exception as e:
            print(f"[SQLAgent] Error generating SQL: {e}")
            return "SELECT 1"

    def execute_query(self, sql: str) -> dict:
        """Execute SQL on Exasol."""
        try:
            result = self.conn.execute(sql).fetchall()
            return {
                "success": True,
                "sql": sql,
                "data": result,
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
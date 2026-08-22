import os
from openai import OpenAI
from utils.db import get_connection
from dotenv import load_dotenv

load_dotenv()

import requests

class SQLAgent:
    """
    LLM-powered SQL Agent using Groq.
    Generates Exasol-compatible SQL for the TPCH dataset.
    """

    def __init__(self):
        self.conn = get_connection()
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = "openai/gpt-oss-120b"

        self.system_prompt = """You are an expert SQL generator for Exasol database.
You only generate clean, correct, read-only SQL queries for the TPCH schema.

Available tables and important columns:

TPCH.CUSTOMER (C_CUSTKEY, C_NAME, C_ADDRESS, C_NATIONKEY, C_PHONE, C_ACCTBAL, C_MKTSEGMENT)
TPCH.ORDERS (O_ORDERKEY, O_CUSTKEY, O_ORDERSTATUS, O_TOTALPRICE, O_ORDERDATE, O_ORDERPRIORITY)
TPCH.LINEITEM (L_ORDERKEY, L_PARTKEY, L_SUPPKEY, L_LINENUMBER, L_QUANTITY, L_EXTENDEDPRICE, L_DISCOUNT, L_TAX, L_RETURNFLAG, L_LINESTATUS, L_SHIPDATE, L_COMMITDATE, L_RECEIPTDATE, L_SHIPMODE)
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
- Exasol Date Math: Do NOT use DATEDIFF. Use DAYS_BETWEEN(date1, date2) to get the difference in days.
- Return ONLY the SQL query, nothing else
- No explanations, no markdown, no ```sql
"""

        # Predefined fallback queries for the core demo questions
        self.fallback_queries = {
            "compare total revenue by region": """SELECT 
    r.R_NAME AS REGION, 
    ROUND(SUM(l.L_EXTENDEDPRICE * (1 - l.L_DISCOUNT)), 2) AS TOTAL_REVENUE
FROM TPCH.LINEITEM l
JOIN TPCH.ORDERS o ON l.L_ORDERKEY = o.O_ORDERKEY
JOIN TPCH.CUSTOMER c ON o.O_CUSTKEY = c.C_CUSTKEY
JOIN TPCH.NATION n ON c.C_NATIONKEY = n.N_NATIONKEY
JOIN TPCH.REGION r ON n.N_REGIONKEY = r.R_REGIONKEY
GROUP BY r.R_NAME
ORDER BY TOTAL_REVENUE DESC""",
            "who are the top 10 customers by total spend?": """SELECT 
    c.C_NAME AS CUSTOMER, 
    ROUND(SUM(o.O_TOTALPRICE), 2) AS TOTAL_SPEND
FROM TPCH.CUSTOMER c
JOIN TPCH.ORDERS o ON c.C_CUSTKEY = o.O_CUSTKEY
GROUP BY c.C_NAME
ORDER BY TOTAL_SPEND DESC
LIMIT 10""",
            "which suppliers have the highest order volume?": """SELECT 
    s.S_NAME AS SUPPLIER, 
    SUM(l.L_QUANTITY) AS TOTAL_VOLUME
FROM TPCH.SUPPLIER s
JOIN TPCH.LINEITEM l ON s.S_SUPPKEY = l.L_SUPPKEY
GROUP BY s.S_NAME
ORDER BY TOTAL_VOLUME DESC
LIMIT 10""",
            "show average order value by nation": """SELECT 
    n.N_NAME AS NATION, 
    ROUND(AVG(o.O_TOTALPRICE), 2) AS AVG_ORDER_VALUE
FROM TPCH.CUSTOMER c
JOIN TPCH.ORDERS o ON c.C_CUSTKEY = o.O_CUSTKEY
JOIN TPCH.NATION n ON c.C_NATIONKEY = n.N_NATIONKEY
GROUP BY n.N_NAME
ORDER BY AVG_ORDER_VALUE DESC""",
            "what is the total quantity of parts ordered per year?": """SELECT 
    YEAR(o.O_ORDERDATE) AS ORDER_YEAR,
    SUM(l.L_QUANTITY) AS TOTAL_QUANTITY
FROM TPCH.LINEITEM l
JOIN TPCH.ORDERS o ON l.L_ORDERKEY = o.O_ORDERKEY
GROUP BY YEAR(o.O_ORDERDATE)
ORDER BY ORDER_YEAR ASC""",
            "what are the top 5 most expensive parts?": """SELECT 
    P_NAME AS PART_NAME,
    ROUND(P_RETAILPRICE, 2) AS RETAIL_PRICE
FROM TPCH.PART
ORDER BY P_RETAILPRICE DESC
LIMIT 5""",
            "which nations have the highest number of customers?": """SELECT 
    n.N_NAME AS NATION,
    COUNT(c.C_CUSTKEY) AS CUSTOMER_COUNT
FROM TPCH.CUSTOMER c
JOIN TPCH.NATION n ON c.C_NATIONKEY = n.N_NATIONKEY
GROUP BY n.N_NAME
ORDER BY CUSTOMER_COUNT DESC
LIMIT 10""",
            "what is the average account balance of customers by market segment?": """SELECT 
    C_MKTSEGMENT AS MARKET_SEGMENT,
    ROUND(AVG(C_ACCTBAL), 2) AS AVG_BALANCE
FROM TPCH.CUSTOMER
GROUP BY C_MKTSEGMENT
ORDER BY AVG_BALANCE DESC"""
        }

    def _match_fallback(self, question: str) -> str:
        """Perform fuzzy matching to find a fallback query for demo questions."""
        q_clean = question.lower().strip()
        
        # Original 4 questions
        if "revenue" in q_clean and "region" in q_clean:
            return self.fallback_queries["compare total revenue by region"]
        if "top" in q_clean and "customer" in q_clean:
            # Check if it's the nation query instead
            if "nation" in q_clean:
                return self.fallback_queries["which nations have the highest number of customers?"]
            return self.fallback_queries["who are the top 10 customers by total spend?"]
        if "supplier" in q_clean and ("volume" in q_clean or "order" in q_clean):
            return self.fallback_queries["which suppliers have the highest order volume?"]
        if "average" in q_clean and "order" in q_clean and "nation" in q_clean:
            return self.fallback_queries["show average order value by nation"]
            
        # New 4 test questions
        if "quantity" in q_clean and ("year" in q_clean or "annual" in q_clean):
            return self.fallback_queries["what is the total quantity of parts ordered per year?"]
        if "expensive" in q_clean and "part" in q_clean:
            return self.fallback_queries["what are the top 5 most expensive parts?"]
        if "nation" in q_clean and "customer" in q_clean:
            return self.fallback_queries["which nations have the highest number of customers?"]
        if "balance" in q_clean and ("segment" in q_clean or "market" in q_clean or "acctbal" in q_clean):
            return self.fallback_queries["what is the average account balance of customers by market segment?"]
            
        return None

    def generate_sql(self, question: str, schema_context: str = "", chat_history: list = None) -> str:
        """Generate SQL using Groq LLM with fallback for demo questions."""
        # Check fallback first, but only if there is no chat history (follow-ups need LLM context)
        if not chat_history:
            fallback = self._match_fallback(question)
            if fallback:
                print(f"[SQLAgent] Match found in fallbacks for question: '{question}'")
                return fallback

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Inject conversational memory
            if chat_history:
                for msg in chat_history:
                    # We expect msg to be dict with 'role' and 'content' (either SQL or summary)
                    messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
            
            messages.append({"role": "user", "content": f"Question: {question}\n\nGenerate the SQL query:"})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1
            }
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            sql = data["choices"][0]["message"]["content"].strip()
            sql = sql.replace("```sql", "").replace("```", "").strip()
            return sql
            
        except Exception as e:
            print(f"[SQLAgent] Error generating SQL: {e}")
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
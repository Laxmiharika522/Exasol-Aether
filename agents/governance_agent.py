# Need this import at the top
import re

class GovernanceAgent:
    """
    Reviews SQL queries for safety before execution.
    Enforces read-only access and basic protection rules.
    """

    def __init__(self):
        # Operations that are never allowed
        self.forbidden_keywords = [
            "INSERT", "UPDATE", "DELETE", "DROP", "ALTER", 
            "TRUNCATE", "CREATE", "GRANT", "REVOKE", "MERGE", "REPLACE"
        ]

        # Columns we want to be careful with (basic PII protection)
        self.sensitive_columns = [
            "email", "phone", "mobile", "salary", "ssn", 
            "password", "credit", "card", "address"
        ]

    def review_query(self, sql: str) -> dict:
        """
        Review a SQL query and decide if it is safe.
        
        Returns:
            {
                "approved": True/False,
                "reason": "...",
                "sql": "original or modified sql"
            }
        """
        if not sql or not sql.strip():
            return {
                "approved": False,
                "reason": "Empty SQL query",
                "sql": sql
            }

        sql_upper = sql.upper()

        # 1. Block any write / dangerous operations
        for keyword in self.forbidden_keywords:
            if re.search(rf"\b{keyword}\b", sql_upper):
                return {
                    "approved": False,
                    "reason": f"Forbidden operation detected: {keyword}",
                    "sql": sql
                }

        # 2. Must be a SELECT (basic safety)
        if not sql_upper.strip().startswith("SELECT"):
            return {
                "approved": False,
                "reason": "Only SELECT queries are allowed",
                "sql": sql
            }

        # 3. Passed all checks
        return {
            "approved": True,
            "reason": "Query is safe (read-only)",
            "sql": sql
        }



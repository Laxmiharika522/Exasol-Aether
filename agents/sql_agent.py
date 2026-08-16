from utils.db import get_connection

class SQLAgent:
    """
    Responsible for generating and executing SQL queries on Exasol.
    """

    def __init__(self):
        self.conn = get_connection()

    def execute_query(self, sql: str):
        """Execute a SQL query and return the results."""
        try:
            result = self.conn.execute(sql).fetchall()
            return {
                "success": True,
                "data": result,
                "row_count": len(result)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def close(self):
        self.conn.close()
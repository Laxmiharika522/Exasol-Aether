from utils.db import get_connection

class SchemaAgent:
    """
    Agent responsible for discovering schemas, tables, and columns
    using Exasol (will later also use MCP).
    """

    def __init__(self):
        self.conn = get_connection()

    def list_schemas(self):
        """Return all schema names."""
        rows = self.conn.execute(
            "SELECT SCHEMA_NAME FROM EXA_SCHEMAS ORDER BY 1"
        ).fetchall()
        return [r[0] for r in rows]

    def list_tables(self, schema: str = None):
        """Return tables, optionally filtered by schema."""
        if schema:
            query = f"""
                SELECT TABLE_SCHEMA, TABLE_NAME 
                FROM EXA_ALL_TABLES 
                WHERE TABLE_SCHEMA = '{schema}'
                ORDER BY TABLE_NAME
            """
        else:
            query = """
                SELECT TABLE_SCHEMA, TABLE_NAME 
                FROM EXA_ALL_TABLES 
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
        return self.conn.execute(query).fetchall()

    def describe_table(self, schema: str, table: str):
        """Return column information for a table."""
        query = f"""
            SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_IS_NULLABLE
            FROM EXA_ALL_COLUMNS
            WHERE COLUMN_SCHEMA = '{schema}' AND COLUMN_TABLE = '{table}'
            ORDER BY COLUMN_ORDINAL_POSITION
        """
        return self.conn.execute(query).fetchall()

    def close(self):
        self.conn.close()
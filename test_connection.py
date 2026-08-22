import pyexasol
from dotenv import load_dotenv
import os

load_dotenv()

dsn = os.getenv("EXA_DSN")
user = os.getenv("EXA_USER")
password = os.getenv("EXA_PASSWORD")

print(f"Connecting to: {dsn} as {user}")

conn = pyexasol.connect(
    dsn=dsn,
    user=user,
    password=password,
    encryption=True,
    websocket_sslopt={"cert_reqs": 0}
)

print("SUCCESS: Connected to Exasol successfully!\n")

# Test basic query first
result = conn.execute("SELECT 1").fetchone()
print(f"Basic test: {result}")

# Check what schemas exist
schemas = conn.execute("SELECT SCHEMA_NAME FROM EXA_SCHEMAS ORDER BY 1").fetchall()
print(f"\nAvailable schemas: {[r[0] for r in schemas]}")

conn.close()
print("\nConnection closed.")
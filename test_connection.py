import pyexasol
from dotenv import load_dotenv
import os

load_dotenv()

conn = pyexasol.connect(
    dsn="127.0.0.1:8563",
    user="sys",
    password="t2r5wQ4HjkibyIrL85zwnEJJ",
    encryption=True,
    websocket_sslopt={"cert_reqs": 0}  # needed for self-signed certificate
)

print("✅ Connected to Exasol successfully!\n")

# Test query - show a few customers
result = conn.execute("""
    SELECT C_CUSTKEY, C_NAME, C_NATIONKEY, C_ACCTBAL
    FROM TPCH.CUSTOMER
    LIMIT 5
""").fetchall()

print("Sample customers from TPCH.CUSTOMER:")
for row in result:
    print(row)

conn.close()
print("\nConnection closed.")
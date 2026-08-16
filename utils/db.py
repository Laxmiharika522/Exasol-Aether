import os
import pyexasol
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Create and return a connection to Exasol."""
    return pyexasol.connect(
        dsn=os.getenv("EXA_DSN", "127.0.0.1:8563"),
        user=os.getenv("EXA_USER", "sys"),
        password=os.getenv("EXA_PASSWORD"),
        encryption=True,
        websocket_sslopt={"cert_reqs": 0}  # for self-signed cert
    )

def test_connection():
    """Simple test to verify connection works."""
    try:
        conn = get_connection()
        result = conn.execute("SELECT 1").fetchone()
        conn.close()
        return result[0] == 1
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
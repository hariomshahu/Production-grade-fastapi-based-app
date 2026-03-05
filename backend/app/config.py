"""App configuration from environment variables."""
import os

TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "items")
# Bind to 0.0.0.0 in dev (Docker/local), 127.0.0.1 when behind Nginx
BIND_HOST = os.environ.get("BIND_HOST", "0.0.0.0")
BIND_PORT = int(os.environ.get("BIND_PORT", "8000"))

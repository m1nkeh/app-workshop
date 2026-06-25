"""Environment-aware Lakebase connection, shared by the app and any migrations.

Deployed it reads the injected PG vars and connects as the app SP; local it
loads .env and connects as you. See the README for the full model. No caching
here on purpose: the app wraps make_engine() in @st.cache_resource and Alembic
builds it once per run, so the cache belongs in those callers, not this module.
"""
import os

from databricks.sdk import WorkspaceClient
from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine

# DATABRICKS_CLIENT_ID is injected only when running as the SP; absent locally.
IS_DEPLOYED = bool(os.getenv("DATABRICKS_CLIENT_ID"))

if not IS_DEPLOYED:
    load_dotenv(find_dotenv())  # walks up from src/app to the repo-root .env


# Who and where we connect: the app SP when deployed, you locally.
def connection_params(client: WorkspaceClient | None = None) -> dict:
    endpoint = os.environ["LAKEBASE_ENDPOINT"]
    if IS_DEPLOYED:
        host = os.environ["PGHOST"]                                        # injected by the platform
        user = os.environ["PGUSER"]                                        # SP client id, injected
    else:
        w = client or WorkspaceClient()
        user = w.current_user.me().user_name                               # your email = your PG role
        host = w.postgres.get_endpoint(name=endpoint).status.hosts.host    # derived from the endpoint
    return {
        "host": host,
        "dbname": os.getenv("PGDATABASE", "databricks_postgres"),
        "user": user,
        "endpoint": endpoint,
    }


# Pooled engine that mints a fresh OAuth token per connection.
def make_engine():
    import psycopg

    w = WorkspaceClient()
    p = connection_params(w)

    def creator():  # fresh token per physical connection the pool opens
        token = w.postgres.generate_database_credential(endpoint=p["endpoint"]).token
        # No port (libpq defaults to 5432), no sslmode (Lakebase enforces TLS).
        return psycopg.connect(
            host=p["host"], dbname=p["dbname"], user=p["user"], password=token,
        )

    return create_engine(
        "postgresql+psycopg://",
        creator=creator,
        pool_recycle=3300,   # before the 1-hour token TTL
        pool_pre_ping=True,  # survive scale-to-zero wake-ups
    )

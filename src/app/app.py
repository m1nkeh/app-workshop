"""App starter: prove the Lakebase connection. See README."""
import streamlit as st
from sqlalchemy import text

import db

st.set_page_config(page_title="App starter", page_icon="🚀")
st.title("App starter")
st.caption("Verified plumbing only. App features get built on top during the workshop.")


# Pooled engine, built once per session.
@st.cache_resource
def get_engine():
    return db.make_engine()


# Connection identity, for the sidebar readout.
@st.cache_data
def get_params():
    return db.connection_params()


params = get_params()

# Sidebar: are we connected as you (local) or the app SP (deployed)?
with st.sidebar:
    st.subheader("Connection")
    st.metric("Environment", "Deployed (SP)" if db.IS_DEPLOYED else "Local (you)")
    st.write(f"Identity: `{params['user']}`")
    st.write(f"Host: `{params['host']}`")
    st.write(f"Endpoint: `{params['endpoint']}`")

st.subheader("Database round-trip")
st.write(
    "Connection only, no tables yet. During the lab you create the `app` schema and "
    "your table as yourself (SQL Editor or `databricks psql`); locally you own them, so "
    "the deployed SP cannot see them until granted."
)

# Round-trip: report who we connected as, and list any tables in schema app.
if st.button("Ping database"):
    try:
        with get_engine().connect() as conn:
            who = conn.execute(text("select current_user, current_database()")).one()
            tables = conn.execute(text(
                "select table_name from information_schema.tables "
                "where table_schema = 'app' order by table_name"
            )).scalars().all()
        st.success(f"Connected as `{who[0]}` to `{who[1]}`")
        st.write(
            "Tables in schema `app`:",
            tables or "(none yet, you create the schema during the lab)",
        )
    except Exception as e:  # noqa: BLE001  (surface the raw error in the lab)
        st.error(f"Connection failed: {e}")

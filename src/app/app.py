import io
import re

from sqlalchemy import text
import streamlit as st

import db

st.set_page_config(page_title="Receipts App", page_icon="🍃", layout="wide")

# Sidebar (>=640px only): fluid width, no drag, no collapse. Below 640px we
# leave Streamlit's native sidebar alone -- pinning it open would eat the
# whole screen on a phone. Both aria-expanded values are matched because
# Streamlit's own collapsed-state rule is equally specific and wins ties
# otherwise. Selectors are Streamlit internals (checked on 1.58).
st.markdown(
    """
    <style>
    @media (min-width: 640px) {
        section[data-testid="stSidebar"][aria-expanded="false"],
        section[data-testid="stSidebar"][aria-expanded="true"] {
            width: clamp(260px, 22vw, 342px) !important;
            min-width: 260px !important;
            max-width: 342px !important;
            transform: none !important;
            visibility: visible !important;
        }
        section[data-testid="stSidebar"] div[style*="cursor: col-resize"] {
            pointer-events: none !important;
        }
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stExpandSidebarButton"] {
            display: none !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Receipts App")
st.caption("Upload a receipt, log a row, see the list.")


# Pooled engine, built once per session.
@st.cache_resource
def get_engine():
    return db.make_engine()


# One WorkspaceClient for file (Volume) operations.
@st.cache_resource
def get_client():
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient()


# Connection identity, for the sidebar readout and the volume subfolder.
@st.cache_data
def get_params():
    return db.connection_params()


params = get_params()
identity = params["user"]  # your email locally, the app SP client id deployed
workspace_host = get_client().config.host
# params["endpoint"] is "projects/<PROJECT>/branches/<BRANCH>/endpoints/primary"
# in both environments, so project/branch are just a slice of it.
project_branch_match = re.search(r"^projects/([^/]+)/branches/([^/]+)/", params["endpoint"])
lakebase_project = project_branch_match.group(1) if project_branch_match else None
lakebase_branch = project_branch_match.group(2) if project_branch_match else None

# Sidebar: are we connected as you (local) or the app SP (deployed)?
with st.sidebar:
    st.subheader("Connection")
    st.metric("Environment", "Deployed (SP)" if db.IS_DEPLOYED else "Local (you)")
    st.caption("Identity")
    st.write(identity)
    st.caption("Postgres host")
    st.write(params["host"])
    st.caption("Workspace")
    st.write(workspace_host)
    if lakebase_project:
        st.caption("Lakebase project")
        st.write(lakebase_project)
    if lakebase_branch:
        st.caption("Lakebase branch")
        st.write(lakebase_branch)
    st.caption("Unity Catalog volume")
    st.write(db.volume_path())


# --- Upload: file to the Volume, then one row to app.receipts -----------------
st.subheader("Add a receipt")
with st.form("upload", clear_on_submit=True):
    uploaded = st.file_uploader("Receipt file", type=None)
    col1, col2, col3 = st.columns(3)
    merchant = col1.text_input("Merchant (optional)")
    amount = col2.number_input("Amount (optional)", min_value=0.0, value=None, format="%.2f")
    txn_date = col3.date_input("Date (optional)", value=None)
    submitted = st.form_submit_button("Upload", type="primary")

if submitted:
    if uploaded is None:
        st.warning("Pick a file first.")
    else:
        try:
            # Identity subfolder, not flattened -- keeps attendees and the SP
            # from colliding in the shared volume.
            file_path = f"{db.volume_path()}/{identity}/{uploaded.name}"
            get_client().files.upload(
                file_path, io.BytesIO(uploaded.getvalue()), overwrite=True
            )
            # merchant/amount/date are hand-entered for now; ai_parse_document
            # fills them in later. status isn't set here -- it defaults to
            # 'submitted' in the schema.
            with get_engine().begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO app.receipts "
                        "(owner, filename, file_path, merchant, amount, txn_date) "
                        "VALUES (:owner, :filename, :file_path, :merchant, :amount, :txn_date)"
                    ),
                    {
                        "owner": identity,
                        "filename": uploaded.name,
                        "file_path": file_path,
                        "merchant": merchant or None,
                        "amount": amount,
                        "txn_date": txn_date,
                    },
                )
            st.success(f"Stored `{uploaded.name}` and logged a row.")
        except Exception as e:  # noqa: BLE001  (surface the raw error in the lab)
            st.error(f"Upload failed: {e}")


# --- List: everything in app.receipts ----------------------------------------
st.subheader("Receipts")
st.caption(
    "Every row, no filtering yet. The RBAC lab adds row-level security so "
    "submitters see only their own and approvers see the pending queue."
)
try:
    with get_engine().connect() as conn:
        rows = conn.execute(
            text(
                # id::text so the uuid renders as a string, not raw bytes.
                "SELECT id::text AS id, owner, filename, merchant, amount, txn_date, status, created_at "
                "FROM app.receipts ORDER BY created_at DESC"
            )
        ).mappings().all()
    if rows:
        st.dataframe([dict(r) for r in rows], use_container_width=True, hide_index=True)
    else:
        st.info("No receipts yet. Upload one above.")
except Exception as e:  # noqa: BLE001  (surface the raw error in the lab)
    st.error(f"Could not read receipts: {e}")

"""Seed demo receipts for the RBAC lab: a few fake submitters, all pending, so
the approver has a queue and the attendee only sees their own rows.

Not a migration -- demo data must never ship when the schema promotes to main.

Run from src/app: uv run python seed.py
Re-runnable: clears only the fake rows, never the attendee's own.
"""
from sqlalchemy import text

import db

# (owner, merchant, amount); each becomes a status='submitted' receipt.
ROWS = [
    ("alice@example.com", "Blue Bottle",   4.50),
    ("alice@example.com", "Uber",         23.10),
    ("bob@example.com",   "Pret",         12.75),
    ("bob@example.com",   "Premier Inn",  89.00),
    ("carol@example.com", "KLM",         210.40),
    ("carol@example.com", "Nando's",      31.20),
]

# file_path is NOT NULL; a placeholder is fine since the list view only shows
# metadata and no file needs to exist.
FILE_PATH = f"{db.volume_path()}/seed/sample_receipt.jpg"

with db.make_engine().begin() as conn:
    conn.execute(text("DELETE FROM app.receipts WHERE owner LIKE '%@example.com'"))
    for owner, merchant, amount in ROWS:
        conn.execute(
            text(
                "INSERT INTO app.receipts (owner, filename, file_path, merchant, amount, status) "
                "VALUES (:owner, 'sample_receipt.jpg', :path, :merchant, :amount, 'submitted')"
            ),
            {"owner": owner, "path": FILE_PATH, "merchant": merchant, "amount": amount},
        )

print(f"seeded {len(ROWS)} pending receipts from fake submitters")

"""
tests/conftest.py
-----------------
Shared pytest fixtures for the banking application test suite.

Strategy
--------
* Each test function gets a fresh temporary SQLite file on disk.
  This avoids all in-memory connection-sharing problems — every call to
  get_connection() naturally opens and closes its own connection to the
  same file, exactly as in production.
* The tmp_path fixture (built into pytest) creates an isolated temp
  directory per test that is cleaned up automatically.
"""

import os
import sys
import sqlite3
import pytest

# ── Make BACKEND importable ──────────────────────────────────────────────────
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "BACKEND"))
sys.path.insert(0, BACKEND_DIR)

# ── Import config and patch DATABASE_PATH (will be updated per test) ─────────
import config as _cfg

# Patch it to a sentinel — each test's reset_db will set it to a real temp file
_cfg.DATABASE_PATH = None

# ── Import app ONCE after config is patched ──────────────────────────────────
import app as _app_module

_flask_app = _app_module.app
_flask_app.config["TESTING"] = True


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_db(tmp_path):
    """
    Point DATABASE_PATH at a fresh temporary file and initialise the schema.
    Runs before every test; the tmp_path directory is auto-cleaned by pytest.
    """
    db_file = str(tmp_path / "test_bank.db")
    _cfg.DATABASE_PATH = db_file

    from models.db import init_db
    init_db()
    yield

    # Ensure no lingering connections hold the file open
    _cfg.DATABASE_PATH = None


@pytest.fixture
def app_client():
    """Flask test client pointing at the per-test temporary database."""
    with _flask_app.test_client() as client:
        yield client


@pytest.fixture
def seeded_client(app_client, reset_db):
    """
    app_client with one pre-inserted customer:
        username : testuser
        password : testpass123
        balance  : 1000.00
    """
    from werkzeug.security import generate_password_hash
    from models.db import get_connection

    conn = get_connection()
    hashed = generate_password_hash("testpass123")
    cursor = conn.execute(
        "INSERT INTO customers (username, password, full_name) VALUES (?, ?, ?)",
        ("testuser", hashed, "Test User"),
    )
    customer_id = cursor.lastrowid
    conn.execute(
        "INSERT INTO accounts (customer_id, balance) VALUES (?, ?)",
        (customer_id, 1000.00),
    )
    conn.commit()
    conn.close()
    yield app_client

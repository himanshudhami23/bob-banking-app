"""
models/db.py
------------
Database connection helper and schema initialisation.
All database interactions in the application flow through this module.
"""

import sqlite3
import os
import sys

# Resolve the database path from config regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config as _config


def _db_path():
    """Return the current DATABASE_PATH (allows tests to override config.DATABASE_PATH)."""
    return _config.DATABASE_PATH


def get_connection():
    """
    Open and return a connection to the SQLite database.

    Rows are returned as sqlite3.Row objects, which support both
    index-based and name-based column access (e.g., row['balance']).
    The connection uses WAL journal mode for better concurrency
    behaviour under Flask's development server.
    """
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """
    Create database tables if they do not already exist.

    Safe to call on every application startup — uses
    CREATE TABLE IF NOT EXISTS to avoid wiping existing data.

    Tables:
        customers    — registered account holders and their hashed passwords
        accounts     — one account per customer, tracks current balance
        transactions — immutable log of every deposit and withdrawal

    Note: The connection is NOT closed here intentionally.  When running
    under tests the patched get_connection() returns a shared in-memory
    connection that must stay open.  Under the real application a new
    connection is opened per request anyway, so leaving this one open is
    harmless; it will be garbage-collected when the process exits.
    """
    conn = get_connection()
    close_after = _db_path() != ":memory:"
    cursor = conn.cursor()
    try:

        # ------------------------------------------------------------------
        # customers: holds login credentials for each registered customer
        # ------------------------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                username   TEXT    NOT NULL UNIQUE,
                password   TEXT    NOT NULL,          -- bcrypt/pbkdf2 hash
                full_name  TEXT    NOT NULL,
                created_at DATETIME DEFAULT (datetime('now'))
            )
        """)

        # ------------------------------------------------------------------
        # accounts: one row per customer, stores the current balance
        # ------------------------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL UNIQUE,
                balance     REAL    NOT NULL DEFAULT 0.0
                                    CHECK (balance >= 0),   -- guard at DB level
                created_at  DATETIME DEFAULT (datetime('now')),
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        """)

        # ------------------------------------------------------------------
        # transactions: append-only log — never updated, only inserted
        # ------------------------------------------------------------------
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id      INTEGER NOT NULL,
                type            TEXT    NOT NULL CHECK (type IN ('deposit','withdrawal')),
                amount          REAL    NOT NULL CHECK (amount > 0),
                balance_after   REAL    NOT NULL,
                created_at      DATETIME DEFAULT (datetime('now')),
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        """)

        conn.commit()
    finally:
        if close_after:
            conn.close()

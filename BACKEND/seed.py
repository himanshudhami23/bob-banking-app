"""
seed.py
-------
One-time database seeding script.

Run this ONCE after the database has been initialised to insert
test customer accounts. It is safe to re-run — it checks whether
each username already exists before inserting.

Usage (from the BACKEND/ directory, with venv activated):
    python seed.py

Seeded accounts
---------------
    username: alice    password: alice123    starting balance: $5,000.00
    username: bob      password: bob456      starting balance: $2,500.00
"""

import os
import sys

# Ensure BACKEND/ is on the path so imports work from any working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash
from models.db import get_connection, init_db

# ── Seed data ─────────────────────────────────────────────────────────────────
CUSTOMERS = [
    {
        "username":        "alice",
        "password":        "alice123",
        "full_name":       "Alice Johnson",
        "initial_balance": 5000.00,
    },
    {
        "username":        "bob",
        "password":        "bob456",
        "full_name":       "Bob Martinez",
        "initial_balance": 2500.00,
    },
]


def seed():
    # Make sure tables exist before inserting
    init_db()

    conn = get_connection()
    try:
        inserted = 0
        skipped  = 0

        for cust in CUSTOMERS:
            # Check if this username already exists
            existing = conn.execute(
                "SELECT id FROM customers WHERE username = ?",
                (cust["username"],)
            ).fetchone()

            if existing:
                print(f"  [skip]  '{cust['username']}' already exists — skipping.")
                skipped += 1
                continue

            # Hash the plain-text password
            hashed_pw = generate_password_hash(cust["password"])

            # Insert the customer row
            cursor = conn.execute(
                "INSERT INTO customers (username, password, full_name) VALUES (?, ?, ?)",
                (cust["username"], hashed_pw, cust["full_name"])
            )
            customer_id = cursor.lastrowid

            # Insert the corresponding account row with the initial balance
            conn.execute(
                "INSERT INTO accounts (customer_id, balance) VALUES (?, ?)",
                (customer_id, cust["initial_balance"])
            )

            print(f"  [ok]    '{cust['username']}' ({cust['full_name']}) "
                  f"— balance: ${cust['initial_balance']:,.2f}")
            inserted += 1

        conn.commit()
        print(f"\nSeeding complete: {inserted} inserted, {skipped} skipped.")

    finally:
        conn.close()


if __name__ == "__main__":
    print("Seeding database...\n")
    seed()

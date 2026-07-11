"""
models/customer_model.py
------------------------
Data-access functions for the 'customers' table.
No business logic lives here — only raw database reads.
"""

from .db import get_connection


def find_by_username(username: str):
    """
    Look up a customer record by username.

    Returns a sqlite3.Row (dict-like) containing all columns if found,
    or None if no matching customer exists.

    The caller (auth_service) is responsible for all credential
    comparison and session management.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT id, username, password, full_name FROM customers WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        return row  # None if not found
    finally:
        conn.close()


def find_by_id(customer_id: int):
    """
    Look up a customer record by primary key.

    Used after login to refresh customer details from the database
    when needed (e.g., displaying the full name on the dashboard).
    Returns a sqlite3.Row or None.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT id, username, full_name FROM customers WHERE id = ?",
            (customer_id,)
        )
        return cursor.fetchone()
    finally:
        conn.close()

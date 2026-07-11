"""
models/account_model.py
-----------------------
Data-access functions for the 'accounts' and 'transactions' tables.

Key design constraints:
  • Every balance-modifying operation updates 'accounts' AND inserts
    into 'transactions' in a SINGLE database transaction (one commit).
    This guarantees the balance and the audit log are always in sync.
  • No business-rule logic lives here (e.g., no insufficient-funds check).
    That belongs in account_service.py.
"""

from .db import get_connection


def get_balance(customer_id: int):
    """
    Return the current balance for the given customer as a float,
    or None if no account row exists for that customer.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT balance FROM accounts WHERE customer_id = ?",
            (customer_id,)
        )
        row = cursor.fetchone()
        return float(row["balance"]) if row else None
    finally:
        conn.close()


def get_account_id(customer_id: int):
    """
    Return the account primary key (id) for a given customer,
    or None if no account row exists.
    Needed internally to insert transaction log records.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT id FROM accounts WHERE customer_id = ?",
            (customer_id,)
        )
        row = cursor.fetchone()
        return row["id"] if row else None
    finally:
        conn.close()


def apply_transaction(customer_id: int, txn_type: str, amount: float, new_balance: float):
    """
    Atomically update the account balance and record the transaction log entry.

    Parameters
    ----------
    customer_id : int   — the customer whose account is being updated
    txn_type    : str   — 'deposit' or 'withdrawal'
    amount      : float — the positive amount of this transaction
    new_balance : float — the balance after the transaction (pre-computed by the service)

    Raises
    ------
    ValueError  — if the account for the given customer_id does not exist
    sqlite3.Error — propagated as-is if the database write fails

    The function opens one connection, runs both the UPDATE and INSERT
    inside that connection's implicit transaction, then commits once.
    If anything fails before the commit, both operations are rolled back
    automatically by SQLite.
    """
    conn = get_connection()
    try:
        # Fetch the account id within the same connection
        cursor = conn.execute(
            "SELECT id FROM accounts WHERE customer_id = ?",
            (customer_id,)
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"No account found for customer_id={customer_id}")
        account_id = row["id"]

        # 1. Update the balance
        conn.execute(
            "UPDATE accounts SET balance = ? WHERE id = ?",
            (new_balance, account_id)
        )

        # 2. Insert the transaction log entry
        conn.execute(
            """
            INSERT INTO transactions (account_id, type, amount, balance_after)
            VALUES (?, ?, ?, ?)
            """,
            (account_id, txn_type, amount, new_balance)
        )

        # Single commit — both writes succeed or neither does
        conn.commit()
        return new_balance

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_recent_transactions(customer_id: int, limit: int = 5):
    """
    Return the most recent `limit` transactions for a customer,
    newest first. Used by the dashboard to show transaction history.
    Returns a list of sqlite3.Row objects (empty list if none).
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT t.type, t.amount, t.balance_after, t.created_at
            FROM   transactions t
            JOIN   accounts a ON a.id = t.account_id
            WHERE  a.customer_id = ?
            ORDER  BY t.created_at DESC
            LIMIT  ?
            """,
            (customer_id, limit)
        )
        return cursor.fetchall()
    finally:
        conn.close()

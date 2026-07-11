"""
services/account_service.py
----------------------------
Business logic for balance enquiry and financial transactions.

Responsibilities:
  • Retrieve current balance (always from the database, never cached)
  • Validate deposit and withdrawal amounts
  • Enforce the insufficient-funds rule for withdrawals
  • Delegate the actual database write to account_model

No SQL queries live here — only business rules and orchestration.
"""

from models.account_model import get_balance, apply_transaction, get_recent_transactions

# Maximum single transaction amount (configurable ceiling)
MAX_TRANSACTION_AMOUNT = 1_000_000.00


def fetch_balance(customer_id: int) -> dict:
    """
    Retrieve the current account balance for a customer.

    Returns
    -------
    dict:
        success (bool)
        balance (float | None)
        error   (str | None)
    """
    balance = get_balance(customer_id)
    if balance is None:
        return {"success": False, "balance": None, "error": "Account not found."}
    return {"success": True, "balance": balance, "error": None}


def deposit(customer_id: int, raw_amount) -> dict:
    """
    Process a deposit for the given customer.

    Parameters
    ----------
    customer_id : int      — the logged-in customer
    raw_amount  : any      — the raw value from request.form (may be a string)

    Returns
    -------
    dict:
        success     (bool)
        new_balance (float | None)
        error       (str | None)
    """
    # --- Validate the amount ---
    amount, error = _validate_amount(raw_amount)
    if error:
        return {"success": False, "new_balance": None, "error": error}

    # --- Fetch current balance ---
    current_balance = get_balance(customer_id)
    if current_balance is None:
        return {"success": False, "new_balance": None, "error": "Account not found."}

    # --- Compute new balance ---
    new_balance = round(current_balance + amount, 2)

    # --- Persist atomically ---
    try:
        apply_transaction(customer_id, "deposit", amount, new_balance)
    except Exception as exc:
        return {"success": False, "new_balance": None, "error": f"Transaction failed: {exc}"}

    return {"success": True, "new_balance": new_balance, "error": None}


def withdraw(customer_id: int, raw_amount) -> dict:
    """
    Process a withdrawal for the given customer.

    Additional rule beyond deposit: the amount must not exceed
    the current balance. The balance check is performed BEFORE
    any database write.

    Parameters / Returns: same shape as deposit().
    """
    # --- Validate the amount ---
    amount, error = _validate_amount(raw_amount)
    if error:
        return {"success": False, "new_balance": None, "error": error}

    # --- Fetch current balance (authoritative read — never use a cached value) ---
    current_balance = get_balance(customer_id)
    if current_balance is None:
        return {"success": False, "new_balance": None, "error": "Account not found."}

    # --- Insufficient-funds check ---
    if amount > current_balance:
        return {
            "success": False,
            "new_balance": None,
            "error": "Insufficient funds. Please enter an amount within your available balance.",
        }

    # --- Compute new balance ---
    new_balance = round(current_balance - amount, 2)

    # --- Persist atomically ---
    try:
        apply_transaction(customer_id, "withdrawal", amount, new_balance)
    except Exception as exc:
        return {"success": False, "new_balance": None, "error": f"Transaction failed: {exc}"}

    return {"success": True, "new_balance": new_balance, "error": None}


def fetch_recent_transactions(customer_id: int, limit: int = 5) -> list:
    """
    Return a list of the most recent transactions for the dashboard.
    Each item is a sqlite3.Row with keys: type, amount, balance_after, created_at.
    """
    return get_recent_transactions(customer_id, limit)


# ── Private helpers ───────────────────────────────────────────────────────────

def _validate_amount(raw_amount) -> tuple:
    """
    Convert raw_amount to a positive float within the allowed range.

    Returns (amount: float, error: None) on success,
    or      (None, error: str)           on failure.
    """
    # Attempt numeric conversion
    try:
        amount = float(str(raw_amount).strip())
    except (TypeError, ValueError):
        return None, "Please enter a valid numeric amount."

    # Must be strictly positive
    if amount <= 0:
        return None, "Amount must be greater than zero."

    # Reasonable upper bound
    if amount > MAX_TRANSACTION_AMOUNT:
        return None, f"Amount exceeds the maximum allowed per transaction (${MAX_TRANSACTION_AMOUNT:,.2f})."

    # Round to 2 decimal places to avoid floating-point drift
    amount = round(amount, 2)
    return amount, None

"""
services/auth_service.py
------------------------
Business logic for customer authentication.

Responsibilities:
  • Verify submitted credentials against the stored password hash
  • Return a structured result dict (never raise on business failures)
  • Never distinguish between "user not found" and "wrong password"
    in the error message (prevents username enumeration)

No session manipulation happens here — that belongs in the route layer.
"""

from werkzeug.security import check_password_hash
from models.customer_model import find_by_username


def login(username: str, password: str) -> dict:
    """
    Verify a customer's credentials.

    Parameters
    ----------
    username : str — the submitted username (stripped of leading/trailing whitespace)
    password : str — the submitted plain-text password

    Returns
    -------
    dict with keys:
        success   (bool)  — True if credentials are valid
        customer  (dict)  — {'id': int, 'full_name': str} on success, None on failure
        error     (str)   — Human-readable error message on failure, None on success
    """
    # Normalise input — strip whitespace
    username = (username or "").strip()
    password = (password or "").strip()

    # Blank-field guard — return early before hitting the database
    if not username or not password:
        return _failure("Username and password are required.")

    # Attempt to find the customer record
    customer = find_by_username(username)

    # Deliberately identical error message for "not found" and "wrong password"
    if customer is None:
        return _failure("Invalid username or password.")

    # Timing-safe hash comparison via Werkzeug
    if not check_password_hash(customer["password"], password):
        return _failure("Invalid username or password.")

    # Credentials verified — return only the data the route needs for the session
    return {
        "success": True,
        "customer": {
            "id": customer["id"],
            "full_name": customer["full_name"],
        },
        "error": None,
    }


# ── Private helpers ───────────────────────────────────────────────────────────

def _failure(message: str) -> dict:
    return {"success": False, "customer": None, "error": message}

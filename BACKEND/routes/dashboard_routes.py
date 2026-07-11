"""
routes/dashboard_routes.py
--------------------------
Handles the main dashboard view for authenticated customers.

Endpoints:
    GET /dashboard — Display the customer's account summary
"""

from flask import Blueprint, render_template, session
from utils import login_required
from services.account_service import fetch_balance, fetch_recent_transactions

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard", methods=["GET"])
@login_required
def dashboard_page():
    """
    Render the customer dashboard.

    Reads the customer identity from the session, fetches the current
    balance and recent transaction history from the database, then
    renders the dashboard template with that data.

    The session guard (login_required) guarantees that session['customer_id']
    is present before this function body executes.
    """
    customer_id = session["customer_id"]
    full_name   = session["full_name"]

    balance_result = fetch_balance(customer_id)
    recent_txns    = fetch_recent_transactions(customer_id, limit=5)

    # If the account is somehow missing, show a safe error state
    balance = balance_result["balance"] if balance_result["success"] else "N/A"

    return render_template(
        "dashboard.html",
        full_name=full_name,
        balance=balance,
        transactions=recent_txns,
    )

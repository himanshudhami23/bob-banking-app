"""
routes/transaction_routes.py
-----------------------------
Handles deposit and withdrawal endpoints.

Endpoints:
    GET  /deposit   — Display the deposit form
    POST /deposit   — Process a deposit submission
    GET  /withdraw  — Display the withdrawal form
    POST /withdraw  — Process a withdrawal submission

All routes are protected by the login_required decorator.
Business logic is fully delegated to account_service.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from utils import login_required
from services.account_service import deposit as do_deposit, withdraw as do_withdraw

transactions_bp = Blueprint("transactions", __name__)


# ── Deposit ───────────────────────────────────────────────────────────────────

@transactions_bp.route("/deposit", methods=["GET"])
@login_required
def deposit_page():
    """Render the deposit form (empty, no pre-populated data)."""
    return render_template("deposit.html")


@transactions_bp.route("/deposit", methods=["POST"])
@login_required
def deposit_submit():
    """
    Process the deposit form submission.

    Reads the amount, calls the account service, then:
      - On success: redirects to /dashboard with a flash success message.
      - On failure: re-renders the deposit form with an inline error message.
    """
    customer_id = session["customer_id"]
    raw_amount  = request.form.get("amount", "")

    result = do_deposit(customer_id, raw_amount)

    if result["success"]:
        flash(f"Deposit of ${result['new_balance'] - _get_previous_balance(customer_id, result['new_balance'], raw_amount):.2f} successful! "
              f"New balance: ${result['new_balance']:,.2f}", "success")
        return redirect(url_for("dashboard.dashboard_page"))

    return render_template("deposit.html", error=result["error"]), 200


# ── Withdraw ──────────────────────────────────────────────────────────────────

@transactions_bp.route("/withdraw", methods=["GET"])
@login_required
def withdraw_page():
    """Render the withdrawal form (empty, no pre-populated data)."""
    return render_template("withdraw.html")


@transactions_bp.route("/withdraw", methods=["POST"])
@login_required
def withdraw_submit():
    """
    Process the withdrawal form submission.

    Reads the amount, calls the account service, then:
      - On success: redirects to /dashboard with a flash success message.
      - On failure: re-renders the withdrawal form with an inline error message.
    """
    customer_id = session["customer_id"]
    raw_amount  = request.form.get("amount", "")

    result = do_withdraw(customer_id, raw_amount)

    if result["success"]:
        try:
            amount_display = float(str(raw_amount).strip())
        except (TypeError, ValueError):
            amount_display = 0.0
        flash(f"Withdrawal of ${amount_display:,.2f} successful! "
              f"New balance: ${result['new_balance']:,.2f}", "success")
        return redirect(url_for("dashboard.dashboard_page"))

    return render_template("withdraw.html", error=result["error"]), 200


# ── Private helper ────────────────────────────────────────────────────────────

def _get_previous_balance(customer_id, new_balance, raw_amount):
    """
    Reconstruct the deposited amount for the flash message.
    We already have new_balance and raw_amount from the form;
    this simply parses raw_amount safely to produce a display value.
    """
    try:
        return float(str(raw_amount).strip())
    except (TypeError, ValueError):
        return 0.0

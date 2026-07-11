"""
routes/auth_routes.py
---------------------
Handles all authentication-related HTTP endpoints.

Endpoints:
    GET  /login   — Display the login form
    POST /login   — Process submitted credentials
    POST /logout  — Clear the session and redirect to login
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from services.auth_service import login as auth_login

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET"])
def login_page():
    """
    Display the login form.
    If the user is already authenticated, redirect straight to the dashboard
    so they are not shown a redundant login screen.
    """
    if session.get("customer_id"):
        return redirect(url_for("dashboard.dashboard_page"))
    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def login_submit():
    """
    Process the submitted login form.

    Reads username and password from request.form, delegates to the
    auth service for credential verification, then either:
      - Sets session keys and redirects to /dashboard (success), or
      - Re-renders the login page with an inline error message (failure).
    """
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    result = auth_login(username, password)

    if result["success"]:
        # Store only the minimum needed — never store the password or hash
        session["customer_id"] = result["customer"]["id"]
        session["full_name"]   = result["customer"]["full_name"]
        return redirect(url_for("dashboard.dashboard_page"))

    # Re-render the form; pass the error so the template can display it
    return render_template("login.html", error=result["error"]), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    Terminate the current session and send the user back to the login page.

    Uses POST (not GET) to prevent session termination via browser prefetch
    or link crawling. The logout button in the template is inside a <form
    method="POST"> for this reason.
    """
    session.clear()
    return redirect(url_for("auth.login_page"))

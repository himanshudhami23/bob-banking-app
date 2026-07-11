"""
tests/test_integration.py
--------------------------
Integration tests for the Flask routes and the database layer.

Uses the Flask test client and an in-memory SQLite database (configured
in conftest.py) to test real HTTP request → response cycles including
actual database reads and writes.

Fixtures (defined in conftest.py):
    app_client    — Flask test client with a clean DB
    seeded_client — Flask test client with one pre-loaded customer
                    (username=testuser, password=testpass123, balance=1000.00)
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "BACKEND")))


# ─────────────────────────────────────────────────────────────────────────────
# Helper: perform a login via the test client
# ─────────────────────────────────────────────────────────────────────────────

def do_login(client, username="testuser", password="testpass123"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Authentication route tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAuthRoutes:

    def test_get_login_page_returns_200(self, app_client):
        resp = app_client.get("/login")
        assert resp.status_code == 200

    def test_login_page_contains_form(self, app_client):
        resp = app_client.get("/login")
        assert b"username" in resp.data
        assert b"password" in resp.data

    def test_root_redirects_to_login(self, app_client):
        resp = app_client.get("/")
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_valid_login_redirects_to_dashboard(self, seeded_client):
        resp = do_login(seeded_client)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_invalid_password_returns_200(self, seeded_client):
        resp = do_login(seeded_client, password="wrongpassword")
        assert resp.status_code == 200

    def test_invalid_password_shows_error(self, seeded_client):
        resp = do_login(seeded_client, password="wrongpassword")
        assert b"Invalid username or password" in resp.data

    def test_unknown_user_shows_same_error(self, seeded_client):
        """Error message must be identical for unknown user and wrong password."""
        resp = do_login(seeded_client, username="nobody", password="anything")
        assert b"Invalid username or password" in resp.data

    def test_blank_username_shows_error(self, seeded_client):
        resp = do_login(seeded_client, username="", password="testpass123")
        assert resp.status_code == 200
        assert b"required" in resp.data.lower()

    def test_logout_clears_session_and_redirects(self, seeded_client):
        do_login(seeded_client)
        resp = seeded_client.post("/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_logout_then_dashboard_redirects_to_login(self, seeded_client):
        do_login(seeded_client)
        seeded_client.post("/logout")
        resp = seeded_client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard route tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDashboardRoute:

    def test_unauthenticated_dashboard_redirects(self, app_client):
        resp = app_client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_authenticated_dashboard_returns_200(self, seeded_client):
        do_login(seeded_client)
        resp = seeded_client.get("/dashboard", follow_redirects=True)
        assert resp.status_code == 200

    def test_dashboard_shows_customer_name(self, seeded_client):
        do_login(seeded_client)
        resp = seeded_client.get("/dashboard", follow_redirects=True)
        assert b"Test User" in resp.data

    def test_dashboard_shows_balance(self, seeded_client):
        do_login(seeded_client)
        resp = seeded_client.get("/dashboard", follow_redirects=True)
        assert b"1000.00" in resp.data


# ─────────────────────────────────────────────────────────────────────────────
# Deposit route tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDepositRoute:

    def test_unauthenticated_deposit_get_redirects(self, app_client):
        resp = app_client.get("/deposit", follow_redirects=False)
        assert resp.status_code == 302

    def test_authenticated_deposit_page_returns_200(self, seeded_client):
        do_login(seeded_client)
        resp = seeded_client.get("/deposit")
        assert resp.status_code == 200

    def test_valid_deposit_redirects_to_dashboard(self, seeded_client):
        do_login(seeded_client)
        resp = seeded_client.post(
            "/deposit", data={"amount": "500.00"}, follow_redirects=False
        )
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_valid_deposit_updates_balance(self, seeded_client):
        do_login(seeded_client)
        seeded_client.post("/deposit", data={"amount": "500.00"})
        resp = seeded_client.get("/dashboard")
        assert b"1500.00" in resp.data

    def test_zero_deposit_shows_error(self, seeded_client):
        do_login(seeded_client)
        resp = seeded_client.post("/deposit", data={"amount": "0"})
        assert resp.status_code == 200
        assert b"greater than zero" in resp.data.lower() or b"valid" in resp.data.lower()

    def test_negative_deposit_shows_error(self, seeded_client):
        do_login(seeded_client)
        resp = seeded_client.post("/deposit", data={"amount": "-100"})
        assert resp.status_code == 200
        assert b"error" in resp.data.lower() or b"greater" in resp.data.lower()

    def test_non_numeric_deposit_shows_error(self, seeded_client):
        do_login(seeded_client)
        resp = seeded_client.post("/deposit", data={"amount": "abc"})
        assert resp.status_code == 200
        assert b"valid" in resp.data.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Withdrawal route tests
# ─────────────────────────────────────────────────────────────────────────────

class TestWithdrawRoute:

    def test_unauthenticated_withdraw_get_redirects(self, app_client):
        resp = app_client.get("/withdraw", follow_redirects=False)
        assert resp.status_code == 302

    def test_authenticated_withdraw_page_returns_200(self, seeded_client):
        do_login(seeded_client)
        resp = seeded_client.get("/withdraw")
        assert resp.status_code == 200

    def test_valid_withdrawal_redirects_to_dashboard(self, seeded_client):
        do_login(seeded_client)
        resp = seeded_client.post(
            "/withdraw", data={"amount": "200.00"}, follow_redirects=False
        )
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_valid_withdrawal_updates_balance(self, seeded_client):
        do_login(seeded_client)
        seeded_client.post("/withdraw", data={"amount": "400.00"})
        resp = seeded_client.get("/dashboard")
        assert b"600.00" in resp.data

    def test_over_balance_withdrawal_shows_error(self, seeded_client):
        do_login(seeded_client)
        resp = seeded_client.post("/withdraw", data={"amount": "9999.00"})
        assert resp.status_code == 200
        assert b"insufficient" in resp.data.lower()

    def test_exact_balance_withdrawal_succeeds(self, seeded_client):
        do_login(seeded_client)
        resp = seeded_client.post(
            "/withdraw", data={"amount": "1000.00"}, follow_redirects=False
        )
        assert resp.status_code == 302

    def test_zero_withdrawal_shows_error(self, seeded_client):
        do_login(seeded_client)
        resp = seeded_client.post("/withdraw", data={"amount": "0"})
        assert resp.status_code == 200

    def test_non_numeric_withdrawal_shows_error(self, seeded_client):
        do_login(seeded_client)
        resp = seeded_client.post("/withdraw", data={"amount": "xyz"})
        assert resp.status_code == 200
        assert b"valid" in resp.data.lower()

"""
tests/test_auth_service.py
--------------------------
Unit tests for services/auth_service.py

These tests verify that the authentication business logic behaves
correctly in complete isolation — the model layer is patched with
controlled fakes so no real database is needed.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "BACKEND")))

from unittest.mock import patch
from werkzeug.security import generate_password_hash
from services.auth_service import login


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_customer(username="alice", password_plain="alice123", full_name="Alice Johnson"):
    """Return a dict that mimics a sqlite3.Row customer record."""
    return {
        "id":        1,
        "username":  username,
        "password":  generate_password_hash(password_plain),
        "full_name": full_name,
    }


# ── Tests: successful login ───────────────────────────────────────────────────

class TestLoginSuccess:

    def test_valid_credentials_return_success(self):
        customer = _make_customer()
        with patch("services.auth_service.find_by_username", return_value=customer):
            result = login("alice", "alice123")
        assert result["success"] is True

    def test_valid_credentials_return_customer_id(self):
        customer = _make_customer()
        with patch("services.auth_service.find_by_username", return_value=customer):
            result = login("alice", "alice123")
        assert result["customer"]["id"] == 1

    def test_valid_credentials_return_full_name(self):
        customer = _make_customer()
        with patch("services.auth_service.find_by_username", return_value=customer):
            result = login("alice", "alice123")
        assert result["customer"]["full_name"] == "Alice Johnson"

    def test_valid_credentials_return_no_error(self):
        customer = _make_customer()
        with patch("services.auth_service.find_by_username", return_value=customer):
            result = login("alice", "alice123")
        assert result["error"] is None


# ── Tests: wrong password ─────────────────────────────────────────────────────

class TestLoginWrongPassword:

    def test_wrong_password_returns_failure(self):
        customer = _make_customer()
        with patch("services.auth_service.find_by_username", return_value=customer):
            result = login("alice", "wrongpassword")
        assert result["success"] is False

    def test_wrong_password_returns_generic_error(self):
        """Must not distinguish between 'wrong password' and 'user not found'."""
        customer = _make_customer()
        with patch("services.auth_service.find_by_username", return_value=customer):
            result = login("alice", "wrongpassword")
        assert result["error"] == "Invalid username or password."

    def test_wrong_password_returns_no_customer(self):
        customer = _make_customer()
        with patch("services.auth_service.find_by_username", return_value=customer):
            result = login("alice", "wrongpassword")
        assert result["customer"] is None


# ── Tests: user not found ─────────────────────────────────────────────────────

class TestLoginUserNotFound:

    def test_unknown_username_returns_failure(self):
        with patch("services.auth_service.find_by_username", return_value=None):
            result = login("nobody", "anypassword")
        assert result["success"] is False

    def test_unknown_username_returns_same_generic_error(self):
        """Error message must be identical to the wrong-password case."""
        with patch("services.auth_service.find_by_username", return_value=None):
            result = login("nobody", "anypassword")
        assert result["error"] == "Invalid username or password."


# ── Tests: blank input ────────────────────────────────────────────────────────

class TestLoginBlankInput:

    @pytest.mark.parametrize("username, password", [
        ("",      "alice123"),
        ("alice", ""),
        ("",      ""),
        ("  ",    "alice123"),
        ("alice", "   "),
    ])
    def test_blank_fields_return_failure(self, username, password):
        with patch("services.auth_service.find_by_username") as mock_find:
            result = login(username, password)
        assert result["success"] is False
        # find_by_username must NOT be called — blank check fires first
        mock_find.assert_not_called()

    def test_blank_fields_return_required_error(self):
        with patch("services.auth_service.find_by_username"):
            result = login("", "")
        assert "required" in result["error"].lower()

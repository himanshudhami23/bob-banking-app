"""
tests/test_account_service.py
------------------------------
Unit tests for services/account_service.py

The model layer (get_balance, apply_transaction) is patched so these
tests verify business-rule logic only — no database is touched.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "BACKEND")))

from unittest.mock import patch, MagicMock


# ─────────────────────────────────────────────────────────────────────────────
# Deposit tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDeposit:

    def _do_deposit(self, raw_amount, current_balance=500.00):
        from services.account_service import deposit
        with patch("services.account_service.get_balance",      return_value=current_balance), \
             patch("services.account_service.apply_transaction", return_value=current_balance + float(str(raw_amount).strip())) as mock_txn:
            result = deposit(1, raw_amount)
        return result, mock_txn

    # ── Success cases ─────────────────────────────────────────────────────────

    def test_valid_deposit_returns_success(self):
        result, _ = self._do_deposit("250.00")
        assert result["success"] is True

    def test_valid_deposit_returns_correct_new_balance(self):
        result, _ = self._do_deposit("250.00", current_balance=500.00)
        assert result["new_balance"] == 750.00

    def test_valid_deposit_calls_apply_transaction(self):
        _, mock_txn = self._do_deposit("100.00")
        mock_txn.assert_called_once()

    def test_valid_deposit_calls_apply_transaction_with_deposit_type(self):
        from services.account_service import deposit
        with patch("services.account_service.get_balance",      return_value=0.00), \
             patch("services.account_service.apply_transaction") as mock_txn:
            mock_txn.return_value = 100.00
            deposit(1, "100.00")
        args = mock_txn.call_args[0]
        assert args[1] == "deposit"

    def test_deposit_integer_amount_accepted(self):
        result, _ = self._do_deposit(500)
        assert result["success"] is True

    # ── Failure cases — invalid amounts ───────────────────────────────────────

    @pytest.mark.parametrize("bad_amount", [0, "0", "0.00", -1, "-50", "-0.01"])
    def test_zero_or_negative_deposit_rejected(self, bad_amount):
        from services.account_service import deposit
        with patch("services.account_service.get_balance", return_value=500.00), \
             patch("services.account_service.apply_transaction") as mock_txn:
            result = deposit(1, bad_amount)
        assert result["success"] is False
        mock_txn.assert_not_called()

    @pytest.mark.parametrize("bad_input", ["abc", "", "  ", "12.3.4", None])
    def test_non_numeric_deposit_rejected(self, bad_input):
        from services.account_service import deposit
        with patch("services.account_service.get_balance", return_value=500.00), \
             patch("services.account_service.apply_transaction") as mock_txn:
            result = deposit(1, bad_input)
        assert result["success"] is False
        mock_txn.assert_not_called()

    def test_deposit_exceeding_max_rejected(self):
        from services.account_service import deposit, MAX_TRANSACTION_AMOUNT
        with patch("services.account_service.get_balance",      return_value=0.00), \
             patch("services.account_service.apply_transaction") as mock_txn:
            result = deposit(1, MAX_TRANSACTION_AMOUNT + 1)
        assert result["success"] is False
        mock_txn.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# Withdrawal tests
# ─────────────────────────────────────────────────────────────────────────────

class TestWithdraw:

    def _do_withdraw(self, raw_amount, current_balance=500.00):
        from services.account_service import withdraw
        try:
            amt = float(str(raw_amount).strip())
        except (TypeError, ValueError):
            amt = 0
        with patch("services.account_service.get_balance",      return_value=current_balance), \
             patch("services.account_service.apply_transaction", return_value=current_balance - amt) as mock_txn:
            result = withdraw(1, raw_amount)
        return result, mock_txn

    # ── Success cases ─────────────────────────────────────────────────────────

    def test_valid_withdrawal_returns_success(self):
        result, _ = self._do_withdraw("200.00", current_balance=500.00)
        assert result["success"] is True

    def test_valid_withdrawal_returns_correct_new_balance(self):
        result, _ = self._do_withdraw("200.00", current_balance=500.00)
        assert result["new_balance"] == 300.00

    def test_withdrawal_exact_balance_succeeds(self):
        """Withdrawing exactly the full balance should succeed (result = 0.00)."""
        result, _ = self._do_withdraw("500.00", current_balance=500.00)
        assert result["success"] is True

    def test_withdrawal_calls_apply_transaction_with_withdrawal_type(self):
        from services.account_service import withdraw
        with patch("services.account_service.get_balance",      return_value=1000.00), \
             patch("services.account_service.apply_transaction") as mock_txn:
            mock_txn.return_value = 900.00
            withdraw(1, "100.00")
        args = mock_txn.call_args[0]
        assert args[1] == "withdrawal"

    # ── Failure: insufficient funds ───────────────────────────────────────────

    def test_over_balance_withdrawal_rejected(self):
        from services.account_service import withdraw
        with patch("services.account_service.get_balance",      return_value=100.00), \
             patch("services.account_service.apply_transaction") as mock_txn:
            result = withdraw(1, "100.01")
        assert result["success"] is False
        assert "insufficient" in result["error"].lower()
        mock_txn.assert_not_called()

    def test_insufficient_funds_error_does_not_reveal_balance(self):
        from services.account_service import withdraw
        with patch("services.account_service.get_balance",      return_value=50.00), \
             patch("services.account_service.apply_transaction"):
            result = withdraw(1, "999.00")
        # Error should say "insufficient funds" but not expose the exact balance
        assert "$50" not in result["error"]

    # ── Failure: invalid amounts ──────────────────────────────────────────────

    @pytest.mark.parametrize("bad_amount", [0, "0", -10, "-5.00"])
    def test_zero_or_negative_withdrawal_rejected(self, bad_amount):
        from services.account_service import withdraw
        with patch("services.account_service.get_balance", return_value=500.00), \
             patch("services.account_service.apply_transaction") as mock_txn:
            result = withdraw(1, bad_amount)
        assert result["success"] is False
        mock_txn.assert_not_called()

    @pytest.mark.parametrize("bad_input", ["abc", "", None])
    def test_non_numeric_withdrawal_rejected(self, bad_input):
        from services.account_service import withdraw
        with patch("services.account_service.get_balance", return_value=500.00), \
             patch("services.account_service.apply_transaction") as mock_txn:
            result = withdraw(1, bad_input)
        assert result["success"] is False
        mock_txn.assert_not_called()

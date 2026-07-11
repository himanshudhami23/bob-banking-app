"""
utils.py
--------
Shared utilities used across the Flask application.

Currently provides:
    login_required — a route decorator that enforces session authentication.
"""

import functools
from flask import session, redirect, url_for


def login_required(f):
    """
    Route decorator that enforces an active customer session.

    Usage:
        @app.route('/dashboard')
        @login_required
        def dashboard():
            ...

    Logic:
        1. Check whether 'customer_id' is present in Flask's session object.
        2. If missing (unauthenticated), redirect to the login page immediately.
        3. If present, execute the original route function normally.

    The decorator preserves the wrapped function's __name__ and __doc__
    via functools.wraps so that Flask's route registry does not raise
    duplicate endpoint name errors when multiple routes use this decorator.
    """
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("customer_id"):
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)
    return decorated_function

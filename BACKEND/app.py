"""
app.py
------
Flask application entry point and factory.

Responsibilities:
  1. Create the Flask app instance with correct template/static paths
  2. Load configuration from config.py
  3. Register all Blueprints (route groups)
  4. Initialise the database (create tables if they do not exist)
  5. Register custom error handlers (404, 500)
  6. Start the development server when run directly
"""

import os
import sys

# Ensure BACKEND/ is on the Python path so absolute imports work
# regardless of the working directory from which app.py is launched.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template
from config import SECRET_KEY, DEBUG

# ── Resolve paths to FRONTEND assets ─────────────────────────────────────────
# app.py lives in BACKEND/; templates and static files live in FRONTEND/
_backend_dir  = os.path.dirname(os.path.abspath(__file__))
_frontend_dir = os.path.join(_backend_dir, "..", "FRONTEND")

TEMPLATE_FOLDER = os.path.join(_frontend_dir, "templates")
STATIC_FOLDER   = os.path.join(_frontend_dir, "static")

# ── Create Flask app instance ─────────────────────────────────────────────────
app = Flask(
    __name__,
    template_folder=TEMPLATE_FOLDER,
    static_folder=STATIC_FOLDER,
)

app.secret_key = SECRET_KEY

# ── Register Blueprints ───────────────────────────────────────────────────────
from routes.auth_routes        import auth_bp
from routes.dashboard_routes   import dashboard_bp
from routes.transaction_routes import transactions_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(transactions_bp)

# ── Root redirect ─────────────────────────────────────────────────────────────
from flask import redirect, url_for

@app.route("/")
def index():
    """Redirect the root URL to the login page."""
    return redirect(url_for("auth.login_page"))

# ── Custom error handlers ─────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(error):
    """Render a friendly 404 page."""
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    """Render a friendly 500 page — never exposes stack traces."""
    return render_template("errors/500.html"), 500

# ── Database initialisation ───────────────────────────────────────────────────
from models.db import init_db
from config import DATABASE_PATH as _initial_db_path

# Only run init_db at import time when a real database path is configured.
# In the test environment, DATABASE_PATH starts as None and is set per-test
# by the reset_db fixture, which calls init_db() itself.
if _initial_db_path is not None:
    with app.app_context():
        init_db()

# ── Development server entry point ────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=DEBUG, host="127.0.0.1", port=5000)

import os

# Base directory of this file (BACKEND/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Flask secret key — used to sign session cookies.
# In production, load this from an environment variable; never hard-code.
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

# Path to the SQLite database file
DATABASE_PATH = os.path.join(BASE_DIR, "bank.db")

# Debug mode — set False in production
DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() == "true"

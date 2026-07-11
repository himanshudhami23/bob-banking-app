# SecureBank — Banking Web Application

A lightweight, full-stack banking application built with **HTML + Bootstrap**, **Python Flask**, and **SQLite**.

---

## Project Structure

```
BankingApp/
├── FRONTEND/
│   ├── templates/
│   │   ├── base.html           # Shared layout (Bootstrap CDN, nav, flash)
│   │   ├── login.html          # Customer login page
│   │   ├── dashboard.html      # Account summary + recent transactions
│   │   ├── deposit.html        # Deposit funds form
│   │   ├── withdraw.html       # Withdraw funds form
│   │   └── errors/
│   │       ├── 404.html
│   │       └── 500.html
│   └── static/
│       └── css/
│           └── custom.css      # Style overrides on top of Bootstrap
│
├── BACKEND/
│   ├── app.py                  # Flask entry point — run this file
│   ├── config.py               # Secret key, DB path, debug flag
│   ├── utils.py                # login_required session guard decorator
│   ├── seed.py                 # One-time DB seeding script
│   ├── requirements.txt        # Python dependencies
│   ├── routes/
│   │   ├── auth_routes.py      # /login, /logout
│   │   ├── dashboard_routes.py # /dashboard
│   │   └── transaction_routes.py # /deposit, /withdraw
│   ├── services/
│   │   ├── auth_service.py     # Credential verification logic
│   │   └── account_service.py  # Deposit / withdrawal business rules
│   └── models/
│       ├── db.py               # SQLite connection helper + schema init
│       ├── customer_model.py   # Customer table queries
│       └── account_model.py    # Account balance + transaction queries
│
├── tests/
│   ├── conftest.py             # Shared pytest fixtures (in-memory DB)
│   ├── test_auth_service.py    # Unit tests — authentication logic
│   ├── test_account_service.py # Unit tests — deposit/withdrawal logic
│   └── test_integration.py     # Integration tests — full HTTP cycles
│
├── IMPLEMENTATION_PLAN.md
└── STEP_BY_STEP_IMPLEMENTATION_GUIDE.md
```

---

## Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- pip (bundled with Python 3)

### 2. Create and activate a virtual environment

```bash
# From the BankingApp/BACKEND/ directory
cd BankingApp/BACKEND

python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Seed the database

Run the seeding script once to create the `bank.db` file and insert test customer accounts:

```bash
python seed.py
```

This inserts two pre-registered customers:

| Username | Password   | Starting Balance |
|----------|------------|-----------------|
| `alice`  | `alice123` | $5,000.00        |
| `bob`    | `bob456`   | $2,500.00        |

### 5. Start the application

```bash
python app.py
```

The server starts at **http://127.0.0.1:5000**

Open your browser and navigate to that URL. You will be redirected to the login page automatically.

---

## Running Tests

From the `BankingApp/` root directory (with the virtual environment active):

```bash
# Install pytest if not already installed
pip install pytest

# Run the full test suite
pytest tests/ -v
```

The test suite uses an in-memory SQLite database — it never touches `bank.db`.

---

## Features

| Feature | Route | Description |
|---|---|---|
| Login | `POST /login` | Verifies hashed credentials; creates a session |
| Dashboard | `GET /dashboard` | Shows balance and last 5 transactions |
| Deposit | `POST /deposit` | Adds funds; validates positive amount |
| Withdraw | `POST /withdraw` | Deducts funds; checks sufficient balance |
| Logout | `POST /logout` | Clears session; redirects to login |

---

## Security Notes

- Passwords are stored as **PBKDF2-SHA256 hashes** (via Werkzeug) — never plain text.
- Sessions are **server-signed cookies** using Flask's secret key.
- Login errors use a **generic message** to prevent username enumeration.
- Logout uses **HTTP POST** to prevent session clearing by browser prefetch.
- All balance updates are **atomic** (single DB transaction commit).
- Jinja2 **auto-escaping** is enabled by default — XSS protection is built in.

---

## Production Checklist

Before deploying to a public server:

- [ ] Replace `dev-secret-key-change-in-production` with a cryptographically random `FLASK_SECRET_KEY` environment variable
- [ ] Set `FLASK_DEBUG=false`
- [ ] Run with a production WSGI server: `gunicorn` (Linux/macOS) or `waitress` (Windows)
- [ ] Place behind a reverse proxy (Nginx/Apache) with TLS/HTTPS enabled
- [ ] Replace SQLite with PostgreSQL for multi-user or high-concurrency deployments
- [ ] Configure application logging to a file

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, Bootstrap 5 (CDN), Jinja2 |
| Backend | Python 3, Flask 3 |
| Database | SQLite 3 (via Python stdlib `sqlite3`) |
| Auth | Werkzeug `generate_password_hash` / `check_password_hash` |
| Tests | pytest |

import os
import re
import secrets
import sqlite3
import time
from collections import defaultdict, deque

from flask import Flask, abort, g, render_template, request, session
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")
DOMAINS = ["mailum.com", "mailum.net"]
USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,31}$")
RATE_LIMIT = 10          # max signup attempts...
RATE_WINDOW = 10 * 60    # ...per IP in this many seconds

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Strict")

attempts = defaultdict(deque)

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "email TEXT PRIMARY KEY COLLATE NOCASE, password_hash TEXT NOT NULL)"
        )
    return g.db

@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db:
        db.close()

@app.after_request
def security_headers(resp):
    resp.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "no-referrer"
    return resp

def rate_limited(ip):
    now = time.time()
    q = attempts[ip]
    while q and now - q[0] > RATE_WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        return True
    q.append(now)
    return False

def validate(username, domain, password, repeat):
    if not USERNAME_RE.match(username):
        return "Email must be 3-32 characters: lowercase letters, numbers, . _ -"
    if domain not in DOMAINS:
        return "Invalid domain."
    if len(password) < 10 or not all(
        re.search(p, password) for p in (r"[a-z]", r"[A-Z]", r"\d")
    ):
        return "Password must be at least 10 characters with upper, lower case and a number."
    if password != repeat:
        return "Passwords do not match."
    return None

def render(**kw):
    session["csrf"] = secrets.token_urlsafe(32)
    return render_template("signup.html", domains=DOMAINS, csrf=session["csrf"], **kw)

@app.route("/", methods=["GET", "POST"])
def signup():
    if request.method != "POST":
        return render()

    token = request.form.get("csrf", "")
    expected = session.pop("csrf", "")
    if not expected or not secrets.compare_digest(token, expected):
        abort(400, "Invalid CSRF token")
    if rate_limited(request.remote_addr):
        return render(error="Too many attempts, try again later."), 429
    # Honeypot: hidden field only bots fill in
    if request.form.get("website"):
        return render(error="Signup rejected."), 400

    username = request.form.get("username", "").strip().lower()
    domain = request.form.get("domain", "")
    password = request.form.get("password", "")
    repeat = request.form.get("repeat", "")

    error = validate(username, domain, password, repeat)
    if error:
        return render(error=error, username=username), 400

    email = f"{username}@{domain}"
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return render(error="This email is already taken.", username=username), 409
    return render(success=f"Account {email} created.")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

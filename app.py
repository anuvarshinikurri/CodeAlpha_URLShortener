"""LinkSnap — Flask REST API for shortening, storing and redirecting URLs.

Endpoints
---------
POST   /api/shorten        {"url": "https://..."}  -> 201 link object
GET    /api/urls                                   -> {"total": n, "urls": [link, ...]}
DELETE /api/urls/<code>                            -> 204
GET    /api/health                                 -> {"status": "ok"}
GET    /<code>                                     -> 302 redirect to the original URL
"""

import os
import secrets
import sqlite3
import string
from datetime import datetime, timezone
from urllib.parse import urlparse

from flask import Flask, abort, g, jsonify, redirect, request
from flask_cors import CORS

ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6
MAX_URL_LENGTH = 2048


def create_app(database_path: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DATABASE"] = database_path or os.environ.get(
        "LINKSNAP_DB", os.path.join(os.path.dirname(__file__), "linksnap.db")
    )
    # Public base used to build short links, e.g. https://lnk.example.com
    app.config["PUBLIC_BASE_URL"] = os.environ.get("LINKSNAP_PUBLIC_URL")
    CORS(app, resources={r"/api/*": {"origins": os.environ.get("LINKSNAP_CORS_ORIGINS", "*")}})

    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        db = get_db()
        db.execute(
            """CREATE TABLE IF NOT EXISTS urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                original_url TEXT NOT NULL,
                created_at TEXT NOT NULL,
                clicks INTEGER NOT NULL DEFAULT 0
            )"""
        )
        db.commit()

    def base_url() -> str:
        return (app.config["PUBLIC_BASE_URL"] or request.host_url).rstrip("/")

    def serialize(row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "code": row["code"],
            "original_url": row["original_url"],
            "short_url": f"{base_url()}/{row['code']}",
            "created_at": row["created_at"],
            "clicks": row["clicks"],
        }

    def error(message: str, status: int):
        return jsonify({"error": message}), status

    def is_valid_url(value: str) -> bool:
        if len(value) > MAX_URL_LENGTH:
            return False
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https") and "." in parsed.netloc and " " not in value

    def new_code(db: sqlite3.Connection) -> str:
        while True:
            code = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
            if db.execute("SELECT 1 FROM urls WHERE code = ?", (code,)).fetchone() is None:
                return code

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/api/shorten")
    def shorten():
        payload = request.get_json(silent=True) or {}
        url = str(payload.get("url", "")).strip()
        if not url:
            return error("Please provide a URL to shorten.", 400)
        if not is_valid_url(url):
            return error("That doesn't look like a valid http(s) URL.", 400)

        db = get_db()
        code = new_code(db)
        created_at = datetime.now(timezone.utc).isoformat()
        cursor = db.execute(
            "INSERT INTO urls (code, original_url, created_at) VALUES (?, ?, ?)",
            (code, url, created_at),
        )
        db.commit()
        row = db.execute("SELECT * FROM urls WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return jsonify(serialize(row)), 201

    @app.get("/api/urls")
    def list_urls():
        rows = get_db().execute("SELECT * FROM urls ORDER BY id DESC").fetchall()
        return jsonify({"total": len(rows), "urls": [serialize(r) for r in rows]})

    @app.delete("/api/urls/<code>")
    def delete_url(code: str):
        db = get_db()
        cursor = db.execute("DELETE FROM urls WHERE code = ?", (code,))
        db.commit()
        if cursor.rowcount == 0:
            return error("Short link not found.", 404)
        return "", 204

    @app.get("/<code>")
    def follow(code: str):
        db = get_db()
        row = db.execute("SELECT original_url FROM urls WHERE code = ?", (code,)).fetchone()
        if row is None:
            abort(404)
        db.execute("UPDATE urls SET clicks = clicks + 1 WHERE code = ?", (code,))
        db.commit()
        return redirect(row["original_url"], code=302)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)

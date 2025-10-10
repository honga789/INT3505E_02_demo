import os, json, hashlib
from datetime import datetime, timedelta, timezone

import requests
from flask import Flask, request, jsonify, Response
import jwt  

SERVICE_URL = os.environ.get("SERVICE_URL", "http://127.0.0.1:5001")

JWT_SECRET = os.environ.get("JWT_SECRET", "secret123")
JWT_ALG = "HS256"
JWT_TTL_HOURS = 2

def create_access_token(sub: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=JWT_TTL_HOURS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])

def err(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status

def parse_bearer_token():
    auth = request.headers.get("Authorization") or ""
    parts = auth.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None

def require_jwt(required_role: str | None = None):
    token = parse_bearer_token()
    if not token:
        return None, err("NOT_AUTHENTICATED", "Authorization Bearer token required", 401)
    try:
        claims = decode_token(token)
    except jwt.ExpiredSignatureError:
        return None, err("TOKEN_EXPIRED", "Token expired", 401)
    except jwt.InvalidTokenError:
        return None, err("INVALID_TOKEN", "Invalid token", 401)
    if required_role and claims.get("role") != required_role:
        return None, err("FORBIDDEN", "Insufficient permission", 403)
    return claims, None


def _json_hash(obj) -> str:
    encoded = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def etag_for_collection(items: list[dict]) -> str:
    snapshot = sorted(items, key=lambda x: x["id"])
    return f"\"{_json_hash(snapshot)}\""

def etag_for_item(item: dict) -> str:
    return f"\"{_json_hash(item)}\""

def add_cache_headers(resp: Response, etag: str):
    resp.headers["ETag"] = etag
    resp.headers["Cache-Control"] = "public, max-age=60"
    return resp

def maybe_not_modified(etag: str):
    inm = request.headers.get("If-None-Match")
    if inm and etag in inm:
        resp = Response(status=304)
        resp.headers["ETag"] = etag
        resp.headers["Cache-Control"] = "public, max-age=60"
        return resp
    return None


def create_app():
    app = Flask(__name__)

    @app.post("/api/v1/auth/login")
    def login():
        data = request.get_json(silent=True) or {}
        r = requests.post(f"{SERVICE_URL}/svc/auth/check", json=data, timeout=5)
        if r.status_code != 200:
            payload = r.json()
            code = (payload.get("error") or {}).get("code", "INVALID_CREDENTIALS")
            msg  = (payload.get("error") or {}).get("message", "Invalid credentials")
            return err(code, msg, 401 if r.status_code == 401 else 400)
        user = r.json() 
        token = create_access_token(user["username"], user["role"])
        return jsonify({"token": token, "user": user}), 200

    
    @app.get("/api/v1/books")
    def list_books():
        r = requests.get(f"{SERVICE_URL}/svc/books", timeout=5)
        if r.status_code != 200:
            payload = r.json()
            e = payload.get("error") or {}
            return err(e.get("code","INTERNAL"), e.get("message","Upstream error"), r.status_code)
        items = r.json()
        etag = etag_for_collection(items)
        not_mod = maybe_not_modified(etag)
        if not_mod: return not_mod
        resp = jsonify(items)
        resp.status_code = 200
        return add_cache_headers(resp, etag)

    @app.post("/api/v1/books")
    def create_book():
        _, auth_err = require_jwt()
        if auth_err: return auth_err
        r = requests.post(f"{SERVICE_URL}/svc/books", json=(request.get_json(silent=True) or {}), timeout=5)
        payload = r.json()
        if r.status_code != 200:
            e = payload.get("error") or {}
            return err(e.get("code","BAD_REQUEST"), e.get("message",""), r.status_code)
        new_book = payload
        resp = jsonify(new_book)
        resp.status_code = 201
        resp.headers["Location"] = f"/api/v1/books/{new_book['id']}"
        return resp

    @app.get("/api/v1/books/<book_id>")
    def get_book(book_id):
        r = requests.get(f"{SERVICE_URL}/svc/books/{book_id}", timeout=5)
        if r.status_code != 200:
            e = (r.json().get("error") or {})
            return err(e.get("code","NOT_FOUND"), e.get("message","Book not found"), r.status_code)
        item = r.json()
        etag = etag_for_item(item)
        not_mod = maybe_not_modified(etag)
        if not_mod: return not_mod
        resp = jsonify(item)
        resp.status_code = 200
        return add_cache_headers(resp, etag)

    @app.put("/api/v1/books/<book_id>")
    def update_book(book_id):
        _, auth_err = require_jwt()
        if auth_err: return auth_err
        r = requests.put(
            f"{SERVICE_URL}/svc/books/{book_id}",
            json=(request.get_json(silent=True) or {}),
            timeout=5,
        )
        payload = r.json()
        if r.status_code != 200:
            e = payload.get("error") or {}
            return err(e.get("code","NOT_FOUND"), e.get("message","Book not found"), r.status_code)
        return jsonify(payload), 200

    @app.delete("/api/v1/books/<book_id>")
    def delete_book(book_id):
        claims, auth_err = require_jwt(required_role="librarian")
        if auth_err: return auth_err
        r = requests.delete(f"{SERVICE_URL}/svc/books/{book_id}", timeout=5)
        if r.status_code != 200:
            e = (r.json().get("error") or {})
            return err(e.get("code","NOT_FOUND"), e.get("message","Book not found"), r.status_code)
        return ("", 204)

    return app

import os
import uuid
from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
import jwt 

app = Flask(__name__)


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


BOOKS = [
    {"id": "1", "title": "Clean Code", "author": "Robert C. Martin", "available": True},
    {"id": "2", "title": "The Pragmatic Programmer", "author": "Andrew Hunt", "available": True},
]

USERS = {
    "admin":  {"password": "admin",  "role": "librarian"},
    "member": {"password": "member", "role": "member"},
}


def err(code: str, message: str, status: int):
    return jsonify({"error": {"code": code, "message": message}}), status

def find_book(book_id: str):
    for b in BOOKS:
        if b["id"] == book_id:
            return b
    return None

def parse_bearer_token() -> str | None:
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


@app.post("/api/v1/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return err("VALIDATION_ERROR", "username and password are required", 400)

    user = USERS.get(username)
    if not user or user["password"] != password:
        return err("INVALID_CREDENTIALS", "Invalid username or password", 401)

    token = create_access_token(sub=username, role=user["role"])
    return jsonify({"token": token, "user": {"username": username, "role": user["role"]}}), 200


@app.get("/api/v1/books")
def list_books():
    return jsonify(BOOKS), 200


@app.post("/api/v1/books")
def create_book():
    claims, err_resp = require_jwt()
    if err_resp: return err_resp

    data = request.get_json(silent=True) or {}
    title = data.get("title")
    author = data.get("author")
    if not title or not author:
        return err("VALIDATION_ERROR", "title and author are required", 400)

    new_book = {
        "id": str(uuid.uuid4()),
        "title": title,
        "author": author,
        "available": True,
    }
    BOOKS.append(new_book)

    from flask import Response
    resp = jsonify(new_book)
    resp.status_code = 201
    resp.headers["Location"] = f"/api/v1/books/{new_book['id']}"
    return resp

@app.get("/api/v1/books/<book_id>")
def get_book(book_id):
    b = find_book(book_id)
    if not b:
        return err("NOT_FOUND", "Book not found", 404)
    return jsonify(b), 200


@app.put("/api/v1/books/<book_id>")
def update_book(book_id):
    claims, err_resp = require_jwt()
    if err_resp: return err_resp

    b = find_book(book_id)
    if not b:
        return err("NOT_FOUND", "Book not found", 404)

    data = request.get_json(silent=True) or {}
    if "title" in data: b["title"] = data["title"]
    if "author" in data: b["author"] = data["author"]
    if "available" in data: b["available"] = bool(data["available"])

    return jsonify(b), 200


@app.delete("/api/v1/books/<book_id>")
def delete_book(book_id):
    claims, err_resp = require_jwt(required_role="librarian")
    if err_resp: return err_resp

    for i, bk in enumerate(BOOKS):
        if bk["id"] == book_id:
            BOOKS.pop(i)
            return ("", 204)
    return err("NOT_FOUND", "Book not found", 404)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

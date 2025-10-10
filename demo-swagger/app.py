import os
import uuid
from datetime import datetime, timedelta, timezone
from copy import deepcopy
from flask import Flask, request, jsonify, make_response
import jwt

app = Flask(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET", "secret123") 
JWT_ALG = "HS256"
JWT_TTL_HOURS = 2

def create_access_token(sub: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=JWT_TTL_HOURS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])


BOOKS = [
        {
            "id": "d290f1ee-6c54-4b01-90e6-d701748f0851",
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "year": 2008,
            "price": 19.99,
            "tags": ["clean", "best-practice"]
        },
        {
            "id": "2c3d4e5f-6071-4829-9a2b-abcdef012345",
            "title": "Design Patterns",
            "author": "Erich Gamma et al.",
            "year": 1994,
            "price": 30.00,
            "tags": ["oop", "patterns"]
        },
        {
            "id": "4e5f6071-8293-4a0b-bcde-1234567890ab",
            "title": "Introduction to Algorithms",
            "author": "Cormen, Leiserson, Rivest, Stein",
            "year": 2009,
            "price": 45.00,
            "tags": ["algorithms", "cs"]
        },
    ]


def error(code: str, message: str, http_status: int):
    return make_response(jsonify({"code": code, "message": message}), http_status)

def require_auth(fn):
    from functools import wraps
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return error("UNAUTHORIZED", "Invalid or missing token", 401)
        token = auth.split(" ", 1)[1].strip()
        try:
            request.user = decode_token(token)
        except jwt.ExpiredSignatureError:
            return error("UNAUTHORIZED", "Token expired", 401)
        except jwt.InvalidTokenError as e:
            return error("UNAUTHORIZED", f"Invalid token: {e}", 401)
        return fn(*args, **kwargs)
    return wrapper

def find_book_idx(book_id: str):
    for i, b in enumerate(BOOKS):
        if b["id"] == book_id:
            return i
    return None

def validate_tags(value):
    return isinstance(value, list) and all(isinstance(x, str) for x in value)

def validate_create(body):
    if not isinstance(body, dict):
        return "Body must be JSON object"
    if "title" not in body or not isinstance(body["title"], str):
        return "title is required (string)"
    if "author" not in body or not isinstance(body["author"], str):
        return "author is required (string)"
    if "year" in body and (not isinstance(body["year"], int) or body["year"] < 0):
        return "year must be integer >= 0"
    if "price" in body and not isinstance(body["price"], (int, float)):
        return "price must be number"
    if "tags" in body and not validate_tags(body["tags"]):
        return "tags must be array of strings"
    return None

def validate_update(body):
    if not isinstance(body, dict):
        return "Body must be JSON object"
    if "title" in body and not isinstance(body["title"], str):
        return "title must be string"
    if "author" in body and not isinstance(body["author"], str):
        return "author must be string"
    if "year" in body and (not isinstance(body["year"], int) or body["year"] < 0):
        return "year must be integer >= 0"
    if "price" in body and not isinstance(body["price"], (int, float)):
        return "price must be number"
    if "tags" in body and not validate_tags(body["tags"]):
        return "tags must be array of strings"
    return None

def apply_search_and_sort(items, q, sort_key):
    data = items
    if q:
        ql = q.lower()
        data = [b for b in data if ql in b.get("title","").lower() or ql in b.get("author","").lower()]
    sort_map = {
        "title_asc": ("title", False),
        "title_desc": ("title", True),
        "year_asc": ("year", False),
        "year_desc": ("year", True),
    }
    if sort_key in sort_map:
        field, desc = sort_map[sort_key]
        data = sorted(
            data,
            key=lambda x: (x.get(field) is None, x.get(field)),
            reverse=desc
        )
    return data


@app.before_request
def handle_cors_preflight():
    if request.method == "OPTIONS":
        resp = make_response("", 204)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,PATCH,DELETE,OPTIONS"
        return resp

@app.after_request
def add_headers(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Expose-Headers"] = (
        "X-RateLimit-Limit, X-RateLimit-Remaining, Location, Authorization"
    )
    if 200 <= resp.status_code < 300:
        resp.headers["X-RateLimit-Limit"] = "500"
        resp.headers["X-RateLimit-Remaining"] = "498"
    return resp

@app.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    if username == "admin" and password == "admin":
        token = create_access_token(sub=username)
        return jsonify({"access_token": token, "token_type": "Bearer", "expires_in": JWT_TTL_HOURS * 3600})
    return error("UNAUTHORIZED", "Invalid credentials", 401)


@app.get("/api/v1/books")
@require_auth
def list_books():
    q = request.args.get("q", type=str)
    sort_key = request.args.get("sort", type=str)
    data = apply_search_and_sort(BOOKS, q, sort_key)
    return jsonify({"items": deepcopy(data), "total": len(data)}), 200

@app.post("/api/v1/books")
@require_auth
def create_book():
    body = request.get_json(silent=True)
    msg = validate_create(body)
    if msg:
        return error("BAD_REQUEST", msg, 400)
    new_book = {
        "id": str(uuid.uuid4()),
        "title": body["title"],
        "author": body["author"],
        "year": body.get("year"),
        "price": body.get("price"),
        "tags": body.get("tags", []),
    }
    BOOKS.append(new_book)
    return jsonify(new_book), 201

@app.get("/api/v1/books/<id>")
@require_auth
def get_book(id):
    idx = find_book_idx(id)
    if idx is None:
        return error("NOT_FOUND", "Book not found", 404)
    return jsonify(BOOKS[idx]), 200

@app.patch("/api/v1/books/<id>")
@require_auth
def update_book(id):
    idx = find_book_idx(id)
    if idx is None:
        return error("NOT_FOUND", "Book not found", 404)
    body = request.get_json(silent=True)
    msg = validate_update(body)
    if msg:
        return error("BAD_REQUEST", msg, 400)
    book = BOOKS[idx]
    for field in ("title", "author", "year", "price", "tags"):
        if field in body:
            book[field] = body[field]
    BOOKS[idx] = book
    return jsonify(book), 200

@app.delete("/api/v1/books/<id>")
@require_auth
def delete_book(id):
    idx = find_book_idx(id)
    if idx is None:
        return error("NOT_FOUND", "Book not found", 404)
    BOOKS.pop(idx)
    return ("", 204)

@app.get("/")
def home():
    return "Books Service running. Use /auth/login to get a JWT, then call /api/v1/books.*", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

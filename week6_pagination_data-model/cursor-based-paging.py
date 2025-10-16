
from flask import Flask, request, jsonify, make_response
import hashlib
import json
import base64
from datetime import datetime, timezone

app = Flask(__name__)

books = [
    {"id": 1, "title": "1984", "author": "George Orwell", "updated_at": "2024-06-01T10:00:00Z"},
    {"id": 2, "title": "To Kill a Mockingbird", "author": "Harper Lee", "updated_at": "2024-06-01T10:00:00Z"},
    {"id": 3, "title": "The Hobbit", "author": "J.R.R. Tolkien", "updated_at": "2024-06-02T08:30:00Z"},
    {"id": 4, "title": "Brave New World", "author": "Aldous Huxley", "updated_at": "2024-06-03T09:00:00Z"},
    {"id": 5, "title": "Fahrenheit 451", "author": "Ray Bradbury", "updated_at": "2024-06-03T09:00:00Z"},
    {"id": 6, "title": "Animal Farm", "author": "George Orwell", "updated_at": "2024-06-03T11:15:00Z"},
    {"id": 7, "title": "The Catcher in the Rye", "author": "J.D. Salinger", "updated_at": "2024-06-04T13:05:00Z"},
    {"id": 8, "title": "Lord of the Flies", "author": "William Golding", "updated_at": "2024-06-04T13:05:00Z"},
    {"id": 9, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "updated_at": "2024-06-05T07:40:00Z"},
    {"id": 10, "title": "Moby Dick", "author": "Herman Melville", "updated_at": "2024-06-06T10:10:00Z"},
    {"id": 11, "title": "War and Peace", "author": "Leo Tolstoy", "updated_at": "2024-06-07T16:20:00Z"},
    {"id": 12, "title": "Crime and Punishment", "author": "Fyodor Dostoevsky", "updated_at": "2024-06-07T16:20:00Z"},
    {"id": 13, "title": "The Odyssey", "author": "Homer", "updated_at": "2024-06-08T19:00:00Z"},
    {"id": 14, "title": "Ulysses", "author": "James Joyce", "updated_at": "2024-06-09T12:00:00Z"},
    {"id": 15, "title": "The Divine Comedy", "author": "Dante Alighieri", "updated_at": "2024-06-10T09:30:00Z"},
]

SAMPLE_TOKEN = "hehe123"

def require_token(f):
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")
        if token != f"Bearer {SAMPLE_TOKEN}":
            return {"error": "Unauthorized"}, 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


def to_dt(iso_str: str) -> datetime:
    """Parse ISO8601 string to aware datetime (supports 'Z')."""
    if iso_str.endswith("Z"):
        iso_str = iso_str.replace("Z", "+00:00")
    return datetime.fromisoformat(iso_str)


def sort_key(b):
    return (to_dt(b["updated_at"]), b["id"])


def encode_cursor(t_iso: str, last_id: int) -> str:
    payload = {"t": t_iso, "id": last_id}
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    token = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    return token


def decode_cursor(token: str):
    try:
        padding = "=" * (-len(token) % 4)
        raw = base64.urlsafe_b64decode((token + padding).encode("utf-8"))
        obj = json.loads(raw.decode("utf-8"))
        t_iso = obj["t"]
        last_id = int(obj["id"])
        return t_iso, last_id
    except Exception:
        return None, None


def generate_etag(payload) -> str:
    body = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    import hashlib
    return hashlib.md5(body.encode("utf-8")).hexdigest()


@app.get("/books")
def list_books_cursor():
    search = request.args.get("search", "").strip().lower()
    if search:
        filtered = [b for b in books if search in b["title"].lower() or search in b["author"].lower()]
    else:
        filtered = books

    filtered_sorted = sorted(filtered, key=sort_key)

    try:
        limit = int(request.args.get("limit", 5))
    except ValueError:
        limit = 5
    if limit < 1:
        limit = 1

    after_token = request.args.get("after")
    start_idx = 0
    if after_token:
        t_iso, last_id = decode_cursor(after_token)
        if t_iso is None:
            return {"error": "Invalid cursor"}, 400
        cursor_tuple = (to_dt(t_iso), last_id)

        for i, b in enumerate(filtered_sorted):
            if sort_key(b) > cursor_tuple:
                start_idx = i
                break
        else:
            start_idx = len(filtered_sorted)

    page_items = filtered_sorted[start_idx: start_idx + limit]

    next_cursor = None
    if page_items:
        last = page_items[-1]
        next_cursor = encode_cursor(last["updated_at"], last["id"])

    data = {
        "limit": limit,
        "results": page_items,
        "next_cursor": next_cursor,
        "sort": {"by": ["updated_at", "id"], "order": "asc"},
        "count": len(page_items),
    }

    etag = generate_etag(data)
    if request.headers.get("If-None-Match") == etag:
        resp = make_response("", 304)
        resp.headers["ETag"] = etag
        return resp

    resp = make_response(jsonify(data), 200)
    resp.headers["Content-Type"] = "application/json"
    resp.headers["Cache-Control"] = "public, max-age=60"
    resp.headers["ETag"] = etag
    return resp


@app.get("/books/<int:book_id>")
def get_book(book_id: int):
    book = next((b for b in books if b["id"] == book_id), None)
    if not book:
        return {"error": "Book not found"}, 404
    return jsonify(book)


@app.post("/books")
@require_token
def add_book():
    if not request.is_json:
        return {"error": "Request must be JSON"}, 415

    title = request.json.get("title")
    author = request.json.get("author")
    if not title or not author:
        return {"error": "Title and author are required"}, 400

    new_id = (max((b["id"] for b in books), default=0) + 1)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    new_book = {"id": new_id, "title": title, "author": author, "updated_at": now}
    books.append(new_book)
    return jsonify(new_book), 201


if __name__ == "__main__":
    app.run(port=5002, debug=True)

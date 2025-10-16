
from flask import Flask, request, jsonify, make_response
import hashlib
import json

app = Flask(__name__)

books = [
    {"id": 1, "title": "1984", "author": "George Orwell"},
    {"id": 2, "title": "To Kill a Mockingbird", "author": "Harper Lee"},
    {"id": 3, "title": "The Hobbit", "author": "J.R.R. Tolkien"},
    {"id": 4, "title": "Brave New World", "author": "Aldous Huxley"},
    {"id": 5, "title": "Fahrenheit 451", "author": "Ray Bradbury"},
    {"id": 6, "title": "Animal Farm", "author": "George Orwell"},
    {"id": 7, "title": "The Catcher in the Rye", "author": "J.D. Salinger"},
    {"id": 8, "title": "Lord of the Flies", "author": "William Golding"},
    {"id": 9, "title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
    {"id": 10, "title": "Moby Dick", "author": "Herman Melville"},
    {"id": 11, "title": "War and Peace", "author": "Leo Tolstoy"},
    {"id": 12, "title": "Crime and Punishment", "author": "Fyodor Dostoevsky"},
    {"id": 13, "title": "The Odyssey", "author": "Homer"},
    {"id": 14, "title": "Ulysses", "author": "James Joyce"},
    {"id": 15, "title": "The Divine Comedy", "author": "Dante Alighieri"}
]

SAMPLE_TOKEN = "hehe123"

def require_token(f):
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token != f"Bearer {SAMPLE_TOKEN}":
            return {"error": "Unauthorized"}, 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


def generate_etag(payload) -> str:
    body = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(body.encode("utf-8")).hexdigest()


@app.get("/books")
def list_books():
    search = request.args.get("search", "").strip().lower()
    if search:
        filtered = [b for b in books if search in b["title"].lower() or search in b["author"].lower()]
    else:
        filtered = books

    try:
        limit = int(request.args.get("limit", 5))
    except ValueError:
        limit = 5
    try:
        offset = int(request.args.get("offset", 0))
    except ValueError:
        offset = 0

    if limit < 1:
        limit = 1
    if offset < 0:
        offset = 0

    total = len(filtered)
    page_items = filtered[offset: offset + limit]

    data = {
        "limit": limit,
        "offset": offset,
        "total": total,
        "results": page_items,
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
    new_book = {"id": new_id, "title": title, "author": author}
    books.append(new_book)
    return jsonify(new_book), 201


if __name__ == "__main__":
    app.run(port=5000, debug=True)

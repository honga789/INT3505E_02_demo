import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)


BOOKS = [
    {"id": "1", "title": "Clean Code", "author": "Robert C. Martin", "available": True},
    {"id": "2", "title": "The Pragmatic Programmer", "author": "Andrew Hunt", "available": True},
]

def err(code: str, message: str, status: int):
    return jsonify({"error": {"code": code, "message": message}}), status

def find_book(book_id: str):
    for b in BOOKS:
        if b["id"] == book_id:
            return b
    return None


@app.get("/api/v1/books")
def list_books():
    return jsonify(BOOKS), 200


@app.post("/api/v1/books")
def create_book():
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
    for i, bk in enumerate(BOOKS):
        if bk["id"] == book_id:
            BOOKS.pop(i)
            return ("", 204)
    return err("NOT_FOUND", "Book not found", 404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

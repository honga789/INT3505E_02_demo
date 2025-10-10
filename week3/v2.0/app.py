import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

BOOKS = [
    {"id": "1", "title": "Clean Code", "author": "Robert C. Martin", "available": True},
    {"id": "2", "title": "The Pragmatic Programmer", "author": "Andrew Hunt", "available": True},
]


@app.get("/getBooks")
def get_books():
    return jsonify(BOOKS), 200

@app.post("/addBook")
def add_book():
    data = request.get_json(silent=True) or {}
    new_book = {
        "id": str(uuid.uuid4()),
        "title": data.get("title"),
        "author": data.get("author"),
        "available": True,
    }
    BOOKS.append(new_book)
    return jsonify(new_book), 200

@app.post("/editBookById")
def edit_book_by_id():
    data = request.get_json(silent=True) or {}
    book_id = data.get("id")
    if not book_id:
        return jsonify({"error": "MISSING_ID", "message": "id is required"}), 200

    for b in BOOKS:
        if b["id"] == book_id:
            if "title" in data: b["title"] = data["title"]
            if "author" in data: b["author"] = data["author"]
            if "available" in data: b["available"] = bool(data["available"])
            return jsonify({"ok": True, "book": b}), 200

    return jsonify({"error": "NOT_FOUND", "message": "Book not found"}), 200

@app.post("/deleteBook")
def delete_book():
    data = request.get_json(silent=True) or {}
    book_id = data.get("id")
    if not book_id:
        return jsonify({"error": "MISSING_ID", "message": "id is required"}), 200

    for i, b in enumerate(BOOKS):
        if b["id"] == book_id:
            BOOKS.pop(i)
            return jsonify({"ok": True, "deletedId": book_id}), 200

    return jsonify({"error": "NOT_FOUND", "message": "Book not found"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

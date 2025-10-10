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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

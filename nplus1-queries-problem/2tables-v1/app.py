from flask import Flask, request, jsonify, abort

app = Flask(__name__)

authors = [{"id": i, "author_name": f"Author {i}"} for i in range(1, 11)]
books = [{"id": i, "book_name": f"Book {i}", "author_id": (i % 10) + 1}
         for i in range(1, 201)]

@app.get("/books")
def list_books():
    limit = request.args.get("limit", default=10, type=int)
    limit = max(1, min(limit, len(books)))
    items = books[:limit]
    return jsonify({
        "data": [
            {"id": b["id"], "book_name": b["book_name"], "author_id": b["author_id"]}
            for b in items
        ]
    })

@app.get("/books/<int:book_id>")
def get_book(book_id: int):
    for b in books:
        if b["id"] == book_id:
            return jsonify({"data": b})
    abort(404, description="book not found")


@app.get("/authors")
def list_authors():
    limit = request.args.get("limit", default=len(authors), type=int)
    limit = max(1, min(limit, len(authors)))
    return jsonify({"data": authors[:limit]})

@app.get("/authors/<int:author_id>")
def get_author(author_id: int):
    for a in authors:
        if a["id"] == author_id:
            return jsonify({"data": a})
    abort(404, description="author not found")

@app.errorhandler(404)
def _not_found(err):
    return jsonify({"error": {"code": 404, "message": err.description}}), 404

if __name__ == "__main__":
    app.run(port=5000, debug=True)

from flask import Flask, jsonify, request

app = Flask(__name__)

books = {
    1: {"id": 1, "title": "Dune", "quantity": 3},
    2: {"id": 2, "title": "1984", "quantity": 0},
}

@app.route("/books/<int:book_id>", methods=["GET"])
def get_book(book_id):
    book = books.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    return jsonify(book)


@app.route("/books/<int:book_id>/borrow", methods=["POST"])
def borrow_book(book_id):
    book = books.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    if book["quantity"] <= 0:
        return jsonify({"message": "Book out of stock"}), 400

    book["quantity"] -= 1
    return jsonify({"message": "Borrow success", "book": book})


@app.route("/books/<int:book_id>/notify-me", methods=["POST"])
def notify_me(book_id):
    return jsonify({"message": "We will notify you when the book is available."})


if __name__ == "__main__":
    app.run(port=5003, debug=True)

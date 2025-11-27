from flask import Flask, jsonify, url_for

app = Flask(__name__)

books = {
    1: {"id": 1, "title": "Dune", "quantity": 3},
    2: {"id": 2, "title": "1984", "quantity": 0},
}

@app.route("/api/books/<int:book_id>", methods=["GET"])
def get_book_hateoas(book_id):
    book = books.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    response = {
        "data": book,
        "links": []
    }

    # Nếu còn sách: cho phép borrow
    if book["quantity"] > 0:
        response["links"].append({
            "rel": "borrow",
            "method": "POST",
            "href": url_for("borrow_book_hateoas", book_id=book_id, _external=True)
        })
    else:
        # Nếu hết sách: hướng user đến notify-me
        response["links"].append({
            "rel": "notify_me",
            "method": "POST",
            "href": url_for("notify_me_hateoas", book_id=book_id, _external=True)
        })

    return jsonify(response)


@app.route("/api/books/<int:book_id>/borrow", methods=["POST"])
def borrow_book_hateoas(book_id):
    book = books.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404

    if book["quantity"] <= 0:
        return jsonify({"error": "Book out of stock"}), 400

    book["quantity"] -= 1

    return jsonify({
        "message": "Borrow success",
        "book": book,
        "links": [
            {
                "rel": "self",
                "method": "GET",
                "href": url_for("get_book_hateoas", book_id=book_id, _external=True)
            }
        ]
    })


@app.route("/api/books/<int:book_id>/notify-me", methods=["POST"])
def notify_me_hateoas(book_id):
    return jsonify({
        "message": "You will be notified when the book is available."
    })


if __name__ == "__main__":
    app.run(port=5004, debug=True)

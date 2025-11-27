import requests

WEBHOOK_URL = "http://localhost:6000/webhook"  # Endpoint subcriber

def send_webhook(event_type, data):
    """
    event_type: str -> 'book.borrowed' | 'book.returned'
    data: dict -> thông tin sách, user...
    """
    payload = {
        "event": event_type,
        "data": data
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        print("Webhook sent:", response.status_code)
    except Exception as e:
        print("Failed to send webhook:", e)

############
# PUBLISHER
############

from flask import Flask, request, jsonify

app = Flask(__name__)

books = [
    {"id": 1, "title": "1984", "author": "George Orwell", "quantity": 2},
    {"id": 2, "title": "The Hobbit", "author": "J.R.R. Tolkien", "quantity": 1},
]

# Borrow book
@app.route("/books/<int:book_id>/borrow", methods=["POST"])
def borrow_book(book_id):
    book = next((b for b in books if b["id"] == book_id), None)
    if not book:
        return {"error": "Book not found"}, 404
    if book["quantity"] <= 0:
        return {"error": "Book not available"}, 400

    book["quantity"] -= 1

    # Gửi webhook thông báo sách đã được mượn
    send_webhook("book.borrowed", {"book_id": book_id, "title": book["title"]})

    return jsonify({"message": "Book borrowed", "book": book})

# Return book
@app.route("/books/<int:book_id>/return", methods=["POST"])
def return_book(book_id):
    book = next((b for b in books if b["id"] == book_id), None)
    if not book:
        return {"error": "Book not found"}, 404

    book["quantity"] += 1

    # Gửi webhook thông báo sách đã được trả lại
    send_webhook("book.returned", {"book_id": book_id, "title": book["title"]})

    return jsonify({"message": "Book returned", "book": book})

if __name__ == "__main__":
    app.run(port=5000, debug=True)

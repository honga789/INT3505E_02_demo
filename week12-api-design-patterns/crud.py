from flask import Flask, jsonify, request

app = Flask(__name__)

books = [
    {"id": 1, "title": "1984"},
    {"id": 2, "title": "Dune"}
]

@app.route("/books", methods=["GET"])
def get_books():
    return jsonify(books), 200

@app.route("/books", methods=["POST"])
def create_book():
    data = request.json
    new_book = {"id": len(books)+1, "title": data["title"]}
    books.append(new_book)
    return jsonify(new_book), 201

@app.route("/books/<int:id>", methods=["PUT"])
def update_book(id):
    data = request.json
    for b in books:
        if b["id"] == id:
            b["title"] = data["title"]
            return jsonify(b)
    return {"error": "Not found"}, 404

@app.route("/books/<int:id>", methods=["DELETE"])
def delete_book(id):
    global books
    books = [b for b in books if b["id"] != id]
    return {"message": "deleted"}, 204

app.run(5001)


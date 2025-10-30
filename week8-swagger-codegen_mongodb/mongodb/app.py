from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
import os

app = Flask(__name__)


MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
db = client["library"]
books = db["books"]

def to_json(doc):
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc


@app.get("/health")
def health():
    client.admin.command("ping")
    return {"status": "ok"}

@app.get("/books")
def list_books():
    items = [to_json(d) for d in books.find()]
    return jsonify(items)

@app.post("/books")
def create_book():
    data = request.get_json(force=True) or {}
    if "title" not in data:
        return {"error": "title is required"}, 400
    result = books.insert_one({
        "title": data["title"].strip(),
        "author": data.get("author"),
        "year": data.get("year"),
        "tags": data.get("tags", []),
    })
    doc = books.find_one({"_id": result.inserted_id})
    return to_json(doc), 201

@app.get("/books/<id>")
def get_book(id):
    try:
        doc = books.find_one({"_id": ObjectId(id)})
    except InvalidId:
        return {"error": "invalid id"}, 400
    if not doc:
        return {"error": "not found"}, 404
    return to_json(doc)

@app.patch("/books/<id>")
def update_book(id):
    try:
        _id = ObjectId(id)
    except InvalidId:
        return {"error": "invalid id"}, 400
    data = request.get_json(force=True) or {}
    result = books.find_one_and_update(
        {"_id": _id},
        {"$set": data},
        return_document=True
    )
    if not result:
        return {"error": "not found"}, 404
    return to_json(result)

@app.delete("/books/<id>")
def delete_book(id):
    try:
        _id = ObjectId(id)
    except InvalidId:
        return {"error": "invalid id"}, 400
    result = books.delete_one({"_id": _id})
    if result.deleted_count == 0:
        return {"error": "not found"}, 404
    return "", 204

if __name__ == "__main__":
    books.create_index("title")
    app.run(host="0.0.0.0", port=5000, debug=True)

from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)

BOOKS = [
    {"id": "1", "title": "Clean Code", "author": "Robert C. Martin", "available": True},
    {"id": "2", "title": "The Pragmatic Programmer", "author": "Andrew Hunt", "available": True},
]

USERS = {
    "admin":  {"password": "admin",  "role": "librarian"},
    "member": {"password": "member", "role": "member"},
}

def err(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status

@app.post("/svc/auth/check")
def svc_auth_check():
    data = request.get_json(silent=True) or {}
    u, p = data.get("username"), data.get("password")
    if not u or not p:
        return err("VALIDATION_ERROR", "username and password are required", 400)
    user = USERS.get(u)
    if not user or user["password"] != p:
        return err("INVALID_CREDENTIALS", "Invalid username or password", 401)
    return jsonify({"username": u, "role": user["role"]}), 200

@app.get("/svc/books")
def svc_list():
    return jsonify(BOOKS), 200

@app.get("/svc/books/<book_id>")
def svc_get(book_id):
    for b in BOOKS:
        if b["id"] == book_id:
            return jsonify(b), 200
    return err("NOT_FOUND", "Book not found", 404)

@app.post("/svc/books")
def svc_create():
    data = request.get_json(silent=True) or {}
    title, author = data.get("title"), data.get("author")
    if not title or not author:
        return err("VALIDATION_ERROR", "title and author are required", 400)
    new_book = {
        "id": str(uuid.uuid4()),
        "title": title,
        "author": author,
        "available": True,
    }
    BOOKS.append(new_book)
    return jsonify(new_book), 200

@app.put("/svc/books/<book_id>")
def svc_update(book_id):
    data = request.get_json(silent=True) or {}
    for b in BOOKS:
        if b["id"] == book_id:
            if "title" in data: b["title"] = data["title"]
            if "author" in data: b["author"] = data["author"]
            if "available" in data: b["available"] = bool(data["available"])
            return jsonify(b), 200
    return err("NOT_FOUND", "Book not found", 404)

@app.delete("/svc/books/<book_id>")
def svc_delete(book_id):
    for i, b in enumerate(BOOKS):
        if b["id"] == book_id:
            BOOKS.pop(i)
            return jsonify({"ok": True}), 200
    return err("NOT_FOUND", "Book not found", 404)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)

from flask import Flask, request, jsonify
from datetime import datetime, timezone
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

LOANS = []  # [{id, book_id, user_name, borrowed_at, returned_at}]

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


def _now_iso():
    return datetime.now(timezone.utc).isoformat()

@app.post("/svc/loans")
def svc_create_loan():
    data = request.get_json(silent=True) or {}
    book_id = data.get("book_id")
    user_name = data.get("user_name") or data.get("username")
    if not book_id or not user_name:
        return err("VALIDATION_ERROR", "book_id and user_name are required", 400)


    book = next((b for b in BOOKS if b["id"] == book_id), None)
    if not book:
        return err("NOT_FOUND", "Book not found", 404)
    if not book.get("available", False):
        return err("CONFLICT", "Book is not available", 409)

    loan = {
        "id": str(uuid.uuid4()),
        "book_id": book_id,
        "user_name": user_name,
        "borrowed_at": _now_iso(),
        "returned_at": None,
    }
    LOANS.append(loan)
    book["available"] = False
    return jsonify(loan), 200

@app.get("/svc/loans")
def svc_list_loans():
    q_user = request.args.get("user") or request.args.get("user_name")
    items = [l for l in LOANS if (not q_user or l["user_name"] == q_user)]
    return jsonify(items), 200

@app.get("/svc/loans/<loan_id>")
def svc_get_loan(loan_id):
    loan = next((l for l in LOANS if l["id"] == loan_id), None)
    if not loan:
        return err("NOT_FOUND", "Loan not found", 404)
    return jsonify(loan), 200

@app.put("/svc/loans/<loan_id>/returned")
def svc_return_loan(loan_id):
    data = request.get_json(silent=True) or {}
    actor = data.get("username") or data.get("user_name")
    is_librarian = bool(data.get("is_librarian"))

    if not actor and not is_librarian:
        return err("UNAUTHORIZED", "Missing actor", 401)

    loan = next((l for l in LOANS if l["id"] == loan_id), None)
    if not loan:
        return err("NOT_FOUND", "Loan not found", 404)

    if not is_librarian and loan["user_name"] != actor:
        return err("FORBIDDEN", "Not allowed", 403)
    
    if loan["returned_at"] is not None:
        return jsonify(loan), 200

    loan["returned_at"] = _now_iso()
    book = next((b for b in BOOKS if b["id"] == loan["book_id"]), None)
    if book:
        book["available"] = True

    return jsonify(loan), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)

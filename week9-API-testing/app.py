from flask import Flask, request, jsonify, make_response
import hashlib
import json
import jwt
import uuid
import datetime
from functools import wraps

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret123'
token_expiration_seconds = 2 * 60 * 60

users = [
    {"id": 1, "username": "admin",  "password": "admin",  "role": "librarian"},
    {"id": 2, "username": "member", "password": "member", "role": "member"},
]

books = [
    {"id": "1", "title": "Clean Code", "author": "Robert C. Martin", "available": True},
    {"id": "2", "title": "The Pragmatic Programmer", "author": "Andrew Hunt", "available": True},
]

def generate_token(user):
    now = datetime.datetime.now(datetime.UTC)
    payload = {
        'user_id': user['id'],
        'username': user['username'],
        'role': user['role'],
        'exp': now + datetime.timedelta(seconds=token_expiration_seconds)
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token


def decode_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}


def require_token(role=None):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            authz = request.headers.get('Authorization', '')
            if not authz.lower().startswith('bearer '):
                return {"error": "Unauthorized"}, 401
            token = authz.split(" ", 1)[1]
            decoded = decode_token(token)
            if isinstance(decoded, dict) and "error" in decoded:
                return decoded, 401
            if role and decoded.get('role') != role:
                return {"error": "Forbidden"}, 403
            request.user = decoded
            return f(*args, **kwargs)
        return wrapper
    return decorator


def _etag_for(data_obj) -> str:
    body = json.dumps(data_obj, sort_keys=True, separators=(",", ":")).encode('utf-8')
    return hashlib.md5(body).hexdigest()


def _find_book(book_id: str):
    return next((b for b in books if b["id"] == book_id), None)


@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return {"error": "Request must be JSON"}, 415
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    user = next((u for u in users if u['username'] == username and u['password'] == password), None)
    if not user:
        return {"error": "Invalid credentials"}, 401
    token = generate_token(user)
    return jsonify({
        "token": token,
        "token_type": "Bearer",
        "expires_in": token_expiration_seconds,
        "user": {"username": user['username'], "role": user['role']}
    })


@app.route('/books', methods=['GET'])
def list_books():
    q = (request.args.get('search') or '').strip().lower()
    data = books
    if q:
        data = [b for b in books if q in b['title'].lower() or q in b['author'].lower()]

    etag = _etag_for(data)
    client_etag = request.headers.get('If-None-Match')
    if client_etag and client_etag == etag:
        resp = make_response('', 304)
        resp.headers['ETag'] = etag
        resp.headers['Cache-Control'] = 'public, max-age=60'
        return resp

    resp = make_response(jsonify(data), 200)
    resp.headers['ETag'] = etag
    resp.headers['Cache-Control'] = 'public, max-age=60'
    return resp


@app.route('/books/<book_id>', methods=['GET'])
def get_book(book_id):
    b = _find_book(book_id)
    if not b:
        return {"error": "Book not found"}, 404

    etag = _etag_for(b)
    client_etag = request.headers.get('If-None-Match')
    if client_etag and client_etag == etag:
        resp = make_response('', 304)
        resp.headers['ETag'] = etag
        resp.headers['Cache-Control'] = 'public, max-age=60'
        return resp

    resp = make_response(jsonify(b), 200)
    resp.headers['ETag'] = etag
    resp.headers['Cache-Control'] = 'public, max-age=60'
    return resp


@app.route('/books', methods=['POST'])
@require_token()
def create_book():
    if not request.is_json:
        return {"error": "Request must be JSON"}, 415
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    author = (data.get('author') or '').strip()
    if not title or not author:
        return {"error": "Title and author are required"}, 400

    new_book = {
        "id": str(uuid.uuid4()),
        "title": title,
        "author": author,
        "available": bool(data.get('available', True))
    }
    books.append(new_book)

    resp = make_response(jsonify(new_book), 201)
    resp.headers['Location'] = f"/books/{new_book['id']}"
    return resp


@app.route('/books/<book_id>', methods=['PUT'])
@require_token()
def update_book(book_id):
    b = _find_book(book_id)
    if not b:
        return {"error": "Book not found"}, 404

    if not request.is_json:
        return {"error": "Request must be JSON"}, 415

    data = request.get_json() or {}
    if 'title' in data: b['title'] = (data['title'] or '').strip()
    if 'author' in data: b['author'] = (data['author'] or '').strip()
    if 'available' in data: b['available'] = bool(data['available'])

    return jsonify(b), 200


@app.route('/books/<book_id>', methods=['DELETE'])
@require_token(role='librarian')
def delete_book(book_id):
    for i, bk in enumerate(books):
        if bk['id'] == book_id:
            books.pop(i)
            return '', 204
    return {"error": "Book not found"}, 404


if __name__ == '__main__':
    app.run(port=5000, debug=True)

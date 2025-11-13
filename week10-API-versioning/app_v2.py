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
    {
        "id": str(uuid.uuid4()),
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "available": True
    },
    {
        "id": str(uuid.uuid4()),
        "title": "The Pragmatic Programmer",
        "author": "Andrew Hunt, David Thomas",
        "available": True
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Designing Data-Intensive Applications",
        "author": "Martin Kleppmann",
        "available": False
    }
]


def _etag_for(payload):
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def generate_token(user):
    payload = {
        'sub': user['id'],
        'username': user['username'],
        'role': user['role'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=token_expiration_seconds),
        'iat': datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


def require_token(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get('Authorization', '')
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return {"error": "Missing or invalid Authorization header"}, 401

            token = parts[1]
            try:
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return {"error": "Token expired"}, 401
            except jwt.InvalidTokenError:
                return {"error": "Invalid token"}, 401

            if role and data.get('role') != role:
                return {"error": "Forbidden. Insufficient role"}, 403

            request.user = {
                'id': data['sub'],
                'username': data['username'],
                'role': data['role'],
            }
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def _find_book(book_id: str):
    for b in books:
        if b['id'] == book_id:
            return b
    return None


@app.route('/api/v2/login', methods=['POST'])
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


@app.route('/api/v2/books', methods=['GET'])
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


@app.route('/api/v2/books/<book_id>', methods=['GET'])
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


@app.route('/api/v2/books', methods=['POST'])
@require_token()
def create_book():
    if not request.is_json:
        return {"error": "Request must be JSON"}, 415

    data = request.get_json() or {}
    title = data.get('title')
    author = data.get('author')

    if not title or not author:
        return {"error": "title and author are required"}, 400
    
    if 'available' not in data:
        return {"error": "available is required"}, 400

    available = data['available']

    new_book = {
        'id': str(uuid.uuid4()),
        'title': title,
        'author': author,
        'available': bool(available)
    }
    books.append(new_book)
    resp = make_response(jsonify(new_book), 201)
    resp.headers['Location'] = f"/api/v2/books/{new_book['id']}"
    return resp


@app.route('/api/v2/books/<book_id>', methods=['PUT'])
@require_token()
def update_book(book_id):
    b = _find_book(book_id)
    if not b:
        return {"error": "Book not found"}, 404
    if not request.is_json:
        return {"error": "Request must be JSON"}, 415

    data = request.get_json() or {}
    if 'title' in data:
        b['title'] = data['title']
    if 'author' in data:
        b['author'] = data['author']
    if 'available' in data:
        b['available'] = bool(data['available'])

    return jsonify(b)


@app.route('/api/v2/books/<book_id>', methods=['DELETE'])
@require_token(role='librarian')
def delete_book(book_id):
    for i, bk in enumerate(books):
        if bk['id'] == book_id:
            books.pop(i)
            return '', 204
    return {"error": "Book not found"}, 404


if __name__ == '__main__':
    app.run(port=5000, debug=True)

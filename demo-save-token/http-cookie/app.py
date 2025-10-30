from flask import Flask, request, jsonify, make_response, send_from_directory
import jwt
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'

@app.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')

    if username == 'admin' and password == 'admin':
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        token = jwt.encode(
            {'user': username, 'exp': expires_at},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        
        if isinstance(token, bytes):
            token = token.decode('utf-8')

        resp = make_response(jsonify({'message': 'Login successful'}))
        resp.set_cookie(
            'access_token',
            token,
            httponly=True,
            samesite='Lax',
            max_age=30
        )
        return resp

    return jsonify({'message': 'Invalid username or password'}), 401


@app.route('/protected', methods=['GET'])
def protected():
    token = request.cookies.get('access_token')
    if not token:
        return jsonify({'message': 'Missing token'}), 401

    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return jsonify({'message': 'Access granted!', 'user': payload.get('user')})
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401


@app.route('/', methods=['GET'])
def home():
    return send_from_directory('.', 'index.html')


if __name__ == "__main__":
    app.run(port=5000, debug=True)

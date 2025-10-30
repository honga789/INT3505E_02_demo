from flask import Flask, request, jsonify, send_from_directory
import jwt
import os
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret123')

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

        return jsonify({'token': token})

    return jsonify({'message': 'Invalid username or password'}), 401


@app.route('/', methods=['GET'])
def home():
    return send_from_directory('.', 'index.html')


if __name__ == "__main__":
    app.run(port=5000, debug=True)

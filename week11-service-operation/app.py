import logging
from flask import Flask, jsonify, request
from prometheus_flask_exporter import PrometheusMetrics
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("library.log"), logging.StreamHandler()]
)
logger = logging.getLogger("LibraryService")

metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Library API', version='1.0.0')

book_not_found_counter = metrics.counter(
    'book_not_found_total', 'Count of requests for non-existent books'
)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "60 per hour"],
    storage_uri="memory://"
)

books = [
    {"id": 1, "title": "Dế Mèn Phiêu Lưu Ký", "author": "Tô Hoài"},
    {"id": 2, "title": "Số Đỏ", "author": "Vũ Trọng Phụng"}
]

@app.route('/books', methods=['GET'])
def get_all_books():
    logger.info("Client requested book list")
    return jsonify({"count": len(books), "data": books})

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book_detail(book_id):
    book = next((b for b in books if b["id"] == book_id), None)
    
    if book:
        return jsonify(book)
    
    logger.warning(f"Book lookup failed for ID: {book_id}")
    book_not_found_counter.inc()
    return jsonify({"error": "Book not found"}), 404

# Rate Limit
@app.route('/books', methods=['POST'])
@limiter.limit("3 per minute")
def add_book():
    data = request.json
    if not data or 'title' not in data:
        logger.error("Invalid payload for adding book")
        return jsonify({"error": "Invalid data"}), 400

    new_book = {
        "id": len(books) + 1,
        "title": data['title'],
        "author": data.get('author', 'Unknown')
    }
    books.append(new_book)
    
    logger.info(f"New book added: {new_book['title']}")
    return jsonify(new_book), 201

# Endpoint test lỗi 500
@app.route('/system/error')
def simulate_crash():
    try:
        1 / 0
    except Exception as e:
        logger.error(f"System crash: {str(e)}")
        return jsonify({"error": "Internal Error"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
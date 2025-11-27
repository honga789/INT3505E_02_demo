from flask import Flask, request, jsonify

app = Flask(__name__)

books = [
    {"id": 1, "title": "1984", "author": "George Orwell", "year": 1949},
    {"id": 2, "title": "Dune", "author": "Frank Herbert", "year": 1965},
    {"id": 3, "title": "The Hobbit", "author": "J.R.R. Tolkien", "year": 1937},
    {"id": 4, "title": "Brave New World", "author": "Aldous Huxley", "year": 1932},
    {"id": 5, "title": "Harry Potter", "author": "J.K. Rowling", "year": 1997},
]

@app.route("/api/books", methods=["GET"])
def query_books():

    data = books

    # ---------------------------
    # 1. FILTERING
    # ---------------------------
    author = request.args.get("author")
    year_lt = request.args.get("year_lt")
    year_gt = request.args.get("year_gt")

    if author:
        data = [b for b in data if author.lower() in b["author"].lower()]

    if year_lt:
        data = [b for b in data if b["year"] < int(year_lt)]

    if year_gt:
        data = [b for b in data if b["year"] > int(year_gt)]

    # ---------------------------
    # 2. SORTING
    # ---------------------------
    sort = request.args.get("sort")   # sort=year, sort=-year
    if sort:
        reverse = sort.startswith("-")
        sort_key = sort.lstrip("-")

        if sort_key in data[0]:
            data = sorted(data, key=lambda x: x[sort_key], reverse=reverse)

    # ---------------------------
    # 3. FIELD SELECTION
    # ---------------------------
    fields = request.args.get("fields")
    if fields:
        field_list = fields.split(",")
        data = [
            {k: v for k, v in b.items() if k in field_list}
            for b in data
        ]

    # ---------------------------
    # 4. PAGINATION
    # ---------------------------
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 2))

    start = (page - 1) * limit
    end = start + limit

    total_pages = (len(data) + limit - 1) // limit

    paged_data = data[start:end]

    return jsonify({
        "page": page,
        "total_pages": total_pages,
        "total_items": len(data),
        "results": paged_data
    })


if __name__ == "__main__":
    app.run(port=5002, debug=True)

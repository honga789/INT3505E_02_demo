from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from ..extensions import db
from ..models.book import Book
from ._utils import parse_pagination, apply_sorting, api_error

books_api_bp = Blueprint("books_api", __name__)

@books_api_bp.get("")
@jwt_required()
def list_books():
    page, page_size = parse_pagination()
    q = Book.query
    search = request.args.get("search")
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Book.title.ilike(like), Book.author.ilike(like)))
    category = request.args.get("category")
    if category:
        q = q.filter(Book.category == category)

    q = apply_sorting(q, Book, allowed_fields=("id", "title", "author", "year", "created_at"))
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return jsonify({"data": [b.to_dict() for b in items], "meta": {"page": page, "page_size": page_size, "total": total}})

@books_api_bp.post("")
@jwt_required()
def create_book():
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    author = data.get("author")
    total_copies = int(data.get("total_copies", 1))
    if not title or not author or total_copies < 0:
        return api_error("INVALID_INPUT", "Missing title/author or invalid copies", 422)
    b = Book(
        isbn=data.get("isbn"),
        title=title,
        author=author,
        category=data.get("category"),
        publisher=data.get("publisher"),
        year=data.get("year"),
        total_copies=total_copies,
        available_copies=data.get("available_copies", total_copies),
        location=data.get("location"),
    )
    if b.available_copies > b.total_copies or b.available_copies < 0:
        return api_error("INVALID_INPUT", "available_copies must be within [0, total_copies]", 422)
    db.session.add(b)
    db.session.commit()
    return jsonify(b.to_dict()), 201

@books_api_bp.get("/<int:bid>")
@jwt_required()
def get_book(bid):
    b = Book.query.get_or_404(bid)
    return jsonify(b.to_dict())

@books_api_bp.put("/<int:bid>")
@jwt_required()
def update_book(bid):
    b = Book.query.get_or_404(bid)
    data = request.get_json(silent=True) or {}
    for field in ["isbn", "title", "author", "category", "publisher", "year", "location"]:
        if field in data:
            setattr(b, field, data[field])
    if "total_copies" in data:
        b.total_copies = int(data["total_copies"])
    if "available_copies" in data:
        b.available_copies = int(data["available_copies"])
    if b.available_copies < 0 or b.available_copies > b.total_copies:
        return api_error("INVALID_INPUT", "available_copies must be within [0, total_copies]", 422)
    db.session.commit()
    return jsonify(b.to_dict())

@books_api_bp.delete("/<int:bid>")
@jwt_required()
def delete_book(bid):
    from ..models.loan import Loan
    b = Book.query.get_or_404(bid)
    active = Loan.query.filter(Loan.book_id == bid, Loan.returned_at.is_(None)).count()
    if active > 0:
        return api_error("BOOK_HAS_ACTIVE_LOANS", "Cannot delete a book with active loans", 409)
    db.session.delete(b)
    db.session.commit()
    return jsonify({"deleted": True})

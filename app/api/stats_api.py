from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from ..models.book import Book
from ..models.loan import Loan

stats_api_bp = Blueprint("stats_api", __name__)

@stats_api_bp.get("")
@jwt_required()
def stats():
    total_books = Book.query.count()
    available_books = Book.query.with_entities(func.sum(Book.available_copies)).scalar() or 0
    active_loans = Loan.query.filter(Loan.returned_at.is_(None)).count()
    overdue_loans = Loan.query.filter(Loan.returned_at.is_(None), Loan.due_at < func.now()).count()
    # thống kê top đơn giản
    top = (
        Loan.query.with_entities(Loan.book_id, func.count(Loan.id).label("loan_count"))
        .group_by(Loan.book_id).order_by(func.count(Loan.id).desc()).limit(5).all()
    )
    from ..models.book import Book as B
    top_books = []
    for book_id, count in top:
        b = B.query.get(book_id)
        if b:
            top_books.append({"book_id": book_id, "title": b.title, "loan_count": count})
    return jsonify({
        "total_books": total_books,
        "available_books": int(available_books),
        "active_loans": active_loans,
        "overdue_loans": overdue_loans,
        "top_books": top_books
    })

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from ..extensions import db
from ..models.loan import Loan
from ..services.loan_service import create_loan, return_loan, renew_loan, LoanError
from ._utils import parse_pagination, apply_sorting, api_error

loans_api_bp = Blueprint("loans_api", __name__)

@loans_api_bp.get("")
@jwt_required()
def list_loans():
    page, page_size = parse_pagination()
    q = Loan.query
    status = request.args.get("status")
    if status:
        q = q.filter(Loan.status == status)
    member_id = request.args.get("member_id")
    if member_id:
        q = q.filter(Loan.member_id == int(member_id))
    book_id = request.args.get("book_id")
    if book_id:
        q = q.filter(Loan.book_id == int(book_id))

    q = apply_sorting(q, Loan, allowed_fields=("id", "loaned_at", "due_at", "status"))
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return jsonify({"data": [l.to_dict() for l in items], "meta": {"page": page, "page_size": page_size, "total": total}})

@loans_api_bp.post("")
@jwt_required()
def create_loan_api():
    data = request.get_json(silent=True) or {}
    try:
        loan = create_loan(int(data.get("book_id")), int(data.get("member_id")), int(data.get("due_days", 14)))
        db.session.commit()
        return jsonify(loan.to_dict()), 201
    except LoanError as e:
        db.session.rollback()
        return api_error(e.code, e.message, 409)
    except Exception:
        db.session.rollback()
        return api_error("INVALID_INPUT", "Invalid book_id/member_id", 422)

@loans_api_bp.post("/<int:loan_id>/return")
@jwt_required()
def return_loan_api(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    return_loan(loan)
    db.session.commit()
    return jsonify(loan.to_dict())

@loans_api_bp.post("/<int:loan_id>/renew")
@jwt_required()
def renew_loan_api(loan_id):
    loan = Loan.query.get_or_404(loan_id)
    data = request.get_json(silent=True) or {}
    extra = int(data.get("extra_days", 7))
    try:
        renew_loan(loan, extra)
        db.session.commit()
        return jsonify(loan.to_dict())
    except LoanError as e:
        db.session.rollback()
        return api_error(e.code, e.message, 400)

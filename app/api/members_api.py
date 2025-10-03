from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from ..extensions import db
from ..models.member import Member
from ._utils import parse_pagination, apply_sorting, api_error

members_api_bp = Blueprint("members_api", __name__)

@members_api_bp.get("")
@jwt_required()
def list_members():
    page, page_size = parse_pagination()
    q = Member.query
    search = request.args.get("search")
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Member.name.ilike(like), Member.code.ilike(like)))
    q = apply_sorting(q, Member, allowed_fields=("id", "name", "code"))
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return jsonify({"data": [m.to_dict() for m in items], "meta": {"page": page, "page_size": page_size, "total": total}})

@members_api_bp.post("")
@jwt_required()
def create_member():
    data = request.get_json(silent=True) or {}
    if not data.get("code") or not data.get("name"):
        return api_error("INVALID_INPUT", "Missing code or name", 422)
    m = Member(code=data["code"], name=data["name"], phone=data.get("phone"), email=data.get("email"))
    db.session.add(m)
    db.session.commit()
    return jsonify(m.to_dict()), 201

@members_api_bp.get("/<int:mid>")
@jwt_required()
def get_member(mid):
    m = Member.query.get_or_404(mid)
    return jsonify(m.to_dict())

@members_api_bp.put("/<int:mid>")
@jwt_required()
def update_member(mid):
    m = Member.query.get_or_404(mid)
    data = request.get_json(silent=True) or {}
    for f in ["code", "name", "phone", "email"]:
        if f in data:
            setattr(m, f, data[f])
    db.session.commit()
    return jsonify(m.to_dict())

@members_api_bp.delete("/<int:mid>")
@jwt_required()
def delete_member(mid):
    m = Member.query.get_or_404(mid)
    db.session.delete(m)
    db.session.commit()
    return jsonify({"deleted": True})

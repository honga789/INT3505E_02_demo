from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from ..models.admin_user import AdminUser

auth_api_bp = Blueprint("auth_api", __name__)

@auth_api_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": {"code": "INVALID_INPUT", "message": "Missing username or password"}}), 422

    user = AdminUser.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": {"code": "INVALID_CREDENTIALS", "message": "Invalid username/password"}}), 401

    token = create_access_token(
        identity=str(user.id),
        additional_claims={"username": user.username}
    )
    return jsonify({"access_token": token, "expires_in": 3600})

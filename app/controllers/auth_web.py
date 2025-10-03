from flask import Blueprint, render_template

auth_web_bp = Blueprint("auth_web", __name__)

@auth_web_bp.get("/login")
def login_page():
    return render_template("login.html")

@auth_web_bp.get("/logout")
def logout_page():
    # Client xoá token bằng JS rồi chuyển về /login
    return render_template("login.html", logout=True)

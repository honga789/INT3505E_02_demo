from flask import Blueprint, render_template

loans_web_bp = Blueprint("loans_web", __name__)

@loans_web_bp.get("/loans")
def loans_page():
    return render_template("loans.html")

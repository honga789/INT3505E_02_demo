from flask import Blueprint, render_template

books_web_bp = Blueprint("books_web", __name__)

@books_web_bp.get("/books")
def books_page():
    return render_template("books.html")

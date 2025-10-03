from flask import Blueprint, render_template

dashboard_web_bp = Blueprint("dashboard_web", __name__)

@dashboard_web_bp.get("/")
def dashboard():
    return render_template("dashboard.html")

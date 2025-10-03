from flask import Flask
from .extensions import db, migrate, bcrypt, jwt
from .api.auth_api import auth_api_bp
from .api.books_api import books_api_bp
from .api.members_api import members_api_bp
from .api.loans_api import loans_api_bp
from .api.stats_api import stats_api_bp
from .controllers.auth_web import auth_web_bp
from .controllers.dashboard_web import dashboard_web_bp
from .controllers.books_web import books_web_bp
from .controllers.loans_web import loans_web_bp
from .models.admin_user import AdminUser
from .models.book import Book
from .models.member import Member
from .models.loan import Loan
from .seed import seed_data

def create_app():
    app = Flask(__name__, static_folder="views/static", template_folder="views/templates")
    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # API v1
    app.register_blueprint(auth_api_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(books_api_bp, url_prefix="/api/v1/books")
    app.register_blueprint(members_api_bp, url_prefix="/api/v1/members")
    app.register_blueprint(loans_api_bp, url_prefix="/api/v1/loans")
    app.register_blueprint(stats_api_bp, url_prefix="/api/v1/stats")

    # Web (admin)
    app.register_blueprint(auth_web_bp)
    app.register_blueprint(dashboard_web_bp)
    app.register_blueprint(books_web_bp)
    app.register_blueprint(loans_web_bp)

    @app.cli.command("init-db")
    def init_db():
        """Khởi tạo DB & seed dữ liệu tối thiểu."""
        with app.app_context():
            db.create_all()
            seed_data()
            print("Database initialized & seeded.")

    return app

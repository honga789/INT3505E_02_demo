from .extensions import db
from .models.admin_user import AdminUser
from .models.book import Book
from .models.member import Member

def seed_data():
    # admin
    if not AdminUser.query.filter_by(username="admin").first():
        AdminUser.create("admin", "admin123")
    # books
    if Book.query.count() == 0:
        samples = [
            Book(title="Clean Code", author="Robert C. Martin", category="SE", total_copies=3, available_copies=3, year=2008, location="A1"),
            Book(title="The Pragmatic Programmer", author="Andrew Hunt", category="SE", total_copies=2, available_copies=2, year=1999, location="A1"),
            Book(title="Introduction to Algorithms", author="CLRS", category="Algorithms", total_copies=2, available_copies=2, year=2009, location="B2"),
        ]
        for s in samples: db.session.add(s)
    # members
    if Member.query.count() == 0:
        ms = [
            Member(code="M001", name="Nguyen Van A", phone="0901", email="a@example.com"),
            Member(code="M002", name="Tran Thi B", phone="0902", email="b@example.com"),
        ]
        for m in ms: db.session.add(m)
    db.session.commit()

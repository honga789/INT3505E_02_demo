from datetime import datetime
from ..extensions import db

class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(32), unique=True, nullable=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(128), nullable=True)
    publisher = db.Column(db.String(255), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    total_copies = db.Column(db.Integer, nullable=False, default=1)
    available_copies = db.Column(db.Integer, nullable=False, default=1)
    location = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "isbn": self.isbn,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "publisher": self.publisher,
            "year": self.year,
            "total_copies": self.total_copies,
            "available_copies": self.available_copies,
            "location": self.location,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

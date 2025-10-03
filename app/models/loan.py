from datetime import datetime, timedelta
from ..extensions import db

class Loan(db.Model):
    __tablename__ = "loans"
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=False)
    loaned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_at = db.Column(db.DateTime, nullable=False)
    returned_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(16), default="ACTIVE", nullable=False)
    renew_count = db.Column(db.Integer, default=0, nullable=False)

    book = db.relationship("Book")
    member = db.relationship("Member")

    @staticmethod
    def default_due(days=14):
        return datetime.utcnow() + timedelta(days=days)

    def to_dict(self, include_refs=True):
        data = {
            "id": self.id,
            "book_id": self.book_id,
            "member_id": self.member_id,
            "loaned_at": self.loaned_at.isoformat(),
            "due_at": self.due_at.isoformat(),
            "returned_at": self.returned_at.isoformat() if self.returned_at else None,
            "status": self.status,
            "renew_count": self.renew_count,
        }
        if include_refs:
            data["book"] = {"id": self.book.id, "title": self.book.title} if self.book else None
            data["member"] = {"id": self.member.id, "name": self.member.name} if self.member else None
        return data

from datetime import timedelta, datetime
from ..extensions import db
from ..models.book import Book
from ..models.loan import Loan

MAX_RENEW = 2

class LoanError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)

def create_loan(book_id: int, member_id: int, due_days: int = 14) -> Loan:
    book = Book.query.get(book_id)
    if not book:
        raise LoanError("BOOK_NOT_FOUND", "Book not found")
    if book.available_copies <= 0:
        raise LoanError("BOOK_NOT_AVAILABLE", "No available copies")

    loan = Loan(book_id=book_id, member_id=member_id, due_at=Loan.default_due(due_days))
    book.available_copies -= 1
    db.session.add(loan)
    db.session.flush()
    return loan

def return_loan(loan: Loan) -> Loan:
    if loan.returned_at:
        return loan
    loan.returned_at = datetime.utcnow()
    loan.status = "RETURNED"
    loan.book.available_copies += 1
    return loan

def renew_loan(loan: Loan, extra_days: int = 7) -> Loan:
    if loan.returned_at:
        raise LoanError("ALREADY_RETURNED", "Loan already returned")
    if loan.renew_count >= MAX_RENEW:
        raise LoanError("RENEW_LIMIT_REACHED", "Renew limit reached")
    if loan.due_at < datetime.utcnow():
        raise LoanError("CANNOT_RENEW_OVERDUE", "Loan is overdue")

    loan.due_at = loan.due_at + timedelta(days=extra_days)
    loan.renew_count += 1
    return loan

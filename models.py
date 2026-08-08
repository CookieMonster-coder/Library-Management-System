from datetime import datetime

class User:
    """Base User class representing standard library user attributes and permissions."""
    def __init__(self, user_id: int, username: str, full_name: str, email: str, role: str, created_at: str = None):
        self.user_id = user_id
        self.username = username
        self.full_name = full_name
        self.email = email
        self.role = role
        self.created_at = created_at

    def __repr__(self):
        return f"<{self.role.capitalize()}(id={self.user_id}, username='{self.username}', name='{self.full_name}')>"

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'created_at': str(self.created_at) if self.created_at else None
        }


class Admin(User):
    """Admin Entity: Oversees librarians, students, system configuration, and audit reports."""
    def __init__(self, user_id: int, username: str, full_name: str, email: str, created_at: str = None):
        super().__init__(user_id, username, full_name, email, role='admin', created_at=created_at)


class Librarian(User):
    """Librarian Entity: Manages catalog, inventory, book issues, returns, and fines."""
    def __init__(self, user_id: int, username: str, full_name: str, email: str, created_at: str = None):
        super().__init__(user_id, username, full_name, email, role='librarian', created_at=created_at)


class Student(User):
    """Student Entity: Browses catalog, borrows/returns books, reserves titles, pays fines."""
    def __init__(self, user_id: int, username: str, full_name: str, email: str, created_at: str = None):
        super().__init__(user_id, username, full_name, email, role='student', created_at=created_at)


class Book:
    """Book Entity representing a catalog title and available copies."""
    def __init__(self, book_id: int, isbn: str, title: str, author: str, category: str, 
                 total_copies: int, available_copies: int, publisher: str = "", publication_year: int = None):
        self.book_id = book_id
        self.isbn = isbn
        self.title = title
        self.author = author
        self.category = category
        self.total_copies = total_copies
        self.available_copies = available_copies
        self.publisher = publisher
        self.publication_year = publication_year

    def is_available(self) -> bool:
        return self.available_copies > 0

    def to_dict(self):
        return {
            'book_id': self.book_id,
            'isbn': self.isbn,
            'title': self.title,
            'author': self.author,
            'category': self.category,
            'total_copies': self.total_copies,
            'available_copies': self.available_copies,
            'publisher': self.publisher,
            'publication_year': self.publication_year
        }


class LoanTransaction:
    """Transaction Entity representing a book borrow record."""
    def __init__(self, transaction_id: int, book_id: int, student_id: int, issued_by_id: int,
                 issue_date: str, due_date: str, return_date: str = None, status: str = 'issued',
                 book_title: str = "", student_name: str = "", issuer_name: str = ""):
        self.transaction_id = transaction_id
        self.book_id = book_id
        self.student_id = student_id
        self.issued_by_id = issued_by_id
        self.issue_date = issue_date
        self.due_date = due_date
        self.return_date = return_date
        self.status = status
        # Expanded fields for visual displays
        self.book_title = book_title
        self.student_name = student_name
        self.issuer_name = issuer_name

    def to_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'book_id': self.book_id,
            'book_title': self.book_title,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'issued_by_id': self.issued_by_id,
            'issuer_name': self.issuer_name,
            'issue_date': str(self.issue_date),
            'due_date': str(self.due_date),
            'return_date': str(self.return_date) if self.return_date else None,
            'status': self.status
        }


class Fine:
    """Fine Entity representing an overdue fine."""
    def __init__(self, fine_id: int, transaction_id: int, student_id: int, amount: float,
                 status: str = 'unpaid', created_at: str = None, student_name: str = "", book_title: str = ""):
        self.fine_id = fine_id
        self.transaction_id = transaction_id
        self.student_id = student_id
        self.amount = amount
        self.status = status
        self.created_at = created_at
        self.student_name = student_name
        self.book_title = book_title

    def to_dict(self):
        return {
            'fine_id': self.fine_id,
            'transaction_id': self.transaction_id,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'book_title': self.book_title,
            'amount': self.amount,
            'status': self.status,
            'created_at': str(self.created_at) if self.created_at else None
        }


class Reservation:
    """Reservation Entity representing a student's hold on a book."""
    def __init__(self, reservation_id: int, book_id: int, student_id: int, reserved_at: str = None,
                 status: str = 'pending', book_title: str = "", student_name: str = ""):
        self.reservation_id = reservation_id
        self.book_id = book_id
        self.student_id = student_id
        self.reserved_at = reserved_at
        self.status = status
        self.book_title = book_title
        self.student_name = student_name

    def to_dict(self):
        return {
            'reservation_id': self.reservation_id,
            'book_id': self.book_id,
            'book_title': self.book_title,
            'student_id': self.student_id,
            'student_name': self.student_name,
            'reserved_at': str(self.reserved_at) if self.reserved_at else None,
            'status': self.status
        }

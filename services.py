from datetime import datetime, date, timedelta
import sqlite3
from database import get_connection, hash_password, DB_NAME
from models import Admin, Librarian, Student, Book, LoanTransaction, Fine, Reservation, User

class LibraryService:
    """Core business logic for Library Management System covering Admin, Librarian, and Student actions."""

    def __init__(self, db_path=DB_NAME):
        self.db_path = db_path

    # ==================== AUTHENTICATION & USERS ====================

    def authenticate(self, username: str, password: str):
        """Authenticates user credentials and returns specific role entity object or None."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        pwd_hash = hash_password(password)

        cursor.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?;", (username, pwd_hash))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        role = row['role']
        if role == 'admin':
            return Admin(row['user_id'], row['username'], row['full_name'], row['email'], row['created_at'])
        elif role == 'librarian':
            return Librarian(row['user_id'], row['username'], row['full_name'], row['email'], row['created_at'])
        elif role == 'student':
            return Student(row['user_id'], row['username'], row['full_name'], row['email'], row['created_at'])
        return None

    def create_user(self, username: str, password: str, full_name: str, email: str, role: str):
        """Creates a new user account (Admin only)."""
        if role not in ('admin', 'librarian', 'student'):
            raise ValueError("Invalid user role specified.")

        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            pwd_hash = hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, email, role)
                VALUES (?, ?, ?, ?, ?);
            """, (username, pwd_hash, full_name, email, role))
            conn.commit()
            user_id = cursor.lastrowid
            return user_id
        except sqlite3.IntegrityError:
            raise ValueError(f"Username '{username}' is already taken.")
        finally:
            conn.close()

    def get_user_by_id(self, user_id: int):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?;", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return User(row['user_id'], row['username'], row['full_name'], row['email'], row['role'], row['created_at'])
        return None

    def get_all_users(self, role_filter: str = None):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        if role_filter:
            cursor.execute("SELECT user_id, username, full_name, email, role, created_at FROM users WHERE role = ? ORDER BY user_id DESC;", (role_filter,))
        else:
            cursor.execute("SELECT user_id, username, full_name, email, role, created_at FROM users ORDER BY user_id DESC;")

        rows = cursor.fetchall()
        conn.close()

        users = []
        for r in rows:
            users.append(User(r['user_id'], r['username'], r['full_name'], r['email'], r['role'], r['created_at']))
        return users

    def update_user(self, user_id: int, full_name: str, email: str, role: str, new_password: str = None):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        if new_password and new_password.strip():
            pwd_hash = hash_password(new_password)
            cursor.execute("""
                UPDATE users SET full_name = ?, email = ?, role = ?, password_hash = ?
                WHERE user_id = ?;
            """, (full_name, email, role, pwd_hash, user_id))
        else:
            cursor.execute("""
                UPDATE users SET full_name = ?, email = ?, role = ?
                WHERE user_id = ?;
            """, (full_name, email, role, user_id))

        conn.commit()
        conn.close()
        return True

    def delete_user(self, user_id: int):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        # Check if user has active loans
        cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE student_id = ? AND status = 'issued';", (user_id,))
        if cursor.fetchone()['count'] > 0:
            conn.close()
            raise ValueError("Cannot delete user with active borrowed books.")

        cursor.execute("DELETE FROM users WHERE user_id = ?;", (user_id,))
        conn.commit()
        conn.close()
        return True

    # ==================== BOOK MANAGEMENT ====================

    def get_all_books(self, search_query: str = None, category_filter: str = None):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM books WHERE 1=1"
        params = []

        if search_query:
            query += " AND (title LIKE ? OR author LIKE ? OR isbn LIKE ? OR category LIKE ?)"
            term = f"%{search_query}%"
            params.extend([term, term, term, term])

        if category_filter:
            query += " AND category = ?"
            params.append(category_filter)

        query += " ORDER BY book_id DESC;"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        books = []
        for r in rows:
            books.append(Book(
                r['book_id'], r['isbn'], r['title'], r['author'], r['category'],
                r['total_copies'], r['available_copies'], r['publisher'], r['publication_year']
            ))
        return books

    def get_categories(self):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM books ORDER BY category ASC;")
        rows = cursor.fetchall()
        conn.close()
        return [r['category'] for r in rows if r['category']]

    def get_book_by_id(self, book_id: int):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books WHERE book_id = ?;", (book_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return Book(
                row['book_id'], row['isbn'], row['title'], row['author'], row['category'],
                row['total_copies'], row['available_copies'], row['publisher'], row['publication_year']
            )
        return None

    def add_book(self, isbn: str, title: str, author: str, category: str, 
                 total_copies: int, publisher: str = "", publication_year: int = None):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO books (isbn, title, author, category, total_copies, available_copies, publisher, publication_year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (isbn, title, author, category, total_copies, total_copies, publisher, publication_year))
            conn.commit()
            book_id = cursor.lastrowid
            return book_id
        except sqlite3.IntegrityError:
            raise ValueError(f"Book with ISBN '{isbn}' already exists.")
        finally:
            conn.close()

    def update_book(self, book_id: int, isbn: str, title: str, author: str, category: str, 
                    total_copies: int, publisher: str = "", publication_year: int = None):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        # Calculate difference in total copies to update available_copies safely
        cursor.execute("SELECT total_copies, available_copies FROM books WHERE book_id = ?;", (book_id,))
        current = cursor.fetchone()
        if not current:
            conn.close()
            raise ValueError("Book not found.")

        diff = total_copies - current['total_copies']
        new_available = current['available_copies'] + diff

        if new_available < 0:
            conn.close()
            raise ValueError("Cannot reduce total copies below currently borrowed copies count.")

        cursor.execute("""
            UPDATE books SET isbn = ?, title = ?, author = ?, category = ?, 
                             total_copies = ?, available_copies = ?, publisher = ?, publication_year = ?
            WHERE book_id = ?;
        """, (isbn, title, author, category, total_copies, new_available, publisher, publication_year, book_id))

        conn.commit()
        conn.close()
        return True

    def delete_book(self, book_id: int):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        # Check if active loans exist
        cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE book_id = ? AND status = 'issued';", (book_id,))
        if cursor.fetchone()['count'] > 0:
            conn.close()
            raise ValueError("Cannot delete book that is currently checked out by students.")

        cursor.execute("DELETE FROM books WHERE book_id = ?;", (book_id,))
        conn.commit()
        conn.close()
        return True

    # ==================== ISSUE & RETURN LOGIC ====================

    def issue_book(self, book_id: int, student_id: int, issued_by_id: int, custom_days: int = None):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        # 1. Verify student exists and is indeed a student
        cursor.execute("SELECT role FROM users WHERE user_id = ?;", (student_id,))
        student_row = cursor.fetchone()
        if not student_row or student_row['role'] != 'student':
            conn.close()
            raise ValueError("Invalid student ID specified.")

        # 2. Verify book availability
        cursor.execute("SELECT title, available_copies FROM books WHERE book_id = ?;", (book_id,))
        book_row = cursor.fetchone()
        if not book_row:
            conn.close()
            raise ValueError("Book not found.")
        if book_row['available_copies'] <= 0:
            conn.close()
            raise ValueError(f"'{book_row['title']}' has no available copies currently.")

        # 3. Check student active loan limit
        cursor.execute("SELECT value FROM settings WHERE key = 'max_books_per_student';")
        max_books = int(cursor.fetchone()['value'])

        cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE student_id = ? AND status = 'issued';", (student_id,))
        active_loans = cursor.fetchone()['count']
        if active_loans >= max_books:
            conn.close()
            raise ValueError(f"Student has already reached the maximum limit of {max_books} active borrowed books.")

        # 4. Check for existing active loan of the SAME book
        cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE student_id = ? AND book_id = ? AND status = 'issued';", (student_id, book_id))
        if cursor.fetchone()['count'] > 0:
            conn.close()
            raise ValueError("Student is already borrowing an active copy of this book.")

        # 5. Calculate due date
        if custom_days is None:
            cursor.execute("SELECT value FROM settings WHERE key = 'max_loan_days';")
            loan_days = int(cursor.fetchone()['value'])
        else:
            loan_days = int(custom_days)

        issue_date_str = date.today().isoformat()
        due_date_str = (date.today() + timedelta(days=loan_days)).isoformat()

        # Execute Transaction
        cursor.execute("""
            INSERT INTO transactions (book_id, student_id, issued_by_id, issue_date, due_date, status)
            VALUES (?, ?, ?, ?, ?, 'issued');
        """, (book_id, student_id, issued_by_id, issue_date_str, due_date_str))
        trans_id = cursor.lastrowid

        # Update available copies
        cursor.execute("UPDATE books SET available_copies = available_copies - 1 WHERE book_id = ?;", (book_id,))

        # Update any pending reservations for this book & student to 'fulfilled'
        cursor.execute("UPDATE reservations SET status = 'fulfilled' WHERE book_id = ? AND student_id = ? AND status = 'pending';", (book_id, student_id))

        conn.commit()
        conn.close()
        return trans_id

    def return_book(self, transaction_id: int):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        # 1. Fetch transaction record
        cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?;", (transaction_id,))
        trans = cursor.fetchone()
        if not trans:
            conn.close()
            raise ValueError("Transaction record not found.")

        if trans['status'] == 'returned':
            conn.close()
            raise ValueError("This book transaction has already been marked as returned.")

        return_date_obj = date.today()
        return_date_str = return_date_obj.isoformat()
        due_date_obj = datetime.strptime(trans['due_date'], "%Y-%m-%d").date()

        # 2. Check for overdue fine
        fine_amount = 0.0
        if return_date_obj > due_date_obj:
            overdue_days = (return_date_obj - due_date_obj).days
            cursor.execute("SELECT value FROM settings WHERE key = 'fine_per_day';")
            rate = float(cursor.fetchone()['value'])
            fine_amount = overdue_days * rate

            # Create Fine record
            cursor.execute("""
                INSERT INTO fines (transaction_id, student_id, amount, status)
                VALUES (?, ?, ?, 'unpaid');
            """, (transaction_id, trans['student_id'], fine_amount))

        # 3. Update Transaction & Increment Book Available Copies
        cursor.execute("""
            UPDATE transactions SET return_date = ?, status = 'returned'
            WHERE transaction_id = ?;
        """, (return_date_str, transaction_id))

        cursor.execute("UPDATE books SET available_copies = available_copies + 1 WHERE book_id = ?;", (trans['book_id'],))

        conn.commit()
        conn.close()
        return fine_amount

    def get_all_transactions(self, student_id: int = None, status_filter: str = None):
        """Retrieves list of transactions enriched with book and user names."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT t.*, b.title as book_title, u1.full_name as student_name, u2.full_name as issuer_name
            FROM transactions t
            JOIN books b ON t.book_id = b.book_id
            JOIN users u1 ON t.student_id = u1.user_id
            JOIN users u2 ON t.issued_by_id = u2.user_id
            WHERE 1=1
        """
        params = []

        if student_id:
            query += " AND t.student_id = ?"
            params.append(student_id)

        if status_filter:
            query += " AND t.status = ?"
            params.append(status_filter)

        query += " ORDER BY t.transaction_id DESC;"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        transactions = []
        today_str = date.today().isoformat()

        for r in rows:
            status = r['status']
            # Dynamically identify overdue loans if not yet returned
            if status == 'issued' and r['due_date'] < today_str:
                status = 'overdue'

            transactions.append(LoanTransaction(
                r['transaction_id'], r['book_id'], r['student_id'], r['issued_by_id'],
                r['issue_date'], r['due_date'], r['return_date'], status,
                book_title=r['book_title'], student_name=r['student_name'], issuer_name=r['issuer_name']
            ))
        return transactions

    # ==================== FINES MANAGEMENT ====================

    def get_all_fines(self, student_id: int = None, status_filter: str = None):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT f.*, u.full_name as student_name, b.title as book_title
            FROM fines f
            JOIN users u ON f.student_id = u.user_id
            JOIN transactions t ON f.transaction_id = t.transaction_id
            JOIN books b ON t.book_id = b.book_id
            WHERE 1=1
        """
        params = []

        if student_id:
            query += " AND f.student_id = ?"
            params.append(student_id)

        if status_filter:
            query += " AND f.status = ?"
            params.append(status_filter)

        query += " ORDER BY f.fine_id DESC;"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        fines = []
        for r in rows:
            fines.append(Fine(
                r['fine_id'], r['transaction_id'], r['student_id'], r['amount'],
                r['status'], r['created_at'], student_name=r['student_name'], book_title=r['book_title']
            ))
        return fines

    def pay_fine(self, fine_id: int):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT status FROM fines WHERE fine_id = ?;", (fine_id,))
        fine = cursor.fetchone()
        if not fine:
            conn.close()
            raise ValueError("Fine record not found.")

        if fine['status'] == 'paid':
            conn.close()
            raise ValueError("Fine is already marked as paid.")

        cursor.execute("UPDATE fines SET status = 'paid' WHERE fine_id = ?;", (fine_id,))
        conn.commit()
        conn.close()
        return True

    # ==================== RESERVATIONS ====================

    def reserve_book(self, book_id: int, student_id: int):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        # Check existing active reservation
        cursor.execute("SELECT COUNT(*) as count FROM reservations WHERE book_id = ? AND student_id = ? AND status = 'pending';", (book_id, student_id))
        if cursor.fetchone()['count'] > 0:
            conn.close()
            raise ValueError("You already have an active pending reservation for this book.")

        cursor.execute("INSERT INTO reservations (book_id, student_id, status) VALUES (?, ?, 'pending');", (book_id, student_id))
        res_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return res_id

    def get_all_reservations(self, student_id: int = None, status_filter: str = None):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT r.*, b.title as book_title, u.full_name as student_name
            FROM reservations r
            JOIN books b ON r.book_id = b.book_id
            JOIN users u ON r.student_id = u.user_id
            WHERE 1=1
        """
        params = []

        if student_id:
            query += " AND r.student_id = ?"
            params.append(student_id)

        if status_filter:
            query += " AND r.status = ?"
            params.append(status_filter)

        query += " ORDER BY r.reservation_id DESC;"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        reservations = []
        for r in rows:
            reservations.append(Reservation(
                r['reservation_id'], r['book_id'], r['student_id'],
                r['reserved_at'], r['status'], book_title=r['book_title'], student_name=r['student_name']
            ))
        return reservations

    def cancel_reservation(self, reservation_id: int):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE reservations SET status = 'cancelled' WHERE reservation_id = ?;", (reservation_id,))
        conn.commit()
        conn.close()
        return True

    # ==================== SYSTEM SETTINGS & ANALYTICS ====================

    def get_settings(self):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings;")
        rows = cursor.fetchall()
        conn.close()
        return {r['key']: r['value'] for r in rows}

    def update_settings(self, settings_dict: dict):
        conn = get_connection(self.db_path)
        cursor = conn.cursor()
        for k, v in settings_dict.items():
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?);", (k, str(v)))
        conn.commit()
        conn.close()
        return True

    def get_system_analytics(self):
        """Generates comprehensive system summary reports for Admin dashboard."""
        conn = get_connection(self.db_path)
        cursor = conn.cursor()

        analytics = {}

        # Users counts
        cursor.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role;")
        role_counts = {r['role']: r['count'] for r in cursor.fetchall()}
        analytics['total_users'] = sum(role_counts.values())
        analytics['admin_count'] = role_counts.get('admin', 0)
        analytics['librarian_count'] = role_counts.get('librarian', 0)
        analytics['student_count'] = role_counts.get('student', 0)

        # Books counts
        cursor.execute("SELECT COUNT(*) as titles, SUM(total_copies) as total_copies, SUM(available_copies) as avail_copies FROM books;")
        b_row = cursor.fetchone()
        analytics['book_titles'] = b_row['titles'] or 0
        analytics['total_copies'] = b_row['total_copies'] or 0
        analytics['available_copies'] = b_row['avail_copies'] or 0
        analytics['issued_copies'] = analytics['total_copies'] - analytics['available_copies']

        # Loans counts
        cursor.execute("SELECT status, COUNT(*) as count FROM transactions GROUP BY status;")
        t_counts = {r['status']: r['count'] for r in cursor.fetchall()}
        analytics['active_loans'] = t_counts.get('issued', 0)
        analytics['returned_loans'] = t_counts.get('returned', 0)

        # Overdue count
        today_str = date.today().isoformat()
        cursor.execute("SELECT COUNT(*) as count FROM transactions WHERE status = 'issued' AND due_date < ?;", (today_str,))
        analytics['overdue_loans'] = cursor.fetchone()['count']

        # Fines
        cursor.execute("SELECT status, SUM(amount) as sum_amt FROM fines GROUP BY status;")
        f_sums = {r['status']: r['sum_amt'] or 0.0 for r in cursor.fetchall()}
        analytics['unpaid_fines'] = f_sums.get('unpaid', 0.0)
        analytics['collected_fines'] = f_sums.get('paid', 0.0)

        # Reservations
        cursor.execute("SELECT COUNT(*) as count FROM reservations WHERE status = 'pending';")
        analytics['pending_reservations'] = cursor.fetchone()['count']

        conn.close()
        return analytics

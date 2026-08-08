import sqlite3
import hashlib
import os
from datetime import datetime, timedelta

DB_NAME = "library.db"

def get_connection(db_path=DB_NAME):
    """Establishes and returns a database connection with dictionary-like row access."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def hash_password(password: str) -> str:
    """Hashes password using SHA-256 for secure local authentication."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db(db_path=DB_NAME):
    """Initializes SQLite database tables if they do not exist."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Users Table (Admin, Librarian, Student)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'librarian', 'student')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Books Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            total_copies INTEGER NOT NULL DEFAULT 1,
            available_copies INTEGER NOT NULL DEFAULT 1,
            publisher TEXT,
            publication_year INTEGER
        );
    """)

    # Transactions (Book Loans) Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            issued_by_id INTEGER NOT NULL,
            issue_date DATE NOT NULL,
            due_date DATE NOT NULL,
            return_date DATE,
            status TEXT NOT NULL DEFAULT 'issued' CHECK(status IN ('issued', 'returned', 'overdue')),
            FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (issued_by_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
    """)

    # Fines Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fines (
            fine_id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'unpaid' CHECK(status IN ('unpaid', 'paid')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
    """)

    # Book Reservations Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'fulfilled', 'cancelled')),
            FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
    """)

    # System Settings Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)

    conn.commit()
    conn.close()

def seed_db(db_path=DB_NAME):
    """Populates database with default system settings, users, and books if empty."""
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Check if users already seeded
    cursor.execute("SELECT COUNT(*) as count FROM users;")
    if cursor.fetchone()['count'] == 0:
        # Default Users
        users = [
            ('admin', hash_password('admin123'), 'System Administrator', 'admin@library.org', 'admin'),
            ('librarian1', hash_password('lib123'), 'Sabin Shrestha', 'sabin.shrestha@library.org.np', 'librarian'),
            ('librarian2', hash_password('lib123'), 'Sabita Joshi', 'sabita.joshi@library.org.np', 'librarian'),
            ('student1', hash_password('student123'), 'Aarav Shrestha', 'aarav.shrestha@student.edu.np', 'student'),
            ('student2', hash_password('student123'), 'Bina Thapa', 'bina.thapa@student.edu.np', 'student'),
            ('student3', hash_password('student123'), 'Sujan Adhikari', 'sujan.adhikari@student.edu.np', 'student'),
        ]
        cursor.executemany("""
            INSERT INTO users (username, password_hash, full_name, email, role)
            VALUES (?, ?, ?, ?, ?);
        """, users)

    # Check if books already seeded
    cursor.execute("SELECT COUNT(*) as count FROM books;")
    if cursor.fetchone()['count'] == 0:
        books = [
            ('978-0132350884', 'Clean Code: A Handbook of Agile Software Craftsmanship', 'Robert C. Martin', 'Computer Science', 5, 5, 'Prentice Hall', 2008),
            ('978-0201616224', 'The Pragmatic Programmer', 'Andrew Hunt & David Thomas', 'Computer Science', 4, 4, 'Addison-Wesley', 1999),
            ('978-0596007126', 'Head First Design Patterns', 'Eric Freeman & Elisabeth Robson', 'Software Architecture', 3, 3, "O'Reilly Media", 2004),
            ('978-0134685991', 'Effective Java', 'Joshua Bloch', 'Programming', 4, 4, 'Addison-Wesley', 2017),
            ('978-0321125217', 'Domain-Driven Design', 'Eric Evans', 'Software Architecture', 2, 2, 'Addison-Wesley', 2003),
            ('978-0134494166', 'Artificial Intelligence: A Modern Approach', 'Stuart Russell & Peter Norvig', 'AI & Machine Learning', 3, 3, 'Pearson', 2020),
            ('978-1491957660', 'Designing Data-Intensive Applications', 'Martin Kleppmann', 'Database & Systems', 5, 5, "O'Reilly Media", 2017),
            ('978-0073523323', 'Database System Concepts', 'Abraham Silberschatz', 'Database', 3, 3, 'McGraw-Hill', 2019)
        ]
        cursor.executemany("""
            INSERT INTO books (isbn, title, author, category, total_copies, available_copies, publisher, publication_year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, books)

    # Default Settings
    default_settings = [
        ('max_loan_days', '14'),
        ('fine_per_day', '1.50'),
        ('max_books_per_student', '3')
    ]
    for key, val in default_settings:
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);", (key, val))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    seed_db()
    print("Database initialized and seeded successfully.")

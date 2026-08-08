import unittest
import os
import sqlite3
from datetime import date, timedelta
from database import init_db, seed_db, get_connection
from models import Admin, Librarian, Student
from services import LibraryService

TEST_DB = "test_library.db"

class TestLibrarySystem(unittest.TestCase):

    def setUp(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        seed_db(TEST_DB)
        self.service = LibraryService(TEST_DB)

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_01_authentication_and_roles(self):
        admin = self.service.authenticate('admin', 'admin123')
        self.assertIsNotNone(admin)
        self.assertIsInstance(admin, Admin)
        self.assertEqual(admin.role, 'admin')

        lib = self.service.authenticate('librarian1', 'lib123')
        self.assertIsNotNone(lib)
        self.assertIsInstance(lib, Librarian)

        student = self.service.authenticate('student1', 'student123')
        self.assertIsNotNone(student)
        self.assertIsInstance(student, Student)

        invalid = self.service.authenticate('admin', 'wrongpass')
        self.assertIsNone(invalid)

    def test_02_user_management(self):
        uid = self.service.create_user('newstudent', 'pass123', 'New Student', 'new@edu.com', 'student')
        self.assertIsNotNone(uid)
        
        users = self.service.get_all_users()
        self.assertTrue(any(u.username == 'newstudent' for u in users))

        # Test duplicate username rejection
        with self.assertRaises(ValueError):
            self.service.create_user('newstudent', 'pass123', 'Dup Student', 'dup@edu.com', 'student')

    def test_03_book_management(self):
        book_id = self.service.add_book('978-0000000000', 'Test Driven Development', 'Kent Beck', 'Computer Science', 3)
        self.assertIsNotNone(book_id)

        book = self.service.get_book_by_id(book_id)
        self.assertEqual(book.title, 'Test Driven Development')
        self.assertEqual(book.available_copies, 3)

        # Search book
        search_results = self.service.get_all_books(search_query='Kent Beck')
        self.assertEqual(len(search_results), 1)

    def test_04_issue_and_return_book(self):
        student = self.service.authenticate('student1', 'student123')
        lib = self.service.authenticate('librarian1', 'lib123')
        books = self.service.get_all_books()
        target_book = books[0]

        # Issue book
        tid = self.service.issue_book(target_book.book_id, student.user_id, lib.user_id)
        self.assertIsNotNone(tid)

        # Check copies decreased
        updated_book = self.service.get_book_by_id(target_book.book_id)
        self.assertEqual(updated_book.available_copies, target_book.available_copies - 1)

        # Return book on time
        fine = self.service.return_book(tid)
        self.assertEqual(fine, 0.0)

        # Check copies restored
        restored_book = self.service.get_book_by_id(target_book.book_id)
        self.assertEqual(restored_book.available_copies, target_book.total_copies)

    def test_05_overdue_fine_calculation(self):
        student = self.service.authenticate('student2', 'student123')
        lib = self.service.authenticate('librarian1', 'lib123')
        books = self.service.get_all_books()
        target_book = books[1]

        # Manually create an overdue transaction in DB (5 days overdue)
        conn = get_connection(TEST_DB)
        cursor = conn.cursor()
        issue_date = (date.today() - timedelta(days=20)).isoformat()
        due_date = (date.today() - timedelta(days=5)).isoformat()

        cursor.execute("""
            INSERT INTO transactions (book_id, student_id, issued_by_id, issue_date, due_date, status)
            VALUES (?, ?, ?, ?, ?, 'issued');
        """, (target_book.book_id, student.user_id, lib.user_id, issue_date, due_date))
        tid = cursor.lastrowid
        cursor.execute("UPDATE books SET available_copies = available_copies - 1 WHERE book_id = ?;", (target_book.book_id,))
        conn.commit()
        conn.close()

        # Process Return (5 days overdue @ $1.50/day = $7.50)
        fine_amount = self.service.return_book(tid)
        self.assertEqual(fine_amount, 7.50)

        fines = self.service.get_all_fines(student_id=student.user_id)
        self.assertEqual(len(fines), 1)
        self.assertEqual(fines[0].amount, 7.50)
        self.assertEqual(fines[0].status, 'unpaid')

        # Pay Fine
        paid = self.service.pay_fine(fines[0].fine_id)
        self.assertTrue(paid)

        updated_fines = self.service.get_all_fines(student_id=student.user_id)
        self.assertEqual(updated_fines[0].status, 'paid')

    def test_06_reservations(self):
        student = self.service.authenticate('student3', 'student123')
        books = self.service.get_all_books()
        book_id = books[0].book_id

        res_id = self.service.reserve_book(book_id, student.user_id)
        self.assertIsNotNone(res_id)

        res_list = self.service.get_all_reservations(student_id=student.user_id)
        self.assertEqual(len(res_list), 1)
        self.assertEqual(res_list[0].status, 'pending')

    def test_07_admin_analytics(self):
        stats = self.service.get_system_analytics()
        self.assertIn('total_users', stats)
        self.assertIn('book_titles', stats)
        self.assertIn('active_loans', stats)
        self.assertIn('collected_fines', stats)

if __name__ == '__main__':
    unittest.main()

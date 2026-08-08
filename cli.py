import sys
import getpass
from database import seed_db
from services import LibraryService

class LibraryCLI:
    def __init__(self):
        seed_db()
        self.service = LibraryService()
        self.current_user = None

    def print_header(self, title):
        print("\n" + "=" * 60)
        print(f"   {title.upper()}")
        print("=" * 60)

    def start(self):
        while True:
            self.print_header("Library Management System")
            print("1. Login")
            print("2. Browse Book Catalog (Guest)")
            print("3. Exit")
            choice = input("\nSelect an option (1-3): ").strip()

            if choice == '1':
                self.login_menu()
            elif choice == '2':
                self.view_catalog_guest()
            elif choice == '3':
                print("\nThank you for using Library Management System. Goodbye!")
                sys.exit(0)
            else:
                print("Invalid selection. Please try again.")

    def login_menu(self):
        self.print_header("User Login")
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ") if sys.stdin.isatty() else input("Password: ").strip()

        user = self.service.authenticate(username, password)
        if not user:
            print("\n[ERROR] Invalid username or password.")
            return

        self.current_user = user
        print(f"\n[SUCCESS] Welcome back, {user.full_name}! Role: {user.role.upper()}")

        if user.role == 'admin':
            self.admin_menu()
        elif user.role == 'librarian':
            self.librarian_menu()
        elif user.role == 'student':
            self.student_menu()

    def view_catalog_guest(self):
        self.print_header("Book Catalog")
        search = input("Enter search term (title, author, ISBN, category) or Press Enter for all: ").strip()
        books = self.service.get_all_books(search_query=search if search else None)
        self.display_books_table(books)

    def display_books_table(self, books):
        if not books:
            print("\nNo books found matching criteria.")
            return

        print("\n" + "-" * 95)
        print(f"{'ID':<4} | {'ISBN':<15} | {'Title':<30} | {'Author':<20} | {'Category':<15} | {'Avail/Total'}")
        print("-" * 95)
        for b in books:
            title = (b.title[:27] + '...') if len(b.title) > 30 else b.title
            author = (b.author[:17] + '...') if len(b.author) > 20 else b.author
            category = (b.category[:13] + '...') if len(b.category) > 15 else b.category
            print(f"{b.book_id:<4} | {b.isbn:<15} | {title:<30} | {author:<20} | {category:<15} | {b.available_copies}/{b.total_copies}")
        print("-" * 95)

    # ==================== ADMIN MENU ====================
    def admin_menu(self):
        while True:
            self.print_header(f"Admin Dashboard - Logged in as {self.current_user.full_name}")
            print("1. View System Analytics & Reports")
            print("2. Manage Users (Create / View / Delete)")
            print("3. Manage System Settings (Loan days, Fine rate)")
            print("4. View All Book Loans")
            print("5. View All Fines")
            print("6. Logout")

            choice = input("\nSelect option (1-6): ").strip()
            if choice == '1':
                self.show_admin_analytics()
            elif choice == '2':
                self.admin_manage_users()
            elif choice == '3':
                self.admin_manage_settings()
            elif choice == '4':
                self.view_all_transactions()
            elif choice == '5':
                self.view_all_fines()
            elif choice == '6':
                self.current_user = None
                print("\nLogged out successfully.")
                break

    def show_admin_analytics(self):
        self.print_header("System Analytics Report")
        stats = self.service.get_system_analytics()
        print(f" Total Registered Users  : {stats['total_users']} (Admins: {stats['admin_count']}, Librarians: {stats['librarian_count']}, Students: {stats['student_count']})")
        print(f" Unique Book Titles     : {stats['book_titles']}")
        print(f" Total Physical Copies   : {stats['total_copies']}")
        print(f" Currently Issued Copies : {stats['issued_copies']}")
        print(f" Available Copies        : {stats['available_copies']}")
        print(f" Active Book Loans       : {stats['active_loans']}")
        print(f" Overdue Loans           : {stats['overdue_loans']}")
        print(f" Outstanding Unpaid Fines: ${stats['unpaid_fines']:.2f}")
        print(f" Total Collected Fines   : ${stats['collected_fines']:.2f}")
        print(f" Pending Book Holds      : {stats['pending_reservations']}")

    def admin_manage_users(self):
        self.print_header("Admin - User Management")
        print("1. View All Users")
        print("2. Create New User (Admin/Librarian/Student)")
        print("3. Delete User")
        print("4. Back")

        c = input("\nOption (1-4): ").strip()
        if c == '1':
            users = self.service.get_all_users()
            print("\n" + "-" * 75)
            print(f"{'ID':<4} | {'Username':<15} | {'Full Name':<22} | {'Role':<10} | {'Email'}")
            print("-" * 75)
            for u in users:
                print(f"{u.user_id:<4} | {u.username:<15} | {u.full_name:<22} | {u.role:<10} | {u.email}")
            print("-" * 75)
        elif c == '2':
            username = input("Username: ").strip()
            password = input("Password: ").strip()
            full_name = input("Full Name: ").strip()
            email = input("Email: ").strip()
            role = input("Role (admin/librarian/student): ").strip().lower()
            try:
                uid = self.service.create_user(username, password, full_name, email, role)
                print(f"\n[SUCCESS] User created successfully with ID: {uid}")
            except Exception as e:
                print(f"\n[ERROR] {e}")
        elif c == '3':
            uid = input("Enter User ID to delete: ").strip()
            try:
                self.service.delete_user(int(uid))
                print("\n[SUCCESS] User deleted successfully.")
            except Exception as e:
                print(f"\n[ERROR] {e}")

    def admin_manage_settings(self):
        self.print_header("Admin - System Settings")
        settings = self.service.get_settings()
        print(f"Current Max Loan Days       : {settings.get('max_loan_days')}")
        print(f"Current Daily Fine Rate     : ${settings.get('fine_per_day')}")
        print(f"Current Max Books/Student   : {settings.get('max_books_per_student')}")

        update = input("\nDo you want to update settings? (y/n): ").strip().lower()
        if update == 'y':
            loan_days = input(f"New Max Loan Days (Current: {settings.get('max_loan_days')}): ").strip()
            fine_rate = input(f"New Daily Fine Rate (Current: ${settings.get('fine_per_day')}): ").strip()
            max_books = input(f"New Max Books/Student (Current: {settings.get('max_books_per_student')}): ").strip()

            new_settings = {}
            if loan_days: new_settings['max_loan_days'] = loan_days
            if fine_rate: new_settings['fine_per_day'] = fine_rate
            if max_books: new_settings['max_books_per_student'] = max_books

            if new_settings:
                self.service.update_settings(new_settings)
                print("\n[SUCCESS] Settings updated successfully!")

    # ==================== LIBRARIAN MENU ====================
    def librarian_menu(self):
        while True:
            self.print_header(f"Librarian Dashboard - Logged in as {self.current_user.full_name}")
            print("1. Search & Browse Book Catalog")
            print("2. Add New Book to Catalog")
            print("3. Issue Book to Student")
            print("4. Process Book Return & Assess Fine")
            print("5. Manage Fines (Mark Paid)")
            print("6. View Book Reservations")
            print("7. Logout")

            choice = input("\nSelect option (1-7): ").strip()
            if choice == '1':
                self.view_catalog_guest()
            elif choice == '2':
                self.librarian_add_book()
            elif choice == '3':
                self.librarian_issue_book()
            elif choice == '4':
                self.librarian_return_book()
            elif choice == '5':
                self.view_all_fines(manage=True)
            elif choice == '6':
                self.view_all_reservations()
            elif choice == '7':
                self.current_user = None
                print("\nLogged out successfully.")
                break

    def librarian_add_book(self):
        self.print_header("Librarian - Add New Book")
        isbn = input("ISBN: ").strip()
        title = input("Title: ").strip()
        author = input("Author: ").strip()
        category = input("Category: ").strip()
        copies = int(input("Total Copies: ").strip() or "1")
        publisher = input("Publisher (Optional): ").strip()
        pub_year = input("Publication Year (Optional): ").strip()

        try:
            bid = self.service.add_book(isbn, title, author, category, copies, publisher, int(pub_year) if pub_year else None)
            print(f"\n[SUCCESS] Book '{title}' added with ID: {bid}")
        except Exception as e:
            print(f"\n[ERROR] {e}")

    def librarian_issue_book(self):
        self.print_header("Librarian - Issue Book to Student")
        student_id = input("Enter Student ID: ").strip()
        book_id = input("Enter Book ID: ").strip()

        try:
            tid = self.service.issue_book(int(book_id), int(student_id), self.current_user.user_id)
            print(f"\n[SUCCESS] Book issued successfully! Transaction ID: {tid}")
        except Exception as e:
            print(f"\n[ERROR] {e}")

    def librarian_return_book(self):
        self.print_header("Librarian - Process Book Return")
        tid = input("Enter Transaction ID to return: ").strip()
        try:
            fine = self.service.return_book(int(tid))
            print(f"\n[SUCCESS] Book returned successfully!")
            if fine > 0:
                print(f"[NOTICE] An overdue fine of ${fine:.2f} was automatically assessed for this student.")
        except Exception as e:
            print(f"\n[ERROR] {e}")

    # ==================== STUDENT MENU ====================
    def student_menu(self):
        while True:
            self.print_header(f"Student Dashboard - Welcome {self.current_user.full_name}")
            print("1. Browse Catalog & Search Books")
            print("2. View My Borrowed Books & Due Dates")
            print("3. Reserve a Book")
            print("4. View My Fines & Balance")
            print("5. Logout")

            choice = input("\nSelect option (1-5): ").strip()
            if choice == '1':
                self.view_catalog_guest()
            elif choice == '2':
                self.student_my_loans()
            elif choice == '3':
                self.student_reserve_book()
            elif choice == '4':
                self.student_my_fines()
            elif choice == '5':
                self.current_user = None
                print("\nLogged out successfully.")
                break

    def student_my_loans(self):
        self.print_header("My Borrowed Books")
        loans = self.service.get_all_transactions(student_id=self.current_user.user_id)
        if not loans:
            print("\nYou currently have no active or past borrowed books.")
            return

        print("\n" + "-" * 85)
        print(f"{'T-ID':<5} | {'Book Title':<32} | {'Issue Date':<12} | {'Due Date':<12} | {'Status'}")
        print("-" * 85)
        for l in loans:
            title = (l.book_title[:29] + '...') if len(l.book_title) > 32 else l.book_title
            print(f"{l.transaction_id:<5} | {title:<32} | {l.issue_date:<12} | {l.due_date:<12} | {l.status.upper()}")
        print("-" * 85)

    def student_reserve_book(self):
        self.print_header("Reserve a Book")
        book_id = input("Enter Book ID to reserve: ").strip()
        try:
            rid = self.service.reserve_book(int(book_id), self.current_user.user_id)
            print(f"\n[SUCCESS] Reservation hold placed! Reservation ID: {rid}")
        except Exception as e:
            print(f"\n[ERROR] {e}")

    def student_my_fines(self):
        self.print_header("My Fines & Fees")
        fines = self.service.get_all_fines(student_id=self.current_user.user_id)
        if not fines:
            print("\nYou have no fines on record. Clean record!")
            return

        print("\n" + "-" * 70)
        print(f"{'Fine ID':<8} | {'Book Title':<28} | {'Amount':<10} | {'Status'}")
        print("-" * 70)
        total_unpaid = 0.0
        for f in fines:
            title = (f.book_title[:25] + '...') if len(f.book_title) > 28 else f.book_title
            print(f"{f.fine_id:<8} | {title:<28} | ${f.amount:<9.2f} | {f.status.upper()}")
            if f.status == 'unpaid':
                total_unpaid += f.amount
        print("-" * 70)
        print(f" Total Outstanding Balance: ${total_unpaid:.2f}")

    # ==================== HELPERS ====================
    def view_all_transactions(self):
        self.print_header("All System Book Loans")
        loans = self.service.get_all_transactions()
        if not loans:
            print("No loan transactions found.")
            return

        print("\n" + "-" * 95)
        print(f"{'T-ID':<5} | {'Student':<18} | {'Book Title':<28} | {'Issued':<10} | {'Due':<10} | {'Status'}")
        print("-" * 95)
        for l in loans:
            st = (l.student_name[:16] + '..') if len(l.student_name) > 18 else l.student_name
            bt = (l.book_title[:26] + '..') if len(l.book_title) > 28 else l.book_title
            print(f"{l.transaction_id:<5} | {st:<18} | {bt:<28} | {l.issue_date:<10} | {l.due_date:<10} | {l.status.upper()}")
        print("-" * 95)

    def view_all_fines(self, manage=False):
        self.print_header("System Fines")
        fines = self.service.get_all_fines()
        if not fines:
            print("No fine records found.")
            return

        print("\n" + "-" * 80)
        print(f"{'Fine ID':<8} | {'Student':<20} | {'Book Title':<25} | {'Amount':<10} | {'Status'}")
        print("-" * 80)
        for f in fines:
            st = (f.student_name[:18] + '..') if len(f.student_name) > 20 else f.student_name
            bt = (f.book_title[:23] + '..') if len(f.book_title) > 25 else f.book_title
            print(f"{f.fine_id:<8} | {st:<20} | {bt:<25} | ${f.amount:<9.2f} | {f.status.upper()}")
        print("-" * 80)

        if manage:
            fid = input("\nEnter Fine ID to mark as Paid (or Press Enter to cancel): ").strip()
            if fid:
                try:
                    self.service.pay_fine(int(fid))
                    print("\n[SUCCESS] Fine marked as Paid.")
                except Exception as e:
                    print(f"\n[ERROR] {e}")

    def view_all_reservations(self):
        self.print_header("Book Reservations / Holds")
        res = self.service.get_all_reservations()
        if not res:
            print("No book reservations found.")
            return

        print("\n" + "-" * 75)
        print(f"{'Res ID':<7} | {'Student':<20} | {'Book Title':<28} | {'Status'}")
        print("-" * 75)
        for r in res:
            st = (r.student_name[:18] + '..') if len(r.student_name) > 20 else r.student_name
            bt = (r.book_title[:26] + '..') if len(r.book_title) > 28 else r.book_title
            print(f"{r.reservation_id:<7} | {st:<20} | {bt:<28} | {r.status.upper()}")
        print("-" * 75)

if __name__ == '__main__':
    cli = LibraryCLI()
    cli.start()

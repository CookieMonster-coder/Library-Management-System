"""
Library Management System - Main Entry Point (Pure Python CLI)
Run this file using standard Python: python main.py
"""
import sys
from cli import LibraryCLI

def main():
    try:
        app = LibraryCLI()
        app.start()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted. Goodbye!")
        sys.exit(0)

if __name__ == "__main__":
    main()

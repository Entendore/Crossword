import sys
from PySide6.QtWidgets import QApplication
from crossword_app import CrosswordApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CrosswordApp()
    window.show()
    sys.exit(app.exec())
from PySide6.QtWidgets import QLineEdit, QLabel
from PySide6.QtCore import Signal, Qt, QRegularExpression, QRect
from PySide6.QtGui import QFont, QRegularExpressionValidator, QPainter, QColor


class CrosswordCell(QLineEdit):
    clicked = Signal(int, int)

    def __init__(self, row, col):
        super().__init__()
        self.row = row
        self.col = col
        self.setMaxLength(1)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.is_blocked = False
        self.correct_letter = None
        self.cell_number = None  # For numbering cells
        
        # Only allow letters
        self.setValidator(QRegularExpressionValidator(QRegularExpression("[A-Za-z]")))
        self.base_style = """
            QLineEdit {
                border: 2px solid #333;
                background-color: white;
                padding: 0px;
                margin: 0px;
            }
        """
        self.setStyleSheet(self.base_style)

    def mousePressEvent(self, event):
        self.clicked.emit(self.row, self.col)
        super().mousePressEvent(event)

    def set_blocked(self, blocked=True):
        self.is_blocked = blocked
        self.setReadOnly(blocked)
        self.setText("")
        if blocked:
            self.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #333;
                    background-color: #2c2c2c;
                    padding: 0px;
                    margin: 0px;
                }
            """)
        else:
            self.setStyleSheet(self.base_style)

    def mark_correct(self):
        if not self.is_blocked:
            self.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #333;
                    background-color: #90EE90;
                    padding: 0px;
                    margin: 0px;
                }
            """)

    def mark_incorrect(self):
        if not self.is_blocked:
            self.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #333;
                    background-color: #FFB3B3;
                    padding: 0px;
                    margin: 0px;
                }
            """)

    def reset_color(self):
        if not self.is_blocked:
            self.setStyleSheet(self.base_style)

    def highlight_across(self):
        if not self.is_blocked:
            self.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #333;
                    background-color: #87CEEB;
                    padding: 0px;
                    margin: 0px;
                }
            """)

    def highlight_down(self):
        if not self.is_blocked:
            self.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #333;
                    background-color: #DDA0DD;
                    padding: 0px;
                    margin: 0px;
                }
            """)

    def highlight_both(self):
        if not self.is_blocked:
            self.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #333;
                    background-color: #98FB98;
                    padding: 0px;
                    margin: 0px;
                }
            """)

    def set_cell_number(self, number):
        self.cell_number = number

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.cell_number is not None and not self.is_blocked:
            painter = QPainter(self)
            painter.setPen(QColor("#000080"))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.drawText(QRect(2, 1, 20, 15), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, str(self.cell_number))
            painter.end()
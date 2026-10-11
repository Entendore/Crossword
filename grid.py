from PySide6.QtWidgets import QWidget, QGridLayout
from cell import CrosswordCell


class CrosswordGrid(QWidget):
    def __init__(self, rows=10, cols=10):
        super().__init__()
        self.rows = rows
        self.cols = cols
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(0)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.cells = []
        self._build_grid()

    def _build_grid(self):
        # Clear existing widgets if resizing
        if self.cells:
            for r in range(len(self.cells)):
                for c in range(len(self.cells[r])):
                    self.cells[r][c].deleteLater()

        self.cells = [[CrosswordCell(r, c) for c in range(self.cols)] for r in range(self.rows)]
        for r in range(self.rows):
            for c in range(self.cols):
                self.grid_layout.addWidget(self.cells[r][c], r, c)
        
        if not self.layout():
            self.setLayout(self.grid_layout)

    def resize_grid(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self._build_grid()

    def clear_grid(self):
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.cells[r][c]
                cell.setText("")
                cell.set_blocked(False)
                cell.correct_letter = None
                cell.cell_number = None
                cell.setStyleSheet(cell.base_style)

    def block_empty_cells(self):
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.cells[r][c]
                if cell.text() == "":
                    cell.set_blocked(True)

    def check_answers(self):
        for r in range(self.rows):
            for c in range(self.cols):
                cell = self.cells[r][c]
                if cell.is_blocked or cell.correct_letter is None:
                    continue
                if cell.text().upper() == cell.correct_letter.upper():
                    cell.mark_correct()
                else:
                    cell.mark_incorrect()
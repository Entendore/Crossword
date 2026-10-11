import logging
from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import Qt, QSizeF
from PySide6.QtGui import QPainter, QPen, QColor, QPixmap, QPdfWriter, QFont


class ExportHandler:
    def __init__(self, grid_widget, clue_list, word_numbers):
        self.grid = grid_widget
        self.clue_list = clue_list
        self.word_numbers = word_numbers

    def export_text(self, parent):
        path, _ = QFileDialog.getSaveFileName(parent, "Export Crossword", "", "Text Files (*.txt)")
        if path:
            try:
                with open(path, "w") as f:
                    f.write("CROSSWORD PUZZLE\n")
                    f.write("=" * 40 + "\n\n")
                    
                    for r in range(self.grid.rows):
                        line = ""
                        for c in range(self.grid.cols):
                            cell = self.grid.cells[r][c]
                            if cell.is_blocked:
                                line += "## "
                            else:
                                line += f"{cell.text().upper() if cell.text() else '_ '} "
                        f.write(line + "\n")
                    
                    f.write("\n" + "=" * 40 + "\n")
                    f.write("CLUES\n")
                    f.write("=" * 40 + "\n\n")
                    
                    for idx in range(self.clue_list.count()):
                        clue_text = self.clue_list.item(idx).text()
                        if clue_text and not clue_text.startswith("─"):
                            f.write(clue_text + "\n")
                logging.info(f"Crossword exported as Text to {path}")
            except Exception as e:
                logging.error(f"Failed to export text: {str(e)}")

    def export_image(self, parent):
        path, _ = QFileDialog.getSaveFileName(parent, "Export Crossword Image", "", "PNG Files (*.png)")
        if not path:
            return

        try:
            cell_size = 50
            margin = 20
            width = margin * 2 + self.grid.cols * cell_size
            height = margin * 2 + self.grid.rows * cell_size
            pixmap = QPixmap(width, height)
            pixmap.fill(QColor("white"))
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            painter.setPen(QColor("black"))
            painter.drawText(margin, margin - 5, "CROSSWORD PUZZLE")

            for r in range(self.grid.rows):
                for c in range(self.grid.cols):
                    x = margin + c * cell_size
                    y = margin + r * cell_size
                    
                    cell = self.grid.cells[r][c]
                    if cell.is_blocked:
                        painter.fillRect(x, y, cell_size, cell_size, QColor("#2c2c2c"))
                    else:
                        painter.fillRect(x, y, cell_size, cell_size, QColor("white"))
                    
                    painter.setPen(QPen(QColor("black"), 2))
                    painter.drawRect(x, y, cell_size, cell_size)
                    
                    if not cell.is_blocked and cell.text():
                        painter.setFont(QFont("Arial", 20, QFont.Weight.Bold))
                        painter.setPen(QColor("black"))
                        painter.drawText(x, y, cell_size, cell_size, 
                                       Qt.AlignmentFlag.AlignCenter, cell.text().upper())

            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.setPen(QColor("#000080"))
            for (r, c), num in self.word_numbers.items():
                x = margin + c * cell_size
                y = margin + r * cell_size
                painter.drawText(x + 3, y + 14, str(num))

            painter.end()
            pixmap.save(path)
            logging.info(f"Crossword exported as Image to {path}")
        except Exception as e:
            logging.error(f"Failed to export image: {str(e)}")

    def export_pdf(self, parent):
        path, _ = QFileDialog.getSaveFileName(parent, "Export Crossword as PDF", "", "PDF Files (*.pdf)")
        if not path:
            return

        try:
            pdf_writer = QPdfWriter(path)
            pdf_writer.setPageSizeMM(QSizeF(210, 297))
            painter = QPainter(pdf_writer)
            
            cell_size = 12
            margin = 15
            
            painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            painter.setPen(QColor("black"))
            painter.drawText(margin, margin, "CROSSWORD PUZZLE")

            grid_top = margin + 15

            for r in range(self.grid.rows):
                for c in range(self.grid.cols):
                    x = margin + c * cell_size
                    y = grid_top + r * cell_size
                    
                    cell = self.grid.cells[r][c]
                    if cell.is_blocked:
                        painter.fillRect(x, y, cell_size, cell_size, QColor("#2c2c2c"))
                    else:
                        painter.fillRect(x, y, cell_size, cell_size, QColor("white"))
                    
                    painter.setPen(QPen(QColor("black"), 1))
                    painter.drawRect(x, y, cell_size, cell_size)
                    
                    if not cell.is_blocked and cell.text():
                        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                        painter.setPen(QColor("black"))
                        painter.drawText(x, y, cell_size, cell_size, 
                                       Qt.AlignmentFlag.AlignCenter, cell.text().upper())

            painter.setFont(QFont("Arial", 5, QFont.Weight.Bold))
            painter.setPen(QColor("#000080"))
            for (r, c), num in self.word_numbers.items():
                x = margin + c * cell_size
                y = grid_top + r * cell_size
                painter.drawText(x + 1, y + 6, str(num))

            painter.setPen(QColor("black"))
            y_offset = grid_top + self.grid.rows * cell_size + 15
            
            col_width = 90
            left_col = margin
            right_col = margin + col_width + 10
            
            current_left_y = y_offset
            current_right_y = y_offset
            in_down_section = False
            
            for idx in range(self.clue_list.count()):
                clue_text = self.clue_list.item(idx).text()
                if not clue_text:
                    continue
                    
                if clue_text.startswith("── ACROSS"):
                    painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                    painter.drawText(left_col, current_left_y, clue_text)
                    current_left_y += 12
                elif clue_text.startswith("── DOWN"):
                    in_down_section = True
                    painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                    painter.drawText(right_col, current_right_y, clue_text)
                    current_right_y += 12
                elif in_down_section:
                    painter.setFont(QFont("Arial", 8))
                    lines = self._wrap_text(clue_text, 45)
                    for line in lines:
                        painter.drawText(right_col, current_right_y, line)
                        current_right_y += 10
                else:
                    painter.setFont(QFont("Arial", 8))
                    lines = self._wrap_text(clue_text, 45)
                    for line in lines:
                        painter.drawText(left_col, current_left_y, line)
                        current_left_y += 10

            painter.end()
            logging.info(f"Crossword exported as PDF to {path}")
        except Exception as e:
            logging.error(f"Failed to export PDF: {str(e)}")
    
    def _wrap_text(self, text, max_chars):
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_chars:
                current_line = (current_line + " " + word).strip()
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [text]
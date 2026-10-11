import sys
import math
import json
import logging
from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QPushButton, 
                                 QListWidget, QLabel, QFileDialog,
                                 QSpinBox, QGroupBox, QFrame, QCheckBox)
from PySide6.QtCore import Qt
from grid import CrosswordGrid
from word_manager import WordManager
from export_handler import ExportHandler
from crossword_model import CrosswordSolver

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')

class CrosswordApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crossword Generator")
        self.resize(1300, 800)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)
        self.setLayout(main_layout)

        # Left panel
        left_panel = QVBoxLayout()
        word_group = QGroupBox("Word Manager")
        word_layout = QVBoxLayout()
        self.word_manager = WordManager()
        word_layout.addWidget(self.word_manager)
        word_group.setLayout(word_layout)
        left_panel.addWidget(word_group)
        
        size_group = QGroupBox("Settings")
        size_layout = QVBoxLayout()
        self.auto_size_cb = QCheckBox("Auto-size grid")
        self.auto_size_cb.setChecked(True)
        self.auto_size_cb.stateChanged.connect(self._toggle_size_controls)
        size_layout.addWidget(self.auto_size_cb)
        
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Rows:"))
        self.rows_spin = QSpinBox(); self.rows_spin.setRange(5, 50); self.rows_spin.setValue(15)
        manual_layout.addWidget(self.rows_spin)
        manual_layout.addWidget(QLabel("Cols:"))
        self.cols_spin = QSpinBox(); self.cols_spin.setRange(5, 50); self.cols_spin.setValue(15)
        manual_layout.addWidget(self.cols_spin)
        size_layout.addLayout(manual_layout)
        
        mcts_layout = QHBoxLayout()
        mcts_layout.addWidget(QLabel("MCTS Sims:"))
        self.mcts_spin = QSpinBox(); self.mcts_spin.setRange(0, 50); self.mcts_spin.setValue(8)
        mcts_layout.addWidget(self.mcts_spin)
        size_layout.addLayout(mcts_layout)
        
        self.size_info_label = QLabel("Grid will auto-adjust")
        self.size_info_label.setStyleSheet("color: gray; font-style: italic;")
        size_layout.addWidget(self.size_info_label)
        
        size_group.setLayout(size_layout)
        left_panel.addWidget(size_group)
        
        self.apply_size_btn = QPushButton("Apply Manual Size")
        self.apply_size_btn.clicked.connect(self.apply_grid_size)
        left_panel.addWidget(self.apply_size_btn)
        left_panel.addStretch()
        main_layout.addLayout(left_panel, 1)

        # Center panel
        center_panel = QVBoxLayout()
        self.grid_widget = CrosswordGrid(15, 15)
        grid_frame = QFrame(); grid_frame.setFrameStyle(QFrame.Shape.Box)
        grid_frame_layout = QVBoxLayout(); grid_frame_layout.setContentsMargins(5, 5, 5, 5)
        grid_frame_layout.addWidget(self.grid_widget); grid_frame.setLayout(grid_frame_layout)
        center_panel.addWidget(grid_frame, 1)
        
        legend_layout = QHBoxLayout()
        for text, color in [("Across", "#87CEEB"), ("Down", "#DDA0DD"), ("Both", "#98FB98")]:
            lbl = QLabel(f"  {text}  "); lbl.setStyleSheet(f"background-color: {color}; border: 1px solid #333;")
            legend_layout.addWidget(lbl)
        legend_layout.addStretch()
        center_panel.addLayout(legend_layout)
        main_layout.addLayout(center_panel, 3)

        # Right panel
        right_panel = QVBoxLayout()
        
        control_group = QGroupBox("Controls")
        control_layout = QVBoxLayout()
        self.generate_btn = QPushButton("🔄 Generate Crossword")
        self.generate_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 8px; background-color: #4CAF50; color: white; }")
        self.check_btn = QPushButton("✓ Check Answers")
        self.clear_btn = QPushButton("🗑 Clear Grid")
        self.solve_btn = QPushButton("💡 Auto Solve")
        control_layout.addWidget(self.generate_btn); control_layout.addWidget(self.check_btn)
        control_layout.addWidget(self.clear_btn); control_layout.addWidget(self.solve_btn)
        control_group.setLayout(control_layout)
        right_panel.addWidget(control_group)

        export_group = QGroupBox("Export / Save")
        export_layout = QVBoxLayout()
        self.export_btn = QPushButton("📄 Export Text")
        self.export_img_btn = QPushButton("🖼 Export Image")
        self.export_pdf_btn = QPushButton("📑 Export PDF")
        self.save_crossword_btn = QPushButton("💾 Save Crossword")
        self.load_crossword_btn = QPushButton("📂 Load Crossword")
        
        for btn in [self.export_btn, self.export_img_btn, self.export_pdf_btn, self.save_crossword_btn, self.load_crossword_btn]:
            export_layout.addWidget(btn)
        export_group.setLayout(export_layout)
        right_panel.addWidget(export_group)

        clue_group = QGroupBox("Clues")
        clue_layout = QVBoxLayout()
        self.clue_list = QListWidget()
        clue_layout.addWidget(self.clue_list)
        clue_group.setLayout(clue_layout)
        right_panel.addWidget(clue_group, 1)
        main_layout.addLayout(right_panel, 1)

        # STATE - Notice we removed self.clues!
        self.word_numbers = {}
        self.placed_words_data = []
        self._highlight_connected = False
        self.export_handler = ExportHandler(self.grid_widget, self.clue_list, self.word_numbers)

        # SIGNALS
        self.generate_btn.clicked.connect(self.generate_crossword)
        self.check_btn.clicked.connect(self.check_and_display)
        self.clear_btn.clicked.connect(self.clear_all)
        self.export_btn.clicked.connect(lambda: self.export_handler.export_text(self))
        self.export_img_btn.clicked.connect(lambda: self.export_handler.export_image(self))
        self.export_pdf_btn.clicked.connect(lambda: self.export_handler.export_pdf(self))
        self.solve_btn.clicked.connect(self.auto_solve)
        self.save_crossword_btn.clicked.connect(self.save_crossword)
        self.load_crossword_btn.clicked.connect(self.load_crossword)

        self._toggle_size_controls()
        self._connect_highlighting()
        logging.info("App initialized.")

    def _toggle_size_controls(self):
        auto = self.auto_size_cb.isChecked()
        self.rows_spin.setEnabled(not auto)
        self.cols_spin.setEnabled(not auto)

    def apply_grid_size(self):
        if self.auto_size_cb.isChecked(): return
        rows, cols = self.rows_spin.value(), self.cols_spin.value()
        self.clear_all()
        self.grid_widget.resize_grid(rows, cols)
        self._highlight_connected = False
        self._connect_highlighting()

    def clear_all(self):
        self.grid_widget.clear_grid()
        self.clue_list.clear()
        self.word_numbers.clear()
        self.placed_words_data.clear()

    def _connect_highlighting(self):
        if self._highlight_connected: return
        for r in range(self.grid_widget.rows):
            for c in range(self.grid_widget.cols):
                self.grid_widget.cells[r][c].clicked.connect(self.highlight_word)
        self._highlight_connected = True

    def highlight_word(self, row, col):
        for r in range(self.grid_widget.rows):
            for c in range(self.grid_widget.cols):
                self.grid_widget.cells[r][c].reset_color()
        if self.grid_widget.cells[row][col].is_blocked: return
        is_across = is_down = False
        sc, ec = col, col
        while sc > 0 and not self.grid_widget.cells[row][sc - 1].is_blocked: sc -= 1
        while ec < self.grid_widget.cols - 1 and not self.grid_widget.cells[row][ec + 1].is_blocked: ec += 1
        if ec - sc >= 1:
            is_across = True
            for c in range(sc, ec + 1): self.grid_widget.cells[row][c].highlight_across()
        sr, er = row, row
        while sr > 0 and not self.grid_widget.cells[sr - 1][col].is_blocked: sr -= 1
        while er < self.grid_widget.rows - 1 and not self.grid_widget.cells[er + 1][col].is_blocked: er += 1
        if er - sr >= 1:
            is_down = True
            for r in range(sr, er + 1): self.grid_widget.cells[r][col].highlight_down()
        if is_across and is_down: self.grid_widget.cells[row][col].highlight_both()

    def _calculate_grid_size(self, words):
        if not words: return 15, 15
        max_len = max(len(w) for w in words)
        total_letters = sum(len(w) for w in words)
        
        # Calculate area needed assuming ~30% black space, + padding for longest word
        area = int(total_letters / 0.30) + (max_len * 2)
        
        # Make it slightly wider than tall
        cols = int(math.sqrt(area * 1.3))
        rows = int(area / cols)
        
        # Ensure grid can physically fit the longest word
        cols = max(cols, max_len + 2)
        rows = max(rows, max_len + 2)
        
        # Add breathing room
        cols += 4
        rows += 4
        
        # Clamp to max UI size
        return min(rows, 50), min(cols, 50)

    def generate_crossword(self):
        words = self.word_manager.get_words()
        if not words:
            logging.warning("No words provided.")
            return

        # AUTO SIZE
        rows, cols = self._calculate_grid_size(words)
        if self.auto_size_cb.isChecked():
            self.rows_spin.setValue(rows); self.cols_spin.setValue(cols)
            self.size_info_label.setText(f"Auto: {rows} x {cols}")
            logging.info(f"Auto-sizing grid to: {rows} rows x {cols} cols")

        self.clear_all()
        self._highlight_connected = False
        self.grid_widget.resize_grid(rows, cols)
        self._connect_highlighting()

        # SOLVER
        try:
            solver = CrosswordSolver(rows, cols, words, mcts_simulations=self.mcts_spin.value())
            success, placed_words = solver.solve()
        except Exception as e:
            logging.error(f"Solver crashed: {str(e)}")
            return

        if not success or not placed_words:
            logging.error("Algorithm failed to fit words.")
            return

        for word, r, c, d in placed_words:
            self._place_word_on_grid(word, r, c, d)

        self.grid_widget.block_empty_cells()
        self._draw_clues(placed_words)

    def _draw_clues(self, placed_words):
        self.word_numbers.clear()
        self.placed_words_data.clear()
        
        starts = {}
        for word, r, c, d in placed_words:
            if (r, c) not in starts: starts[(r, c)] = {'across': None, 'down': None}
            if d == 'H': starts[(r, c)]['across'] = word
            else: starts[(r, c)]['down'] = word

        number = 1
        for r, c in sorted(starts.keys(), key=lambda x: (x[0], x[1])):
            self.word_numbers[(r, c)] = number
            for d, key in [('H', 'across'), ('V', 'down')]:
                if starts[(r, c)][key]:
                    self.placed_words_data.append({"word": starts[(r, c)][key], "row": r, "col": c, "dir": d, "num": number})
            number += 1

        for (r, c), num in self.word_numbers.items():
            self.grid_widget.cells[r][c].set_cell_number(num)

        self.clue_list.clear()
        across_clues = [d for d in self.placed_words_data if d['dir'] == 'H']
        down_clues = [d for d in self.placed_words_data if d['dir'] == 'V']
        
        self.clue_list.addItem("── ACROSS ──")
        for data in sorted(across_clues, key=lambda x: x['num']):
            word = data['word']
            # GET HINT DIRECTLY FROM WORD MANAGER
            hint = self.word_manager.hints.get(word, "No hint available")
            self.clue_list.addItem(f"{data['num']}. {hint} ({word})")
            
        self.clue_list.addItem("")
        self.clue_list.addItem("── DOWN ──")
        for data in sorted(down_clues, key=lambda x: x['num']):
            word = data['word']
            # GET HINT DIRECTLY FROM WORD MANAGER
            hint = self.word_manager.hints.get(word, "No hint available")
            self.clue_list.addItem(f"{data['num']}. {hint} ({word})")

    def _place_word_on_grid(self, word, row, col, direction):
        if direction == 'H':
            for i, ch in enumerate(word):
                cell = self.grid_widget.cells[row][col + i]
                cell.setText(ch); cell.correct_letter = ch
        else:
            for i, ch in enumerate(word):
                cell = self.grid_widget.cells[row + i][col]
                cell.setText(ch); cell.correct_letter = ch

    def check_and_display(self):
        self.grid_widget.check_answers()
        correct = incorrect = empty = 0
        for r in range(self.grid_widget.rows):
            for c in range(self.grid_widget.cols):
                cell = self.grid_widget.cells[r][c]
                if cell.is_blocked or cell.correct_letter is None: continue
                if cell.text() == "": empty += 1
                elif cell.text().upper() == cell.correct_letter.upper(): correct += 1
                else: incorrect += 1
        total = correct + incorrect
        if total > 0: logging.info(f"Score: {(correct/total)*100:.1f}%")
        else: logging.info("No answers to check.")

    def auto_solve(self):
        for r in range(self.grid_widget.rows):
            for c in range(self.grid_widget.cols):
                cell = self.grid_widget.cells[r][c]
                if not cell.is_blocked and cell.correct_letter:
                    cell.setText(cell.correct_letter); cell.reset_color()

    def save_crossword(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Crossword", "", "JSON Files (*.json)")
        if path:
            # Save hints from word manager
            with open(path, "w") as f:
                json.dump({"rows": self.grid_widget.rows, "cols": self.grid_widget.cols, "words": self.placed_words_data, "hints": self.word_manager.hints}, f, indent=4)
            logging.info("Saved puzzle.")

    def load_crossword(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Crossword", "", "JSON Files (*.json)")
        if not path: return
        try:
            with open(path, "r") as f: data = json.load(f)
            rows, cols = data.get("rows", 15), data.get("cols", 15)
            self.rows_spin.setValue(rows); self.cols_spin.setValue(cols)
            self.auto_size_cb.setChecked(False); self._toggle_size_controls()
            if rows != self.grid_widget.rows or cols != self.grid_widget.cols:
                self._highlight_connected = False
                self.grid_widget.resize_grid(rows, cols)
                self._connect_highlighting()
            self.clear_all()
            
            # Load hints into word manager
            self.word_manager.hints = data.get("hints", {})
            
            for w_data in data.get("words", []):
                word, r, c, d, num = w_data["word"], w_data["row"], w_data["col"], w_data["dir"], w_data["num"]
                if (r,c) not in self.word_numbers: 
                    self.word_numbers[(r,c)] = num; self.grid_widget.cells[r][c].set_cell_number(num)
                for i, ch in enumerate(word):
                    cell = self.grid_widget.cells[r + (i if d == 'V' else 0)][c + (i if d == 'H' else 0)]
                    cell.setText(ch); cell.correct_letter = ch
                self.placed_words_data.append(w_data)
            self._draw_clues(self.placed_words_data)
            self.grid_widget.block_empty_cells()
            logging.info("Loaded puzzle.")
        except Exception as e:
            logging.error(f"Failed to load: {str(e)}")
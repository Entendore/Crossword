from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                                 QFileDialog, QLabel, QPushButton, QInputDialog)
import json
import logging

class WordManager(QWidget):
    def __init__(self):
        super().__init__()
        self.hints = {}  # SINGLE SOURCE OF TRUTH FOR HINTS
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.count_label = QLabel("Words: 0")
        self.count_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.count_label)
        
        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(200)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add")
        self.remove_btn = QPushButton("Remove")
        self.clear_btn = QPushButton("Clear")
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)
        
        file_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load")
        self.load_hints_btn = QPushButton("Load+Hints")
        self.save_btn = QPushButton("Save")
        file_layout.addWidget(self.load_btn)
        file_layout.addWidget(self.load_hints_btn)
        file_layout.addWidget(self.save_btn)
        layout.addLayout(file_layout)
        
        self.setLayout(layout)

        self.add_btn.clicked.connect(self.add_word)
        self.remove_btn.clicked.connect(self.remove_word)
        self.clear_btn.clicked.connect(self.clear_words)
        # BOTH BUTTONS NOW CALL THE EXACT SAME LOGIC
        self.load_btn.clicked.connect(self._load_words_safe)
        self.load_hints_btn.clicked.connect(self._load_words_safe)
        self.save_btn.clicked.connect(self.save_words)
        
        self.list_widget.model().rowsInserted.connect(self.update_count)
        self.list_widget.model().rowsRemoved.connect(self.update_count)

    def update_count(self):
        self.count_label.setText(f"Words: {self.list_widget.count()} | Hints: {len(self.hints)}")

    def get_words(self):
        return [self.list_widget.item(i).text() for i in range(self.list_widget.count())]

    def add_word(self):
        word, ok1 = QInputDialog.getText(self, "Add Word", "Enter word:")
        if ok1 and word.strip():
            final_word = word.strip().upper()
            hint, ok2 = QInputDialog.getText(self, "Add Hint", f"Enter hint for '{final_word}':")
            self.list_widget.addItem(final_word)
            if ok2 and hint.strip():
                self.hints[final_word] = hint.strip()
                self.update_count()

    def remove_word(self):
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))

    def clear_words(self):
        self.list_widget.clear()
        self.hints.clear()
        self.update_count()

    def _load_words_safe(self):
        """Bulletproof loader that ALWAYS grabs hints if they exist in the JSON."""
        path, _ = QFileDialog.getOpenFileName(self, "Load Words", "", "JSON Files (*.json);;Text Files (*.txt)")
        if not path: return
        
        try:
            if path.endswith(".json"):
                with open(path, "r") as f:
                    data = json.load(f)
                
                new_words = []
                
                if isinstance(data, dict):
                    # It's a {"WORD": "hint"} format
                    for word, hint in data.items():
                        clean_word = word.strip().upper()
                        new_words.append(clean_word)
                        self.hints[clean_word] = hint # SAVE HINT
                elif isinstance(data, list):
                    new_words = [w.strip().upper() for w in data]
                
                self.list_widget.clear()
                self.list_widget.addItems(new_words)
                logging.info(f"Loaded {len(new_words)} words and {len(self.hints)} hints from JSON.")
                
            else:
                with open(path, "r") as f:
                    words = [line.strip().upper() for line in f if line.strip()]
                self.list_widget.clear()
                self.list_widget.addItems(words)
                logging.info(f"Loaded {len(words)} words from TXT (no hints).")
                
            self.update_count()
            
        except Exception as e:
            logging.error(f"Failed to load file: {str(e)}")

    def save_words(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Word List", "", "JSON Files (*.json)")
        if path:
            with open(path, "w") as f:
                json.dump(self.get_words(), f, indent=2)
import sys
from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.importer import get_csv_columns, import_csv


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_file_path: Path | None = None
        self.current_rows: list[dict] = []

        self.setWindowTitle("clear-feedback")
        self.resize(1000, 700)

        self.title_label = QLabel("clear-feedback")
        self.title_label.setStyleSheet("font-size: 28px; font-weight: bold;")

        self.subtitle_label = QLabel(
            "Import a CSV file, select the feedback column, and preview responses."
        )
        self.subtitle_label.setStyleSheet("font-size: 15px; color: #555;")

        self.import_button = QPushButton("Import CSV")
        self.import_button.clicked.connect(self.import_csv_file)

        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #666;")

        self.column_label = QLabel("Feedback column:")
        self.column_selector = QComboBox()
        self.column_selector.setEnabled(False)
        self.column_selector.currentTextChanged.connect(self.refresh_preview)

        top_actions_layout = QHBoxLayout()
        top_actions_layout.addWidget(self.import_button)
        top_actions_layout.addWidget(self.file_label)
        top_actions_layout.addStretch()

        column_layout = QHBoxLayout()
        column_layout.addWidget(self.column_label)
        column_layout.addWidget(self.column_selector)
        column_layout.addStretch()

        self.preview_label = QLabel("Preview")
        self.preview_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(0)
        self.preview_table.setRowCount(0)

        layout = QVBoxLayout()
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addLayout(top_actions_layout)
        layout.addLayout(column_layout)
        layout.addWidget(self.preview_label)
        layout.addWidget(self.preview_table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def import_csv_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import CSV",
            "",
            "CSV files (*.csv)",
        )

        if not file_path:
            return

        try:
            self.current_file_path = Path(file_path)
            self.current_rows = import_csv(self.current_file_path)
            columns = get_csv_columns(self.current_file_path)

            self.file_label.setText(str(self.current_file_path.name))

            self.column_selector.blockSignals(True)
            self.column_selector.clear()
            self.column_selector.addItems(columns)
            self.column_selector.setEnabled(True)
            self.column_selector.blockSignals(False)

            if columns:
                self.column_selector.setCurrentIndex(0)

            self.refresh_preview()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Import error",
                f"Could not import CSV file.\n\n{error}",
            )

    def refresh_preview(self):
        if not self.current_rows:
            return

        selected_column = self.column_selector.currentText()

        if not selected_column:
            return

        preview_rows = self.current_rows[:20]

        self.preview_table.clear()
        self.preview_table.setRowCount(len(preview_rows))
        self.preview_table.setColumnCount(2)
        self.preview_table.setHorizontalHeaderLabels(["Row", selected_column])

        for row_index, row in enumerate(preview_rows):
            row_number_item = QTableWidgetItem(str(row_index + 1))
            feedback_value = row.get(selected_column, "")
            feedback_item = QTableWidgetItem("" if pd.isna(feedback_value) else str(feedback_value))

            self.preview_table.setItem(row_index, 0, row_number_item)
            self.preview_table.setItem(row_index, 1, feedback_item)

        self.preview_table.resizeColumnsToContents()


def run_app():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
import sys
from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.analyzer import analyze_feedback_items
from core.classifier import classify_feedback_items
from core.cleaner import clean_feedback_items
from core.config import load_categories, load_themes
from core.exporter import export_enriched_csv
from core.importer import get_csv_columns, import_csv
from core.theme_classifier import classify_feedback_themes
from report import generate_markdown_report


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR / "data" / "configs" / "default_categories.json"
DEFAULT_THEMES_PATH = BASE_DIR / "data" / "configs" / "default_themes.json"
DEFAULT_EXPORTS_DIR = BASE_DIR / "data" / "exports"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_file_path: Path | None = None
        self.current_rows: list[dict] = []
        self.current_result = None

        self.setWindowTitle("clear-feedback")
        self.resize(1250, 800)

        self.apply_styles()

        self.title_label = QLabel("clear-feedback")
        self.title_label.setStyleSheet("font-size: 30px; font-weight: bold;")

        self.subtitle_label = QLabel(
            "Turn open-ended feedback into clear themes, categories, and actionable patterns."
        )
        self.subtitle_label.setStyleSheet("font-size: 15px; color: #D1D5DB;")

        self.tabs = QTabWidget()

        self.import_tab = QWidget()
        self.insights_tab = QWidget()
        self.review_tab = QWidget()
        self.export_tab = QWidget()

        self.tabs.addTab(self.import_tab, "1. Import")
        self.tabs.addTab(self.insights_tab, "2. Insights")
        self.tabs.addTab(self.review_tab, "3. Review")
        self.tabs.addTab(self.export_tab, "4. Export")

        self.build_import_tab()
        self.build_insights_tab()
        self.build_review_tab()
        self.build_export_tab()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)
        main_layout.addWidget(self.title_label)
        main_layout.addWidget(self.subtitle_label)
        main_layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def apply_styles(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #111827;
                color: #F9FAFB;
            }

            QWidget {
                background-color: #111827;
                color: #F9FAFB;
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 13px;
            }

            QLabel {
                color: #F9FAFB;
            }

            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 8px 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #1D4ED8;
            }

            QPushButton:disabled {
                background-color: #374151;
                color: #9CA3AF;
            }

            QComboBox {
                background-color: #1F2937;
                color: #F9FAFB;
                border: 1px solid #374151;
                border-radius: 7px;
                padding: 6px;
                min-width: 180px;
            }

            QComboBox QAbstractItemView {
                background-color: #1F2937;
                color: #F9FAFB;
                selection-background-color: #2563EB;
            }

            QCheckBox {
                color: #F9FAFB;
                spacing: 8px;
            }

            QTabWidget::pane {
                border: 1px solid #374151;
                border-radius: 8px;
                background-color: #111827;
                top: -1px;
            }

            QTabBar::tab {
                background-color: #1F2937;
                color: #D1D5DB;
                padding: 10px 18px;
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
                margin-right: 3px;
            }

            QTabBar::tab:selected {
                background-color: #2563EB;
                color: white;
            }

            QTableWidget {
                background-color: #1F2937;
                color: #F9FAFB;
                border: 1px solid #374151;
                border-radius: 8px;
                gridline-color: #374151;
                selection-background-color: #2563EB;
                selection-color: white;
                alternate-background-color: #172033;
            }

            QTableWidget::item {
                padding: 6px;
            }

            QHeaderView::section {
                background-color: #374151;
                color: #F9FAFB;
                padding: 8px;
                border: none;
                font-weight: bold;
            }

            QTextEdit {
                background-color: #1F2937;
                color: #F9FAFB;
                border: 1px solid #374151;
                border-radius: 8px;
                padding: 10px;
            }

            QFrame#Card {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 10px;
                padding: 12px;
            }

            QFrame#InfoBox {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 10px;
                padding: 12px;
            }
            """
        )

    def build_import_tab(self):
        self.import_button = QPushButton("Import CSV")
        self.import_button.clicked.connect(self.import_csv_file)

        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #D1D5DB;")

        self.column_label = QLabel("Feedback column:")
        self.column_selector = QComboBox()
        self.column_selector.setEnabled(False)
        self.column_selector.currentTextChanged.connect(self.refresh_preview)

        self.remove_duplicates_checkbox = QCheckBox("Remove exact duplicates")
        self.remove_duplicates_checkbox.setChecked(True)

        self.analyze_button = QPushButton("Run analysis")
        self.analyze_button.setEnabled(False)
        self.analyze_button.clicked.connect(self.run_analysis)

        top_actions_layout = QHBoxLayout()
        top_actions_layout.addWidget(self.import_button)
        top_actions_layout.addWidget(self.file_label)
        top_actions_layout.addStretch()

        analysis_actions_layout = QHBoxLayout()
        analysis_actions_layout.addWidget(self.column_label)
        analysis_actions_layout.addWidget(self.column_selector)
        analysis_actions_layout.addWidget(self.remove_duplicates_checkbox)
        analysis_actions_layout.addWidget(self.analyze_button)
        analysis_actions_layout.addStretch()

        self.import_status_label = QLabel(
            "Import a CSV file to begin. All processing runs locally on your computer."
        )
        self.import_status_label.setStyleSheet(
            "color: #D1D5DB; background-color: #1F2937; padding: 10px; border-radius: 8px;"
        )

        preview_title = QLabel("CSV preview")
        preview_title.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setColumnCount(0)
        self.preview_table.setRowCount(0)
        self.preview_table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        layout.addLayout(top_actions_layout)
        layout.addLayout(analysis_actions_layout)
        layout.addWidget(self.import_status_label)
        layout.addWidget(preview_title)
        layout.addWidget(self.preview_table)

        self.import_tab.setLayout(layout)

    def build_insights_tab(self):
        self.total_card = self.create_metric_card("Total responses", "0")
        self.empty_card = self.create_metric_card("Empty responses", "0")
        self.classified_card = self.create_metric_card("Classified", "0")
        self.unclassified_card = self.create_metric_card("Unclassified / Other", "0")

        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(12)
        metrics_layout.addWidget(self.total_card, 0, 0)
        metrics_layout.addWidget(self.empty_card, 0, 1)
        metrics_layout.addWidget(self.classified_card, 0, 2)
        metrics_layout.addWidget(self.unclassified_card, 0, 3)

        themes_title = QLabel("Top feedback themes")
        themes_title.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.theme_table = QTableWidget()
        self.theme_table.setAlternatingRowColors(True)
        self.theme_table.setColumnCount(5)
        self.theme_table.setHorizontalHeaderLabels(
            ["Theme", "Category", "Mentions", "Percentage", "Visual weight"]
        )
        self.theme_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        category_title = QLabel("Category breakdown")
        category_title.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.category_table = QTableWidget()
        self.category_table.setAlternatingRowColors(True)
        self.category_table.setColumnCount(4)
        self.category_table.setHorizontalHeaderLabels(
            ["Category", "Mentions", "Percentage", "Visual weight"]
        )
        self.category_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        terms_title = QLabel("Frequent terms")
        terms_title.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.frequent_terms_table = QTableWidget()
        self.frequent_terms_table.setAlternatingRowColors(True)
        self.frequent_terms_table.setColumnCount(2)
        self.frequent_terms_table.setHorizontalHeaderLabels(["Term", "Count"])
        self.frequent_terms_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        bottom_layout = QHBoxLayout()

        category_layout = QVBoxLayout()
        category_layout.addWidget(category_title)
        category_layout.addWidget(self.category_table)

        terms_layout = QVBoxLayout()
        terms_layout.addWidget(terms_title)
        terms_layout.addWidget(self.frequent_terms_table)

        bottom_layout.addLayout(category_layout, 2)
        bottom_layout.addLayout(terms_layout, 1)

        examples_title = QLabel("Representative examples by theme")
        examples_title.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.examples_box = QTextEdit()
        self.examples_box.setReadOnly(True)
        self.examples_box.setPlaceholderText(
            "Representative examples will appear here after running the analysis."
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        layout.addLayout(metrics_layout)
        layout.addWidget(themes_title)
        layout.addWidget(self.theme_table)
        layout.addLayout(bottom_layout)
        layout.addWidget(examples_title)
        layout.addWidget(self.examples_box)

        self.insights_tab.setLayout(layout)

    def build_review_tab(self):
        self.review_info_label = QLabel(
            "Use this table to audit individual comments. The main insight view is the grouped theme summary."
        )
        self.review_info_label.setStyleSheet(
            "color: #D1D5DB; background-color: #1F2937; padding: 10px; border-radius: 8px;"
        )

        self.review_table = QTableWidget()
        self.review_table.setAlternatingRowColors(True)
        self.review_table.setColumnCount(0)
        self.review_table.setRowCount(0)
        self.review_table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        layout.addWidget(self.review_info_label)
        layout.addWidget(self.review_table)

        self.review_tab.setLayout(layout)

    def build_export_tab(self):
        export_title = QLabel("Export results")
        export_title.setStyleSheet("font-size: 22px; font-weight: bold;")

        export_description = QLabel(
            "Export the analysis as a Markdown report or as an enriched CSV with categories, themes, and matched keywords."
        )
        export_description.setStyleSheet("color: #D1D5DB;")

        self.export_markdown_button = QPushButton("Export Markdown report")
        self.export_markdown_button.setEnabled(False)
        self.export_markdown_button.clicked.connect(self.export_markdown_report)

        self.export_csv_button = QPushButton("Export enriched CSV")
        self.export_csv_button.setEnabled(False)
        self.export_csv_button.clicked.connect(self.export_csv_file)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.export_markdown_button)
        buttons_layout.addWidget(self.export_csv_button)
        buttons_layout.addStretch()

        self.export_status_box = QTextEdit()
        self.export_status_box.setReadOnly(True)
        self.export_status_box.setPlainText(
            "Run an analysis first. Export options will be enabled after results are available."
        )

        info_box = QFrame()
        info_box.setObjectName("InfoBox")

        info_layout = QVBoxLayout()
        info_layout.addWidget(export_title)
        info_layout.addWidget(export_description)
        info_layout.addLayout(buttons_layout)
        info_box.setLayout(info_layout)

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        layout.addWidget(info_box)
        layout.addWidget(QLabel("Export log"))
        layout.addWidget(self.export_status_box)
        layout.addStretch()

        self.export_tab.setLayout(layout)

    def create_metric_card(self, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #D1D5DB; font-size: 13px;")

        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #F9FAFB;")

        layout = QVBoxLayout()
        layout.addWidget(title_label)
        layout.addWidget(value_label)

        card.setLayout(layout)

        card.title_label = title_label
        card.value_label = value_label

        return card

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

            self.analyze_button.setEnabled(True)
            self.import_status_label.setText(
                f"Loaded {len(self.current_rows)} rows from {self.current_file_path.name}. "
                "Select the feedback column and run analysis."
            )

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

        preview_rows = self.current_rows[:25]

        self.preview_table.clear()
        self.preview_table.setRowCount(len(preview_rows))
        self.preview_table.setColumnCount(2)
        self.preview_table.setHorizontalHeaderLabels(["Row", selected_column])

        for row_index, row in enumerate(preview_rows):
            row_number_item = QTableWidgetItem(str(row_index + 1))
            feedback_value = row.get(selected_column, "")
            feedback_item = QTableWidgetItem(
                "" if pd.isna(feedback_value) else str(feedback_value)
            )

            self.preview_table.setItem(row_index, 0, row_number_item)
            self.preview_table.setItem(row_index, 1, feedback_item)

        self.preview_table.resizeColumnsToContents()

    def run_analysis(self):
        selected_column = self.column_selector.currentText()

        if not selected_column:
            QMessageBox.warning(
                self,
                "Missing column",
                "Please select a feedback column before running the analysis.",
            )
            return

        try:
            categories = load_categories(DEFAULT_CONFIG_PATH)
            themes = load_themes(DEFAULT_THEMES_PATH)

            cleaned_items = clean_feedback_items(
                rows=self.current_rows,
                feedback_column=selected_column,
                remove_duplicates=self.remove_duplicates_checkbox.isChecked(),
            )

            classified_items = classify_feedback_items(
                items=cleaned_items,
                categories=categories,
                default_category="other",
            )

            themed_items = classify_feedback_themes(
                items=classified_items,
                themes=themes,
                default_theme="other",
            )

            result = analyze_feedback_items(themed_items)
            self.current_result = result

            self.update_insights(result)
            self.update_review_table(result)
            self.enable_exports()

            self.tabs.setCurrentWidget(self.insights_tab)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Analysis error",
                f"Could not analyze feedback.\n\n{error}",
            )

    def update_insights(self, result):
        self.total_card.value_label.setText(str(result.total_responses))
        self.empty_card.value_label.setText(str(result.empty_responses))
        self.classified_card.value_label.setText(str(result.classified_responses))
        self.unclassified_card.value_label.setText(str(result.unclassified_responses))

        self.update_theme_table(result)
        self.update_category_table(result)
        self.update_frequent_terms_table(result)
        self.update_examples_box(result)

    def update_theme_table(self, result):
        sorted_themes = sorted(
            result.theme_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        self.theme_table.clearContents()
        self.theme_table.setRowCount(len(sorted_themes))

        for row_index, (theme, count) in enumerate(sorted_themes):
            label = result.theme_labels.get(theme, theme)
            category = result.theme_categories.get(theme, "other")
            percentage = result.theme_percentages.get(theme, 0)
            visual_bar = self.build_text_bar(percentage)

            self.theme_table.setItem(row_index, 0, QTableWidgetItem(label))
            self.theme_table.setItem(row_index, 1, QTableWidgetItem(category))
            self.theme_table.setItem(row_index, 2, QTableWidgetItem(str(count)))
            self.theme_table.setItem(row_index, 3, QTableWidgetItem(f"{percentage}%"))
            self.theme_table.setItem(row_index, 4, QTableWidgetItem(visual_bar))

    def update_category_table(self, result):
        sorted_categories = sorted(
            result.category_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        self.category_table.clearContents()
        self.category_table.setRowCount(len(sorted_categories))

        for row_index, (category, count) in enumerate(sorted_categories):
            percentage = result.category_percentages.get(category, 0)
            visual_bar = self.build_text_bar(percentage)

            self.category_table.setItem(row_index, 0, QTableWidgetItem(category))
            self.category_table.setItem(row_index, 1, QTableWidgetItem(str(count)))
            self.category_table.setItem(row_index, 2, QTableWidgetItem(f"{percentage}%"))
            self.category_table.setItem(row_index, 3, QTableWidgetItem(visual_bar))

    def update_frequent_terms_table(self, result):
        self.frequent_terms_table.clearContents()
        self.frequent_terms_table.setRowCount(len(result.frequent_terms))

        for row_index, (term, count) in enumerate(result.frequent_terms):
            self.frequent_terms_table.setItem(row_index, 0, QTableWidgetItem(term))
            self.frequent_terms_table.setItem(row_index, 1, QTableWidgetItem(str(count)))

    def update_examples_box(self, result):
        examples_text = []

        sorted_themes = sorted(
            result.representative_theme_examples.items(),
            key=lambda item: result.theme_counts.get(item[0], 0),
            reverse=True,
        )

        for theme, examples in sorted_themes:
            label = result.theme_labels.get(theme, theme)
            category = result.theme_categories.get(theme, "other")
            count = result.theme_counts.get(theme, 0)
            percentage = result.theme_percentages.get(theme, 0)

            examples_text.append(label.upper())
            examples_text.append("-" * len(label))
            examples_text.append(f"Category: {category}")
            examples_text.append(f"Mentions: {count} ({percentage}%)")
            examples_text.append("")

            for example in examples:
                examples_text.append(f"• {example}")

            examples_text.append("")

        self.examples_box.setPlainText("\n".join(examples_text))

    def update_review_table(self, result):
        items = result.items

        self.review_table.clear()
        self.review_table.setRowCount(len(items))
        self.review_table.setColumnCount(7)
        self.review_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Original feedback",
                "Cleaned feedback",
                "Category",
                "Theme",
                "Category keywords",
                "Theme keywords",
            ]
        )

        for row_index, item in enumerate(items):
            self.review_table.setItem(row_index, 0, QTableWidgetItem(str(item.id)))
            self.review_table.setItem(row_index, 1, QTableWidgetItem(item.original_text))
            self.review_table.setItem(row_index, 2, QTableWidgetItem(item.cleaned_text))
            self.review_table.setItem(
                row_index,
                3,
                QTableWidgetItem(item.assigned_category or ""),
            )
            self.review_table.setItem(
                row_index,
                4,
                QTableWidgetItem(item.theme_label or item.assigned_theme or ""),
            )
            self.review_table.setItem(
                row_index,
                5,
                QTableWidgetItem(", ".join(item.matched_keywords)),
            )
            self.review_table.setItem(
                row_index,
                6,
                QTableWidgetItem(", ".join(item.matched_theme_keywords)),
            )

        self.review_table.resizeColumnsToContents()

    def enable_exports(self):
        self.export_markdown_button.setEnabled(True)
        self.export_csv_button.setEnabled(True)
        self.export_status_box.setPlainText(
            "Analysis completed. You can now export the Markdown report or enriched CSV."
        )

    def export_markdown_report(self):
        if self.current_result is None:
            QMessageBox.warning(
                self,
                "No results",
                "Run an analysis before exporting a report.",
            )
            return

        DEFAULT_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Markdown report",
            str(DEFAULT_EXPORTS_DIR / "feedback_report.md"),
            "Markdown files (*.md)",
        )

        if not file_path:
            return

        try:
            generate_markdown_report(self.current_result, file_path)
            self.append_export_log(f"Markdown report exported: {file_path}")
            QMessageBox.information(
                self,
                "Export completed",
                "Markdown report exported successfully.",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Export error",
                f"Could not export Markdown report.\n\n{error}",
            )

    def export_csv_file(self):
        if self.current_result is None:
            QMessageBox.warning(
                self,
                "No results",
                "Run an analysis before exporting a CSV file.",
            )
            return

        DEFAULT_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export enriched CSV",
            str(DEFAULT_EXPORTS_DIR / "enriched_feedback.csv"),
            "CSV files (*.csv)",
        )

        if not file_path:
            return

        try:
            export_enriched_csv(self.current_result.items, file_path)
            self.append_export_log(f"Enriched CSV exported: {file_path}")
            QMessageBox.information(
                self,
                "Export completed",
                "Enriched CSV exported successfully.",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Export error",
                f"Could not export enriched CSV.\n\n{error}",
            )

    def append_export_log(self, message: str):
        current_text = self.export_status_box.toPlainText().strip()

        if current_text:
            new_text = f"{current_text}\n{message}"
        else:
            new_text = message

        self.export_status_box.setPlainText(new_text)

    def build_text_bar(self, percentage: float) -> str:
        total_blocks = 20
        filled_blocks = round((percentage / 100) * total_blocks)
        empty_blocks = total_blocks - filled_blocks

        return "█" * filled_blocks + "░" * empty_blocks


def run_app():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
import sys
from pathlib import Path

import pandas as pd
from PySide6.QtCore import QObject, QThread, Signal
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
    QProgressBar,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.ai_analyzer import analyze_feedback_with_ai
from core.analyzer import analyze_feedback_items
from core.classifier import classify_feedback_items
from core.cleaner import clean_feedback_items
from core.config import load_categories, load_themes
from core.exporter import export_enriched_csv
from core.importer import get_csv_columns, import_csv
from core.theme_classifier import classify_feedback_themes
from report import generate_markdown_report
from report_ai import generate_ai_markdown_report


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR / "data" / "configs" / "default_categories.json"
DEFAULT_THEMES_PATH = BASE_DIR / "data" / "configs" / "default_themes.json"
DEFAULT_EXPORTS_DIR = BASE_DIR / "data" / "exports"


class AnalysisWorker(QObject):
    progress_updated = Signal(str, int)
    analysis_finished = Signal(object, object)
    analysis_failed = Signal(str)

    def __init__(
        self,
        rows: list[dict],
        feedback_column: str,
        remove_duplicates: bool,
        use_ai: bool,
        ai_model: str,
        ai_max_items: int | None,
    ):
        super().__init__()

        self.rows = rows
        self.feedback_column = feedback_column
        self.remove_duplicates = remove_duplicates
        self.use_ai = use_ai
        self.ai_model = ai_model
        self.ai_max_items = ai_max_items

    def run(self):
        try:
            self.progress_updated.emit("Loading categories and local rules...", 5)

            categories = load_categories(DEFAULT_CONFIG_PATH)
            themes = load_themes(DEFAULT_THEMES_PATH)

            self.progress_updated.emit("Cleaning feedback text...", 15)

            cleaned_items = clean_feedback_items(
                rows=self.rows,
                feedback_column=self.feedback_column,
                remove_duplicates=self.remove_duplicates,
            )

            self.progress_updated.emit("Classifying feedback with local rules...", 30)

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

            self.progress_updated.emit("Building keyword-based summary...", 45)

            result = analyze_feedback_items(themed_items)
            ai_result = None

            if self.use_ai:
                self.progress_updated.emit(
                    "Starting local AI analysis with Ollama...",
                    50,
                )

                ai_result = analyze_feedback_with_ai(
                    items=themed_items,
                    model=self.ai_model,
                    max_items=self.ai_max_items,
                    progress_callback=self.progress_updated.emit,
                )
            else:
                self.progress_updated.emit("Finishing analysis...", 90)

            self.progress_updated.emit("Analysis completed.", 100)
            self.analysis_finished.emit(result, ai_result)

        except Exception as error:
            self.analysis_failed.emit(str(error))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.current_file_path: Path | None = None
        self.current_rows: list[dict] = []
        self.current_result = None
        self.current_ai_result = None
        self.analysis_thread: QThread | None = None
        self.analysis_worker: AnalysisWorker | None = None

        self.setWindowTitle("clear-feedback")
        self.resize(1180, 800)

        self.apply_styles()

        self.title_label = QLabel("clear-feedback")
        self.title_label.setStyleSheet("font-size: 30px; font-weight: bold;")

        self.subtitle_label = QLabel(
            "Understand what people are asking for, what is missing, and what to improve next."
        )
        self.subtitle_label.setStyleSheet("font-size: 15px; color: #D1D5DB;")

        self.tabs = QTabWidget()

        self.import_tab = QWidget()
        self.insights_tab = QWidget()
        self.review_tab = QWidget()
        self.export_tab = QWidget()

        self.tabs.addTab(self.import_tab, "1. Import")
        self.tabs.addTab(self.insights_tab, "2. Summary")
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

            QProgressBar {
                background-color: #1F2937;
                color: #F9FAFB;
                border: 1px solid #374151;
                border-radius: 7px;
                text-align: center;
                height: 18px;
            }

            QProgressBar::chunk {
                background-color: #2563EB;
                border-radius: 7px;
            }

            QComboBox {
                background-color: #1F2937;
                color: #F9FAFB;
                border: 1px solid #374151;
                border-radius: 7px;
                padding: 6px;
                min-width: 150px;
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

            QFrame#InsightCard {
                background-color: #172033;
                border: 1px solid #374151;
                border-radius: 12px;
                padding: 16px;
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

        self.use_ai_checkbox = QCheckBox("Use local AI with Ollama")
        self.use_ai_checkbox.setChecked(True)

        self.ai_model_selector = QComboBox()
        self.ai_model_selector.addItems(
            [
                "llama3.2:3b",
                "gemma3:1b",
                "qwen2.5:3b",
            ]
        )

        self.ai_limit_selector = QComboBox()
        self.ai_limit_selector.addItems(
            [
                "Analyze all",
                "First 50",
                "First 100",
                "First 200",
            ]
        )

        self.analyze_button = QPushButton("Run analysis")
        self.analyze_button.setEnabled(False)
        self.analyze_button.clicked.connect(self.start_analysis)

        top_actions_layout = QHBoxLayout()
        top_actions_layout.addWidget(self.import_button)
        top_actions_layout.addWidget(self.file_label)
        top_actions_layout.addStretch()

        analysis_actions_layout = QHBoxLayout()
        analysis_actions_layout.addWidget(self.column_label)
        analysis_actions_layout.addWidget(self.column_selector)
        analysis_actions_layout.addWidget(self.remove_duplicates_checkbox)
        analysis_actions_layout.addWidget(self.use_ai_checkbox)
        analysis_actions_layout.addWidget(QLabel("Model:"))
        analysis_actions_layout.addWidget(self.ai_model_selector)
        analysis_actions_layout.addWidget(QLabel("Limit:"))
        analysis_actions_layout.addWidget(self.ai_limit_selector)
        analysis_actions_layout.addWidget(self.analyze_button)
        analysis_actions_layout.addStretch()

        self.import_status_label = QLabel(
            "Import a CSV file to begin. All processing runs locally."
        )
        self.import_status_label.setStyleSheet(
            "color: #D1D5DB; background-color: #1F2937; padding: 10px; border-radius: 8px;"
        )

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

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
        layout.addWidget(self.progress_bar)
        layout.addWidget(preview_title)
        layout.addWidget(self.preview_table)

        self.import_tab.setLayout(layout)

    def build_insights_tab(self):
        self.total_card = self.create_metric_card("Responses analyzed", "0")
        self.covered_card = self.create_metric_card("Covered by insights", "0")
        self.unassigned_card = self.create_metric_card("Not grouped", "0")
        self.coverage_card = self.create_metric_card("Coverage", "0%")

        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(12)
        metrics_layout.addWidget(self.total_card, 0, 0)
        metrics_layout.addWidget(self.covered_card, 0, 1)
        metrics_layout.addWidget(self.unassigned_card, 0, 2)
        metrics_layout.addWidget(self.coverage_card, 0, 3)

        main_title = QLabel("Top 3 things to act on")
        main_title.setStyleSheet("font-size: 24px; font-weight: bold;")

        main_description = QLabel(
            "These are the most important recurring insights detected from the feedback."
        )
        main_description.setStyleSheet("color: #D1D5DB;")

        self.top_insights_layout = QVBoxLayout()
        self.top_insight_cards: list[QFrame] = []

        for index in range(3):
            card = self.create_top_insight_card(index + 1)
            self.top_insight_cards.append(card)
            self.top_insights_layout.addWidget(card)

        export_note = QLabel(
            "For the complete breakdown, representative examples, and methodology, use the Export tab."
        )
        export_note.setWordWrap(True)
        export_note.setStyleSheet(
            "color: #D1D5DB; background-color: #1F2937; "
            "padding: 12px; border-radius: 8px;"
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)
        layout.addLayout(metrics_layout)
        layout.addWidget(main_title)
        layout.addWidget(main_description)
        layout.addLayout(self.top_insights_layout)
        layout.addWidget(export_note)
        layout.addStretch()

        self.insights_tab.setLayout(layout)

    def build_review_tab(self):
        self.review_info_label = QLabel(
            "Use this table only to audit individual comments. The Summary tab is designed for quick decision-making."
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
            "Export a complete report for deeper review, or export the enriched CSV for further analysis."
        )
        export_description.setStyleSheet("color: #D1D5DB;")

        self.export_ai_markdown_button = QPushButton("Export AI report")
        self.export_ai_markdown_button.setEnabled(False)
        self.export_ai_markdown_button.clicked.connect(self.export_ai_markdown_report)

        self.export_csv_button = QPushButton("Export enriched CSV")
        self.export_csv_button.setEnabled(False)
        self.export_csv_button.clicked.connect(self.export_csv_file)

        self.export_markdown_button = QPushButton("Export keyword report")
        self.export_markdown_button.setEnabled(False)
        self.export_markdown_button.clicked.connect(self.export_markdown_report)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.export_ai_markdown_button)
        buttons_layout.addWidget(self.export_csv_button)
        buttons_layout.addWidget(self.export_markdown_button)
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

    def create_top_insight_card(self, number: int) -> QFrame:
        card = QFrame()
        card.setObjectName("InsightCard")

        rank_label = QLabel(f"#{number}")
        rank_label.setStyleSheet("color: #93C5FD; font-size: 15px; font-weight: bold;")

        title_label = QLabel("Waiting for analysis")
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        metric_label = QLabel("0 mentions · 0%")
        metric_label.setStyleSheet("color: #D1D5DB; font-size: 14px;")

        summary_label = QLabel("Import feedback and run analysis to see this insight.")
        summary_label.setWordWrap(True)
        summary_label.setStyleSheet("color: #E5E7EB;")

        action_label = QLabel("")
        action_label.setWordWrap(True)
        action_label.setStyleSheet("color: #BFDBFE; font-weight: 600;")

        layout = QVBoxLayout()
        layout.addWidget(rank_label)
        layout.addWidget(title_label)
        layout.addWidget(metric_label)
        layout.addWidget(summary_label)
        layout.addWidget(action_label)

        card.setLayout(layout)

        card.title_label = title_label
        card.metric_label = metric_label
        card.summary_label = summary_label
        card.action_label = action_label

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

    def start_analysis(self):
        selected_column = self.column_selector.currentText()

        if not selected_column:
            QMessageBox.warning(
                self,
                "Missing column",
                "Please select a feedback column before running the analysis.",
            )
            return

        self.set_analysis_running(True)

        self.analysis_thread = QThread()
        self.analysis_worker = AnalysisWorker(
            rows=self.current_rows,
            feedback_column=selected_column,
            remove_duplicates=self.remove_duplicates_checkbox.isChecked(),
            use_ai=self.use_ai_checkbox.isChecked(),
            ai_model=self.ai_model_selector.currentText(),
            ai_max_items=self.get_ai_max_items(),
        )

        self.analysis_worker.moveToThread(self.analysis_thread)

        self.analysis_thread.started.connect(self.analysis_worker.run)
        self.analysis_worker.progress_updated.connect(self.update_analysis_progress)
        self.analysis_worker.analysis_finished.connect(self.handle_analysis_finished)
        self.analysis_worker.analysis_failed.connect(self.handle_analysis_failed)

        self.analysis_worker.analysis_finished.connect(self.analysis_thread.quit)
        self.analysis_worker.analysis_failed.connect(self.analysis_thread.quit)
        self.analysis_worker.analysis_finished.connect(self.analysis_worker.deleteLater)
        self.analysis_worker.analysis_failed.connect(self.analysis_worker.deleteLater)
        self.analysis_thread.finished.connect(self.analysis_thread.deleteLater)

        self.analysis_thread.start()

    def set_analysis_running(self, is_running: bool):
        self.analyze_button.setEnabled(not is_running)
        self.import_button.setEnabled(not is_running)
        self.column_selector.setEnabled(not is_running)
        self.remove_duplicates_checkbox.setEnabled(not is_running)
        self.use_ai_checkbox.setEnabled(not is_running)
        self.ai_model_selector.setEnabled(not is_running)
        self.ai_limit_selector.setEnabled(not is_running)

        self.progress_bar.setVisible(is_running)

        if is_running:
            self.progress_bar.setValue(0)
            self.import_status_label.setText("Starting analysis...")

    def update_analysis_progress(self, message: str, percentage: int):
        self.import_status_label.setText(message)
        self.progress_bar.setValue(percentage)

    def handle_analysis_finished(self, result, ai_result):
        self.current_result = result
        self.current_ai_result = ai_result

        self.update_summary(result)
        self.update_review_table(result)
        self.enable_exports()

        self.import_status_label.setText("Analysis completed.")
        self.progress_bar.setValue(100)
        self.set_analysis_running(False)

        self.tabs.setCurrentWidget(self.insights_tab)

        self.analysis_thread = None
        self.analysis_worker = None

    def handle_analysis_failed(self, error_message: str):
        self.set_analysis_running(False)
        self.progress_bar.setVisible(False)

        QMessageBox.critical(
            self,
            "Analysis error",
            f"Could not analyze feedback.\n\n{error_message}",
        )

        self.analysis_thread = None
        self.analysis_worker = None

    def get_ai_max_items(self) -> int | None:
        selected_limit = self.ai_limit_selector.currentText()

        if selected_limit == "First 50":
            return 50

        if selected_limit == "First 100":
            return 100

        if selected_limit == "First 200":
            return 200

        return None

    def update_summary(self, result):
        if self.current_ai_result is not None:
            self.update_ai_summary()
        else:
            self.update_keyword_summary(result)

    def update_ai_summary(self):
        ai_result = self.current_ai_result

        self.total_card.value_label.setText(str(ai_result.total_responses))
        self.covered_card.value_label.setText(str(ai_result.assigned_responses))
        self.unassigned_card.value_label.setText(str(ai_result.unassigned_responses))
        self.coverage_card.value_label.setText(f"{ai_result.coverage_percentage}%")

        themes = ai_result.themes

        for index, card in enumerate(self.top_insight_cards):
            if index >= len(themes):
                card.title_label.setText("No additional recurring insight")
                card.metric_label.setText("")
                card.summary_label.setText("")
                card.action_label.setText("")
                continue

            theme = themes[index]

            card.title_label.setText(theme.label)
            card.metric_label.setText(
                f"{theme.mentions} mentions · {theme.percentage}% · {theme.sentiment}"
            )
            card.summary_label.setText(theme.summary)
            card.action_label.setText(f"Recommended action: {theme.suggested_action}")

    def update_keyword_summary(self, result):
        self.total_card.value_label.setText(str(result.total_responses))
        self.covered_card.value_label.setText(str(result.classified_responses))
        self.unassigned_card.value_label.setText(str(result.unclassified_responses))

        coverage = (
            round((result.classified_responses / result.total_responses) * 100, 2)
            if result.total_responses
            else 0
        )

        self.coverage_card.value_label.setText(f"{coverage}%")

        sorted_themes = sorted(
            result.theme_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        for index, card in enumerate(self.top_insight_cards):
            if index >= len(sorted_themes):
                card.title_label.setText("No additional recurring insight")
                card.metric_label.setText("")
                card.summary_label.setText("")
                card.action_label.setText("")
                continue

            theme_name, count = sorted_themes[index]
            label = result.theme_labels.get(theme_name, theme_name)
            category = result.theme_categories.get(theme_name, "other")
            percentage = result.theme_percentages.get(theme_name, 0)

            card.title_label.setText(label)
            card.metric_label.setText(f"{count} mentions · {percentage}% · {category}")
            card.summary_label.setText(
                "Detected with keyword rules. Enable local AI for better summaries and suggested actions."
            )
            card.action_label.setText("")

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
        self.export_ai_markdown_button.setEnabled(self.current_ai_result is not None)

        self.export_status_box.setPlainText(
            "Analysis completed. Export the full report if you want detailed examples and methodology."
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
            "Export keyword Markdown report",
            str(DEFAULT_EXPORTS_DIR / "feedback_report.md"),
            "Markdown files (*.md)",
        )

        if not file_path:
            return

        try:
            generate_markdown_report(self.current_result, file_path)
            self.append_export_log(f"Keyword report exported: {file_path}")
            QMessageBox.information(
                self,
                "Export completed",
                "Keyword report exported successfully.",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Export error",
                f"Could not export keyword report.\n\n{error}",
            )

    def export_ai_markdown_report(self):
        if self.current_ai_result is None:
            QMessageBox.warning(
                self,
                "No AI results",
                "Run an analysis with local AI enabled before exporting an AI report.",
            )
            return

        DEFAULT_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export AI Markdown report",
            str(DEFAULT_EXPORTS_DIR / "ai_feedback_report.md"),
            "Markdown files (*.md)",
        )

        if not file_path:
            return

        try:
            generate_ai_markdown_report(self.current_ai_result, file_path)
            self.append_export_log(f"AI report exported: {file_path}")
            QMessageBox.information(
                self,
                "Export completed",
                "AI report exported successfully.",
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Export error",
                f"Could not export AI report.\n\n{error}",
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


def run_app():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
from pathlib import Path

from src.core.analyzer import analyze_feedback_items
from src.core.classifier import classify_feedback_items
from src.core.cleaner import clean_feedback_items
from src.core.config import load_categories
from src.core.exporter import export_enriched_csv
from src.core.importer import import_csv
from src.report import generate_markdown_report


def test_core_feedback_flow(tmp_path):
    sample_file = Path("src/data/examples/sample_feedback.csv")
    config_file = Path("src/data/configs/default_categories.json")

    rows = import_csv(sample_file)

    assert len(rows) > 0
    assert "feedback" in rows[0]

    categories = load_categories(config_file)

    assert len(categories) > 0
    assert any(category.name == "other" for category in categories)

    cleaned_items = clean_feedback_items(
        rows=rows,
        feedback_column="feedback",
        remove_duplicates=True,
    )

    assert len(cleaned_items) > 0
    assert all(item.original_text is not None for item in cleaned_items)
    assert all(item.cleaned_text is not None for item in cleaned_items)

    classified_items = classify_feedback_items(
        items=cleaned_items,
        categories=categories,
        default_category="other",
    )

    assert len(classified_items) == len(cleaned_items)
    assert all(item.assigned_category is not None for item in classified_items)

    result = analyze_feedback_items(classified_items)

    assert result.total_responses == len(classified_items)
    assert result.empty_responses >= 0
    assert result.classified_responses >= 0
    assert result.unclassified_responses >= 0
    assert isinstance(result.category_counts, dict)
    assert isinstance(result.category_percentages, dict)
    assert isinstance(result.frequent_terms, list)
    assert isinstance(result.representative_examples, dict)
    assert len(result.items) == len(classified_items)

    csv_output = tmp_path / "enriched_feedback.csv"
    markdown_output = tmp_path / "feedback_report.md"

    export_enriched_csv(classified_items, csv_output)
    generate_markdown_report(result, markdown_output)

    assert csv_output.exists()
    assert markdown_output.exists()
    assert csv_output.stat().st_size > 0
    assert markdown_output.stat().st_size > 0

    markdown_content = markdown_output.read_text(encoding="utf-8")

    assert "# Feedback Analysis Report" in markdown_content
    assert "## Executive Summary" in markdown_content
    assert "## Category Breakdown" in markdown_content
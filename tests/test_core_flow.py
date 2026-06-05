from pathlib import Path

from core.analyzer import analyze_feedback_items
from core.classifier import classify_feedback_items
from core.cleaner import clean_feedback_items
from core.config import load_categories, load_themes
from core.exporter import export_enriched_csv
from core.importer import import_csv
from core.theme_classifier import classify_feedback_themes
from report import generate_markdown_report


def test_core_feedback_flow(tmp_path):
    sample_file = Path("src/data/examples/sample_feedback.csv")
    categories_file = Path("src/data/configs/default_categories.json")
    themes_file = Path("src/data/configs/default_themes.json")

    rows = import_csv(sample_file)

    assert len(rows) > 0
    assert "feedback" in rows[0]

    categories = load_categories(categories_file)
    themes = load_themes(themes_file)

    assert len(categories) > 0
    assert len(themes) > 0
    assert any(category.name == "other" for category in categories)
    assert any(theme.name == "other" for theme in themes)

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

    themed_items = classify_feedback_themes(
        items=classified_items,
        themes=themes,
        default_theme="other",
    )

    assert len(themed_items) == len(cleaned_items)
    assert all(item.assigned_category is not None for item in themed_items)
    assert all(item.assigned_theme is not None for item in themed_items)
    assert all(item.theme_label is not None for item in themed_items)

    result = analyze_feedback_items(themed_items)

    assert result.total_responses == len(themed_items)
    assert result.empty_responses >= 0
    assert result.classified_responses >= 0
    assert result.unclassified_responses >= 0
    assert isinstance(result.category_counts, dict)
    assert isinstance(result.category_percentages, dict)
    assert isinstance(result.theme_counts, dict)
    assert isinstance(result.theme_percentages, dict)
    assert isinstance(result.theme_labels, dict)
    assert isinstance(result.theme_categories, dict)
    assert isinstance(result.frequent_terms, list)
    assert isinstance(result.representative_examples, dict)
    assert isinstance(result.representative_theme_examples, dict)
    assert len(result.items) == len(themed_items)

    csv_output = tmp_path / "enriched_feedback.csv"
    markdown_output = tmp_path / "feedback_report.md"

    export_enriched_csv(themed_items, csv_output)
    generate_markdown_report(result, markdown_output)

    assert csv_output.exists()
    assert markdown_output.exists()
    assert csv_output.stat().st_size > 0
    assert markdown_output.stat().st_size > 0

    markdown_content = markdown_output.read_text(encoding="utf-8")

    assert "# Feedback Analysis Report" in markdown_content
    assert "## Executive Summary" in markdown_content
    assert "## Top Feedback Themes" in markdown_content
    assert "## Category Breakdown" in markdown_content
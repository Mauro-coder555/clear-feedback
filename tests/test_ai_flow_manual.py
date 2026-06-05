import os
from pathlib import Path

import pytest

from core.ai_analyzer import analyze_feedback_with_ai
from core.cleaner import clean_feedback_items
from core.importer import import_csv


@pytest.mark.skipif(
    os.getenv("CLEAR_FEEDBACK_RUN_AI_TEST") != "1",
    reason="AI test skipped. Set CLEAR_FEEDBACK_RUN_AI_TEST=1 to run it.",
)
def test_ai_feedback_flow_manual():
    sample_file = Path("src/data/examples/sample_feedback.csv")

    rows = import_csv(sample_file)

    cleaned_items = clean_feedback_items(
        rows=rows,
        feedback_column="feedback",
        remove_duplicates=True,
    )

    result = analyze_feedback_with_ai(
        items=cleaned_items,
        model="llama3.2:3b",
        max_items=20,
    )

    assert result.total_responses > 0
    assert isinstance(result.themes, list)

    print()
    print(f"Total responses: {result.total_responses}")
    print(f"Assigned responses: {result.assigned_responses}")
    print(f"Unassigned responses: {result.unassigned_responses}")
    print(f"Coverage: {result.coverage_percentage}%")

    for theme in result.themes:
        print()
        print(theme.label)
        print(theme.category)
        print(theme.sentiment)
        print(theme.mentions)
        print(theme.percentage)
        print(theme.suggested_action)
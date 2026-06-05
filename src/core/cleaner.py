import re
from typing import Any

from models import FeedbackItem


def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value)

    if text.lower() == "nan":
        return ""

    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = text.lower()

    return text


def clean_feedback_items(
    rows: list[dict],
    feedback_column: str,
    remove_duplicates: bool = False,
) -> list[FeedbackItem]:
    items: list[FeedbackItem] = []
    seen_texts: set[str] = set()

    for index, row in enumerate(rows, start=1):
        if feedback_column not in row:
            raise KeyError(f"Feedback column not found: {feedback_column}")

        original_value = row.get(feedback_column)
        original_text = "" if original_value is None else str(original_value)
        cleaned_text = normalize_text(original_value)

        if remove_duplicates and cleaned_text in seen_texts:
            continue

        seen_texts.add(cleaned_text)

        item = FeedbackItem(
            id=index,
            original_text=original_text,
            cleaned_text=cleaned_text,
            is_empty=cleaned_text == "",
        )

        items.append(item)

    return items
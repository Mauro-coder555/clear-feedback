from pathlib import Path

import pandas as pd

from models import FeedbackItem


def export_enriched_csv(
    items: list[FeedbackItem],
    output_path: str | Path,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = []

    for item in items:
        rows.append(
            {
                "id": item.id,
                "original_text": item.original_text,
                "cleaned_text": item.cleaned_text,
                "is_empty": item.is_empty,
                "assigned_category": item.assigned_category,
                "assigned_theme": item.assigned_theme,
                "theme_label": item.theme_label,
                "matched_keywords": ", ".join(item.matched_keywords),
                "matched_theme_keywords": ", ".join(item.matched_theme_keywords),
                "manually_updated": item.manually_updated,
            }
        )

    dataframe = pd.DataFrame(rows)
    dataframe.to_csv(path, index=False, encoding="utf-8")
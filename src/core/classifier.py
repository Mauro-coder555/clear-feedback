from src.models import Category, FeedbackItem


def classify_feedback_items(
    items: list[FeedbackItem],
    categories: list[Category],
    default_category: str = "other",
) -> list[FeedbackItem]:
    keyword_categories = [
        category for category in categories if category.name != default_category
    ]

    for item in items:
        if item.is_empty:
            item.assigned_category = default_category
            item.matched_keywords = []
            continue

        matched_category = None
        matched_keywords: list[str] = []

        for category in keyword_categories:
            for keyword in category.keywords:
                normalized_keyword = keyword.strip().lower()

                if not normalized_keyword:
                    continue

                if normalized_keyword in item.cleaned_text:
                    matched_category = category.name
                    matched_keywords.append(normalized_keyword)

            if matched_category is not None:
                break

        item.assigned_category = matched_category or default_category
        item.matched_keywords = matched_keywords

    return items
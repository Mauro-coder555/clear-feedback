from models import FeedbackItem, Theme


def classify_feedback_themes(
    items: list[FeedbackItem],
    themes: list[Theme],
    default_theme: str = "other",
) -> list[FeedbackItem]:
    keyword_themes = [
        theme for theme in themes if theme.name != default_theme
    ]

    theme_by_name = {theme.name: theme for theme in themes}

    for item in items:
        if item.is_empty:
            assign_default_theme(item, theme_by_name, default_theme)
            continue

        best_theme = None
        best_matched_keywords: list[str] = []

        for theme in keyword_themes:
            matched_keywords = get_matching_keywords(
                text=item.cleaned_text,
                keywords=theme.keywords,
            )

            if len(matched_keywords) > len(best_matched_keywords):
                best_theme = theme
                best_matched_keywords = matched_keywords

        if best_theme is None:
            assign_default_theme(item, theme_by_name, default_theme)
        else:
            item.assigned_theme = best_theme.name
            item.theme_label = best_theme.label
            item.assigned_category = best_theme.category
            item.matched_theme_keywords = best_matched_keywords

    return items


def get_matching_keywords(text: str, keywords: list[str]) -> list[str]:
    matched_keywords = []

    for keyword in keywords:
        normalized_keyword = keyword.strip().lower()

        if not normalized_keyword:
            continue

        if normalized_keyword in text:
            matched_keywords.append(normalized_keyword)

    return matched_keywords


def assign_default_theme(
    item: FeedbackItem,
    theme_by_name: dict[str, Theme],
    default_theme: str,
) -> None:
    default = theme_by_name.get(default_theme)

    item.assigned_theme = default_theme

    if default is not None:
        item.theme_label = default.label
        item.assigned_category = default.category
    else:
        item.theme_label = default_theme
        item.assigned_category = "other"

    item.matched_theme_keywords = []
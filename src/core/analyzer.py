import re
from collections import Counter, defaultdict

from models import AnalysisResult, FeedbackItem


STOPWORDS = {
    "a",
    "al",
    "algo",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "con",
    "como",
    "de",
    "del",
    "el",
    "en",
    "es",
    "for",
    "from",
    "i",
    "in",
    "is",
    "it",
    "la",
    "las",
    "lo",
    "los",
    "más",
    "mas",
    "me",
    "more",
    "muy",
    "no",
    "of",
    "on",
    "or",
    "para",
    "pero",
    "por",
    "que",
    "se",
    "that",
    "the",
    "this",
    "to",
    "un",
    "una",
    "was",
    "with",
    "y",
}


def analyze_feedback_items(items: list[FeedbackItem]) -> AnalysisResult:
    total_responses = len(items)
    empty_responses = sum(1 for item in items if item.is_empty)

    classified_responses = sum(
        1
        for item in items
        if item.assigned_category is not None and item.assigned_category != "other"
    )

    unclassified_responses = total_responses - classified_responses

    category_counts = Counter(
        item.assigned_category or "other"
        for item in items
    )

    category_percentages = calculate_percentages(category_counts, total_responses)

    theme_counts = Counter(
        item.assigned_theme or "other"
        for item in items
    )

    theme_percentages = calculate_percentages(theme_counts, total_responses)

    theme_categories = {}
    theme_labels = {}

    for item in items:
        theme_name = item.assigned_theme or "other"
        theme_categories[theme_name] = item.assigned_category or "other"
        theme_labels[theme_name] = item.theme_label or theme_name

    frequent_terms = extract_frequent_terms(items)

    representative_examples = get_representative_examples_by_category(items)
    representative_theme_examples = get_representative_examples_by_theme(items)

    return AnalysisResult(
        total_responses=total_responses,
        empty_responses=empty_responses,
        classified_responses=classified_responses,
        unclassified_responses=unclassified_responses,
        category_counts=dict(category_counts),
        category_percentages=category_percentages,
        theme_counts=dict(theme_counts),
        theme_percentages=theme_percentages,
        theme_categories=theme_categories,
        theme_labels=theme_labels,
        frequent_terms=frequent_terms,
        representative_examples=representative_examples,
        representative_theme_examples=representative_theme_examples,
        items=items,
    )


def calculate_percentages(
    counts: Counter,
    total: int,
) -> dict[str, float]:
    if total == 0:
        return {}

    return {
        key: round((count / total) * 100, 2)
        for key, count in counts.items()
    }


def extract_frequent_terms(
    items: list[FeedbackItem],
    limit: int = 15,
) -> list[tuple[str, int]]:
    words: list[str] = []

    for item in items:
        if item.is_empty:
            continue

        item_words = re.findall(r"\b[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]{3,}\b", item.cleaned_text)

        words.extend(
            word.lower()
            for word in item_words
            if word.lower() not in STOPWORDS
        )

    counter = Counter(words)

    return counter.most_common(limit)


def get_representative_examples_by_category(
    items: list[FeedbackItem],
    limit_per_category: int = 3,
) -> dict[str, list[str]]:
    examples: dict[str, list[str]] = defaultdict(list)

    for item in items:
        category = item.assigned_category or "other"

        if item.is_empty:
            continue

        if len(examples[category]) < limit_per_category:
            examples[category].append(item.original_text)

    return dict(examples)


def get_representative_examples_by_theme(
    items: list[FeedbackItem],
    limit_per_theme: int = 3,
) -> dict[str, list[str]]:
    examples: dict[str, list[str]] = defaultdict(list)

    for item in items:
        theme = item.assigned_theme or "other"

        if item.is_empty:
            continue

        if len(examples[theme]) < limit_per_theme:
            examples[theme].append(item.original_text)

    return dict(examples)
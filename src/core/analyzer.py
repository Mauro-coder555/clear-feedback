import re
from collections import Counter, defaultdict

from src.models import AnalysisResult, FeedbackItem


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "i",
    "in",
    "is",
    "it",
    "more",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "with",
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

    category_percentages = {
        category: round((count / total_responses) * 100, 2)
        for category, count in category_counts.items()
    } if total_responses else {}

    frequent_terms = extract_frequent_terms(items)

    representative_examples = get_representative_examples(items)

    return AnalysisResult(
        total_responses=total_responses,
        empty_responses=empty_responses,
        classified_responses=classified_responses,
        unclassified_responses=unclassified_responses,
        category_counts=dict(category_counts),
        category_percentages=category_percentages,
        frequent_terms=frequent_terms,
        representative_examples=representative_examples,
        items=items,
    )


def extract_frequent_terms(
    items: list[FeedbackItem],
    limit: int = 10,
) -> list[tuple[str, int]]:
    words: list[str] = []

    for item in items:
        if item.is_empty:
            continue

        item_words = re.findall(r"\b[a-zA-Z]{3,}\b", item.cleaned_text)
        words.extend(
            word for word in item_words if word.lower() not in STOPWORDS
        )

    counter = Counter(words)

    return counter.most_common(limit)


def get_representative_examples(
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
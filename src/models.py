from dataclasses import dataclass, field


@dataclass
class FeedbackItem:
    id: int
    original_text: str
    cleaned_text: str
    is_empty: bool
    assigned_category: str | None = None
    assigned_theme: str | None = None
    theme_label: str | None = None
    matched_keywords: list[str] = field(default_factory=list)
    matched_theme_keywords: list[str] = field(default_factory=list)
    manually_updated: bool = False


@dataclass
class Category:
    name: str
    keywords: list[str]
    description: str = ""


@dataclass
class Theme:
    name: str
    label: str
    category: str
    keywords: list[str]
    description: str = ""


@dataclass
class AnalysisResult:
    total_responses: int
    empty_responses: int
    classified_responses: int
    unclassified_responses: int
    category_counts: dict[str, int]
    category_percentages: dict[str, float]
    theme_counts: dict[str, int]
    theme_percentages: dict[str, float]
    theme_categories: dict[str, str]
    theme_labels: dict[str, str]
    frequent_terms: list[tuple[str, int]]
    representative_examples: dict[str, list[str]]
    representative_theme_examples: dict[str, list[str]]
    items: list[FeedbackItem]
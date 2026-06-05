import json
from dataclasses import dataclass, field
from typing import Callable

import ollama

from models import FeedbackItem


DEFAULT_AI_MODEL = "llama3.2:3b"

ProgressCallback = Callable[[str, int], None]


@dataclass
class AITheme:
    name: str
    label: str
    category: str
    sentiment: str
    summary: str
    suggested_action: str
    matched_ids: list[int] = field(default_factory=list)
    mentions: int = 0
    percentage: float = 0.0
    examples: list[str] = field(default_factory=list)


@dataclass
class AIAnalysisResult:
    total_responses: int
    assigned_responses: int
    unassigned_responses: int
    coverage_percentage: float
    themes: list[AITheme]
    raw_response: dict


def analyze_feedback_with_ai(
    items: list[FeedbackItem],
    model: str = DEFAULT_AI_MODEL,
    max_items: int | None = None,
    progress_callback: ProgressCallback | None = None,
) -> AIAnalysisResult:
    report_progress(progress_callback, "Preparing feedback for AI analysis...", 5)

    valid_items = [
        item for item in items
        if not item.is_empty and item.cleaned_text.strip()
    ]

    if max_items is not None:
        valid_items = valid_items[:max_items]

    if not valid_items:
        report_progress(progress_callback, "No valid feedback found for AI analysis.", 100)

        return AIAnalysisResult(
            total_responses=0,
            assigned_responses=0,
            unassigned_responses=0,
            coverage_percentage=0,
            themes=[],
            raw_response={"themes": [], "assignments": []},
        )

    report_progress(progress_callback, "Detecting recurring themes with Ollama...", 25)

    detected_themes_response = detect_global_themes(
        items=valid_items,
        model=model,
    )

    detected_themes = parse_detected_themes(detected_themes_response)

    if not detected_themes:
        report_progress(progress_callback, "No recurring themes detected.", 100)

        return AIAnalysisResult(
            total_responses=len(valid_items),
            assigned_responses=0,
            unassigned_responses=len(valid_items),
            coverage_percentage=0,
            themes=[],
            raw_response={
                "themes": [],
                "assignments": [],
                "theme_detection": detected_themes_response,
            },
        )

    report_progress(progress_callback, "Assigning feedback to detected themes...", 65)

    assignments_response = assign_feedback_to_themes(
        items=valid_items,
        themes=detected_themes,
        model=model,
    )

    report_progress(progress_callback, "Building AI summary...", 90)

    result = build_ai_result(
        items=valid_items,
        themes=detected_themes,
        assignments_response=assignments_response,
        raw_theme_response=detected_themes_response,
    )

    report_progress(progress_callback, "AI analysis completed.", 100)

    return result


def report_progress(
    progress_callback: ProgressCallback | None,
    message: str,
    percentage: int,
) -> None:
    if progress_callback is not None:
        progress_callback(message, percentage)


def detect_global_themes(
    items: list[FeedbackItem],
    model: str,
) -> dict:
    prompt = build_theme_detection_prompt(items)

    response = ollama.generate(
        model=model,
        prompt=prompt,
        format=get_theme_detection_schema(),
        options={
            "temperature": 0.1,
        },
        stream=False,
    )

    response_text = response.get("response", "{}")
    return safe_json_loads(response_text)


def assign_feedback_to_themes(
    items: list[FeedbackItem],
    themes: list[AITheme],
    model: str,
) -> dict:
    prompt = build_assignment_prompt(items, themes)

    response = ollama.generate(
        model=model,
        prompt=prompt,
        format=get_assignment_schema(),
        options={
            "temperature": 0,
        },
        stream=False,
    )

    response_text = response.get("response", "{}")
    return safe_json_loads(response_text)


def build_theme_detection_prompt(items: list[FeedbackItem]) -> str:
    feedback_text = "\n".join(
        f"ID {item.id}: {item.original_text}"
        for item in items
    )

    return f"""
You are analyzing open-ended survey feedback.

Your task is to detect the most useful recurring themes for an executive summary.

Rules:
- Use the same language as the feedback when possible.
- Prefer 3 to 8 strong themes.
- Do not create one theme per comment.
- Do not create generic themes like "other feedback".
- Themes must be useful for decision-making.
- Focus on repeated needs, pain points, improvement opportunities, or strong positive signals.
- A theme can be broad enough to include similar comments with different wording.
- Keep labels short and clear.
- suggested_action must be concrete and useful.
- Return only valid JSON matching the schema.

Allowed categories:
content, platform, support, pricing, exercises, clarity, duration, technical-issues, feature-request, positive-feedback, negative-feedback, other.

Allowed sentiments:
positive, negative, mixed, neutral.

Feedback:
{feedback_text}
""".strip()


def build_assignment_prompt(
    items: list[FeedbackItem],
    themes: list[AITheme],
) -> str:
    feedback_text = "\n".join(
        f"ID {item.id}: {item.original_text}"
        for item in items
    )

    themes_text = "\n".join(
        f"- {theme.name}: {theme.label} | {theme.summary}"
        for theme in themes
    )

    return f"""
You are classifying survey feedback into a fixed list of detected themes.

Your task:
- Assign each feedback ID to zero, one, or more themes.
- Use only the theme names provided below.
- Do not invent new theme names.
- If a feedback item is vague, irrelevant, empty, or does not clearly match any theme, return an empty list for that ID.
- If a feedback item contains multiple separate ideas, it can belong to multiple themes.
- Return every feedback ID exactly once in the assignments list.
- Return only valid JSON matching the schema.

Detected themes:
{themes_text}

Feedback:
{feedback_text}
""".strip()


def get_theme_detection_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "themes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "label": {"type": "string"},
                        "category": {"type": "string"},
                        "sentiment": {"type": "string"},
                        "summary": {"type": "string"},
                        "suggested_action": {"type": "string"},
                    },
                    "required": [
                        "name",
                        "label",
                        "category",
                        "sentiment",
                        "summary",
                        "suggested_action",
                    ],
                },
            }
        },
        "required": ["themes"],
    }


def get_assignment_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "assignments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "theme_names": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["id", "theme_names"],
                },
            }
        },
        "required": ["assignments"],
    }


def parse_detected_themes(parsed_response: dict) -> list[AITheme]:
    themes_data = parsed_response.get("themes", [])
    themes: list[AITheme] = []

    seen_names: set[str] = set()

    for theme_data in themes_data:
        name = normalize_theme_name(theme_data.get("name", ""))

        if not name or name in seen_names:
            continue

        seen_names.add(name)

        theme = AITheme(
            name=name,
            label=theme_data.get("label", name),
            category=theme_data.get("category", "other"),
            sentiment=theme_data.get("sentiment", "neutral"),
            summary=theme_data.get("summary", ""),
            suggested_action=theme_data.get("suggested_action", ""),
        )

        themes.append(theme)

    return themes


def build_ai_result(
    items: list[FeedbackItem],
    themes: list[AITheme],
    assignments_response: dict,
    raw_theme_response: dict,
) -> AIAnalysisResult:
    item_by_id = {item.id: item for item in items}
    theme_by_name = {theme.name: theme for theme in themes}
    assigned_ids: set[int] = set()

    assignments = assignments_response.get("assignments", [])

    for assignment in assignments:
        try:
            item_id = int(assignment.get("id"))
        except (TypeError, ValueError):
            continue

        if item_id not in item_by_id:
            continue

        theme_names = assignment.get("theme_names", [])

        for raw_theme_name in theme_names:
            theme_name = normalize_theme_name(str(raw_theme_name))

            if theme_name not in theme_by_name:
                continue

            theme = theme_by_name[theme_name]

            if item_id not in theme.matched_ids:
                theme.matched_ids.append(item_id)
                assigned_ids.add(item_id)

    total_responses = len(items)

    for theme in themes:
        theme.matched_ids = sorted(set(theme.matched_ids))
        theme.mentions = len(theme.matched_ids)
        theme.percentage = (
            round((theme.mentions / total_responses) * 100, 2)
            if total_responses
            else 0
        )
        theme.examples = [
            item_by_id[item_id].original_text
            for item_id in theme.matched_ids[:2]
            if item_id in item_by_id
        ]

    filtered_themes = [
        theme for theme in themes
        if theme.mentions > 0
    ]

    filtered_themes.sort(
        key=lambda theme: theme.mentions,
        reverse=True,
    )

    assigned_responses = len(assigned_ids)
    unassigned_responses = total_responses - assigned_responses
    coverage_percentage = (
        round((assigned_responses / total_responses) * 100, 2)
        if total_responses
        else 0
    )

    return AIAnalysisResult(
        total_responses=total_responses,
        assigned_responses=assigned_responses,
        unassigned_responses=unassigned_responses,
        coverage_percentage=coverage_percentage,
        themes=filtered_themes,
        raw_response={
            "theme_detection": raw_theme_response,
            "assignments": assignments_response,
        },
    )


def safe_json_loads(value: str) -> dict:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def normalize_theme_name(value: str) -> str:
    normalized = value.strip().lower()
    normalized = normalized.replace("_", "-")
    normalized = normalized.replace("/", "-")
    normalized = "-".join(normalized.split())
    return normalized
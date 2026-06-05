from pathlib import Path

from models import AnalysisResult


def generate_markdown_report(
    result: AnalysisResult,
    output_path: str | Path,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    content = build_markdown_report(result)

    path.write_text(content, encoding="utf-8")


def build_markdown_report(result: AnalysisResult) -> str:
    lines: list[str] = []

    lines.append("# Feedback Analysis Report")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- Total responses: {result.total_responses}")
    lines.append(f"- Empty responses: {result.empty_responses}")
    lines.append(f"- Classified responses: {result.classified_responses}")
    lines.append(f"- Unclassified / other responses: {result.unclassified_responses}")
    lines.append("")

    lines.append("## Top Feedback Themes")
    lines.append("")

    if result.theme_counts:
        lines.append("| Theme | Category | Mentions | Percentage |")
        lines.append("|---|---|---:|---:|")

        sorted_themes = sorted(
            result.theme_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        for theme, count in sorted_themes:
            label = result.theme_labels.get(theme, theme)
            category = result.theme_categories.get(theme, "other")
            percentage = result.theme_percentages.get(theme, 0)

            lines.append(f"| {label} | {category} | {count} | {percentage}% |")
    else:
        lines.append("No themes found.")

    lines.append("")

    lines.append("## Category Breakdown")
    lines.append("")

    if result.category_counts:
        lines.append("| Category | Count | Percentage |")
        lines.append("|---|---:|---:|")

        sorted_categories = sorted(
            result.category_counts.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        for category, count in sorted_categories:
            percentage = result.category_percentages.get(category, 0)
            lines.append(f"| {category} | {count} | {percentage}% |")
    else:
        lines.append("No categories found.")

    lines.append("")

    lines.append("## Frequent Terms")
    lines.append("")

    if result.frequent_terms:
        for term, count in result.frequent_terms:
            lines.append(f"- **{term}**: {count}")
    else:
        lines.append("No frequent terms found.")

    lines.append("")

    lines.append("## Representative Examples by Theme")
    lines.append("")

    if result.representative_theme_examples:
        sorted_themes = sorted(
            result.representative_theme_examples.items(),
            key=lambda item: result.theme_counts.get(item[0], 0),
            reverse=True,
        )

        for theme, examples in sorted_themes:
            label = result.theme_labels.get(theme, theme)
            category = result.theme_categories.get(theme, "other")
            count = result.theme_counts.get(theme, 0)
            percentage = result.theme_percentages.get(theme, 0)

            lines.append(f"### {label}")
            lines.append("")
            lines.append(f"- Category: `{category}`")
            lines.append(f"- Mentions: `{count}`")
            lines.append(f"- Percentage: `{percentage}%`")
            lines.append("")

            for example in examples:
                lines.append(f"> {example}")
                lines.append("")
    else:
        lines.append("No representative examples found.")
        lines.append("")

    lines.append("## Methodology")
    lines.append("")
    lines.append(
        "This report was generated locally using keyword-based category and theme classification rules."
    )
    lines.append(
        "No external services, cloud processing, or login are required."
    )
    lines.append("")

    return "\n".join(lines)
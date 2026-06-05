from pathlib import Path

from src.models import AnalysisResult


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
    lines.append(f"- Unclassified responses: {result.unclassified_responses}")
    lines.append("")

    lines.append("## Category Breakdown")
    lines.append("")

    if result.category_counts:
        lines.append("| Category | Count | Percentage |")
        lines.append("|---|---:|---:|")

        for category, count in result.category_counts.items():
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

    lines.append("## Representative Examples")
    lines.append("")

    if result.representative_examples:
        for category, examples in result.representative_examples.items():
            lines.append(f"### {category}")
            lines.append("")

            for example in examples:
                lines.append(f"- {example}")

            lines.append("")
    else:
        lines.append("No representative examples found.")
        lines.append("")

    lines.append("## Methodology")
    lines.append("")
    lines.append(
        "This report was generated locally using keyword-based classification rules."
    )
    lines.append(
        "No external services, cloud processing, or login are required."
    )
    lines.append("")

    return "\n".join(lines)
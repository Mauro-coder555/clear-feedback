from pathlib import Path

from core.ai_analyzer import AIAnalysisResult


def generate_ai_markdown_report(
    result: AIAnalysisResult,
    output_path: str | Path,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    content = build_ai_markdown_report(result)

    path.write_text(content, encoding="utf-8")


def build_ai_markdown_report(result: AIAnalysisResult) -> str:
    lines: list[str] = []

    top_themes = result.themes[:3]

    lines.append("# AI Feedback Analysis Report")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"- Total analyzed responses: {result.total_responses}")
    lines.append(f"- Responses covered by detected themes: {result.assigned_responses}")
    lines.append(f"- Responses not assigned to a theme: {result.unassigned_responses}")
    lines.append(f"- Coverage: {result.coverage_percentage}%")
    lines.append(f"- Detected themes: {len(result.themes)}")
    lines.append("")

    if top_themes:
        lines.append("### Top recurring insights")
        lines.append("")

        for index, theme in enumerate(top_themes, start=1):
            lines.append(
                f"{index}. **{theme.label}** — "
                f"{theme.mentions} mentions ({theme.percentage}%)."
            )
            lines.append(f"   - Sentiment: `{theme.sentiment}`")
            lines.append(f"   - Category: `{theme.category}`")
            lines.append(f"   - Suggested action: {theme.suggested_action}")
            lines.append("")
    else:
        lines.append("No recurring themes were detected.")
        lines.append("")

    lines.append("## All Detected Themes")
    lines.append("")

    if result.themes:
        lines.append("| Theme | Category | Sentiment | Mentions | Percentage |")
        lines.append("|---|---|---|---:|---:|")

        for theme in result.themes:
            lines.append(
                f"| {theme.label} | {theme.category} | {theme.sentiment} | "
                f"{theme.mentions} | {theme.percentage}% |"
            )
    else:
        lines.append("No AI themes detected.")

    lines.append("")

    lines.append("## Detailed Findings")
    lines.append("")

    if result.themes:
        for theme in result.themes:
            lines.append(f"### {theme.label}")
            lines.append("")
            lines.append(f"- Category: `{theme.category}`")
            lines.append(f"- Sentiment: `{theme.sentiment}`")
            lines.append(f"- Mentions: `{theme.mentions}`")
            lines.append(f"- Percentage: `{theme.percentage}%`")
            lines.append("")

            lines.append("**What users are saying**")
            lines.append("")
            lines.append(theme.summary or "No summary provided.")
            lines.append("")

            lines.append("**Suggested action**")
            lines.append("")
            lines.append(theme.suggested_action or "No suggested action provided.")
            lines.append("")

            lines.append("**Representative examples**")
            lines.append("")

            if theme.examples:
                for example in theme.examples:
                    lines.append(f"> {example}")
                    lines.append("")
            else:
                lines.append("No representative examples available.")
                lines.append("")
    else:
        lines.append("No detailed findings available.")
        lines.append("")

    lines.append("## Methodology")
    lines.append("")
    lines.append(
        "This report was generated locally using Ollama. "
        "The feedback was processed on the user's computer without external cloud services."
    )
    lines.append("")
    lines.append(
        "The AI first detects recurring themes and then assigns each feedback response "
        "to zero, one, or more detected themes. Percentages are calculated from those assignments."
    )
    lines.append("")

    return "\n".join(lines)
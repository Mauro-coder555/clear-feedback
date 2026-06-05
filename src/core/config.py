import json
from pathlib import Path

from models import Category, Theme


def load_categories(file_path: str | Path) -> list[Category]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Categories config file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    categories_data = data.get("categories", [])

    categories = []

    for category_data in categories_data:
        category = Category(
            name=category_data["name"],
            description=category_data.get("description", ""),
            keywords=category_data.get("keywords", []),
        )
        categories.append(category)

    return categories


def save_categories(categories: list[Category], file_path: str | Path) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "categories": [
            {
                "name": category.name,
                "description": category.description,
                "keywords": category.keywords,
            }
            for category in categories
        ]
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def load_themes(file_path: str | Path) -> list[Theme]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Themes config file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    themes_data = data.get("themes", [])

    themes = []

    for theme_data in themes_data:
        theme = Theme(
            name=theme_data["name"],
            label=theme_data.get("label", theme_data["name"]),
            category=theme_data.get("category", "other"),
            description=theme_data.get("description", ""),
            keywords=theme_data.get("keywords", []),
        )
        themes.append(theme)

    return themes


def save_themes(themes: list[Theme], file_path: str | Path) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "themes": [
            {
                "name": theme.name,
                "label": theme.label,
                "category": theme.category,
                "description": theme.description,
                "keywords": theme.keywords,
            }
            for theme in themes
        ]
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
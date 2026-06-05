import json
from pathlib import Path

from src.models import Category


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
from pathlib import Path

import pandas as pd


def import_csv(file_path: str | Path) -> list[dict]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    if path.suffix.lower() != ".csv":
        raise ValueError(f"Expected a CSV file, got: {path.suffix}")

    dataframe = pd.read_csv(path)

    return dataframe.to_dict(orient="records")


def get_csv_columns(file_path: str | Path) -> list[str]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    dataframe = pd.read_csv(path, nrows=1)

    return list(dataframe.columns)
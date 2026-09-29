"""Load the five raw CSVs. Raw files are only ever read, never written."""
import csv
from pathlib import Path
import pandas as pd
from .config import RAW_DIR, REQUIRED_COLUMNS

TABLES = ["tickets", "agents", "customers", "orders", "products"]


def raw_path(name: str, raw_dir: Path = RAW_DIR) -> Path:
    exact = raw_dir / f"{name}.csv"
    if exact.exists():
        return exact
    matches = sorted(raw_dir.glob(f"*{name}.csv"))   # tolerate upload prefixes
    if not matches:
        raise FileNotFoundError(f"{name}.csv not found in {raw_dir}")
    return matches[0]


def raw_record_count(path: Path) -> int:
    """Independent CSV record count (handles quoted multi-line cells), excluding the header."""
    with open(path, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.reader(f)) - 1


def load_all(raw_dir: Path = RAW_DIR) -> dict:
    data = {}
    for name in TABLES:
        df = pd.read_csv(raw_path(name, raw_dir))
        missing = [c for c in REQUIRED_COLUMNS[name] if c not in df.columns]
        if missing:
            raise ValueError(f"{name}.csv missing required columns: {missing}")
        data[name] = df
    return data

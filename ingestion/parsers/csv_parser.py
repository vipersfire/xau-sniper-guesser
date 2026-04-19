"""Rule-based CSV parser for COT and FRED data. No AI/LLM."""
import csv
import io
from typing import Iterator


def parse_csv_rows(text: str, delimiter: str = ",", skip_header: bool = True) -> list[list[str]]:
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    if skip_header and rows:
        rows = rows[1:]
    return rows


def parse_csv_dicts(text: str, delimiter: str = ",") -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    return [dict(row) for row in reader]


def parse_fred_csv(text: str) -> list[dict]:
    """Parse FRED CSV: DATE,VALUE"""
    rows = parse_csv_dicts(text)
    result = []
    for row in rows:
        date_str = row.get("DATE", "").strip()
        value_str = row.get("VALUE", "").strip()
        if not date_str or value_str == ".":
            continue
        try:
            from datetime import date
            d = date.fromisoformat(date_str)
            v = float(value_str)
            result.append({"date": d, "value": v})
        except (ValueError, KeyError):
            continue
    return result

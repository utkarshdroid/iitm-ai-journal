#!/usr/bin/env python3
"""Validate a daily log JSON file against tracking/schema.json.

Usage:
    python automation/validate.py tracking/data/2025-09-15.json
    python automation/validate.py            # validates every file in tracking/data/

Exit code 0 = all valid, 1 = at least one problem. Fails loudly; never edits data.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "tracking" / "schema.json"
DATA_DIR = ROOT / "tracking" / "data"


def load_schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def validate_file(path: Path, schema: dict) -> list[str]:
    """Return a list of problem strings. Empty list = valid."""
    problems = []
    try:
        with open(path) as f:
            day = json.load(f)
    except json.JSONDecodeError as e:
        return [f"invalid JSON: {e}"]

    cats = set(schema["categories"])
    slots = schema["hourly_slots"]

    # date
    if "date" not in day:
        problems.append("missing 'date'")
    elif Path(path).stem != day["date"]:
        problems.append(f"filename '{Path(path).stem}' != date field '{day['date']}'")

    # slots
    day_slots = day.get("slots", {})
    for slot in slots:
        if slot not in day_slots:
            continue  # unfilled slot is allowed
        entry = day_slots[slot]
        cat = entry.get("category")
        if cat and cat not in cats:
            problems.append(f"slot {slot}: category '{cat}' not in schema")
        en = entry.get("energy")
        if en is not None and en not in (1, 2, 3, 4, 5):
            problems.append(f"slot {slot}: energy '{en}' not 1-5 or null")
    for slot in day_slots:
        if slot not in slots:
            problems.append(f"unknown slot '{slot}' not in schema")

    # signals
    sig = day.get("signals", {})
    for key in ("mood", "overall_energy"):
        v = sig.get(key)
        if v is not None and v not in (1, 2, 3, 4, 5):
            problems.append(f"signals.{key} '{v}' not 1-5 or null")

    return problems


def main():
    schema = load_schema()
    if len(sys.argv) > 1:
        targets = [Path(sys.argv[1])]
    else:
        targets = sorted(DATA_DIR.glob("*.json"))

    if not targets:
        print("No log files to validate.")
        return 0

    any_bad = False
    for path in targets:
        problems = validate_file(path, schema)
        if problems:
            any_bad = True
            print(f"FAIL  {path.name}")
            for p in problems:
                print(f"      - {p}")
        else:
            print(f"OK    {path.name}")
    return 1 if any_bad else 0


if __name__ == "__main__":
    sys.exit(main())

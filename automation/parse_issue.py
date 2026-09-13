#!/usr/bin/env python3
"""Parse a GitHub Issue Form submission into a valid daily log JSON.

GitHub Issue Forms render the body as markdown:
    ### Field Label
    <value>
    ### Next Field Label
    <value>

Usage:
    python automation/parse_issue.py < issue_body.txt
    python automation/parse_issue.py --body "..."     # inline
Writes tracking/data/<date>.json and prints the path.
Exits non-zero on any problem (bad date, no valid slots, unknown category).

This runs server-side in a GitHub Action (GitHub's own auth) — never needs a token.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "tracking" / "schema.json"
DATA_DIR = ROOT / "tracking" / "data"

NO_RESPONSE = "_no response_"


def load_schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def split_sections(body: str) -> dict:
    """Return {lowercased field label: value string} from issue-form markdown."""
    sections = {}
    current = None
    buff = []
    for line in body.splitlines():
        m = re.match(r"^###\s+(.*)$", line.strip())
        if m:
            if current is not None:
                sections[current] = "\n".join(buff).strip()
            current = m.group(1).strip().lower()
            buff = []
        else:
            buff.append(line)
    if current is not None:
        sections[current] = "\n".join(buff).strip()
    return sections


def clean(val: str):
    """Normalize a single-line field; treat GitHub's no-response marker as empty."""
    if val is None:
        return ""
    v = val.strip()
    return "" if v == NO_RESPONSE else v


def hour_to_slot(token: str, slots: list[str]):
    """Map loose hour input (6, 05, 5am, 17, 5pm) to a canonical slot start hour."""
    t = token.strip().lower().replace(" ", "")
    ampm = None
    if t.endswith("am"):
        ampm, t = "am", t[:-2]
    elif t.endswith("pm"):
        ampm, t = "pm", t[:-2]
    t = t.split(":")[0]  # allow "5:00"
    if not t.isdigit():
        return None
    h = int(t)
    if ampm == "pm" and h != 12:
        h += 12
    if ampm == "am" and h == 12:
        h = 0
    prefix = f"{h:02d}:00-"
    for s in slots:
        if s.startswith(prefix):
            return s
    return None


def parse_slots(text: str, schema: dict):
    """Parse the slots textarea. Returns (slots_dict, problems)."""
    slots_out = {}
    problems = []
    cats = set(schema["categories"])
    cats_lower = {c.lower(): c for c in cats}
    canon_slots = schema["hourly_slots"]

    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            problems.append(f"slots line {i}: need at least 'hour | category'")
            continue
        hour_tok, cat_tok = parts[0], parts[1]
        activity = parts[2] if len(parts) > 2 else ""
        energy = None
        if len(parts) > 3 and parts[3]:
            if parts[3] in ("1", "2", "3", "4", "5"):
                energy = int(parts[3])
            else:
                problems.append(f"slots line {i}: energy '{parts[3]}' not 1-5")

        slot = hour_to_slot(hour_tok, canon_slots)
        if slot is None:
            problems.append(f"slots line {i}: can't map hour '{hour_tok}' to a 5AM-11PM slot")
            continue
        cat = cats_lower.get(cat_tok.lower())
        if cat is None:
            problems.append(f"slots line {i}: category '{cat_tok}' not in schema")
            continue
        slots_out[slot] = {"activity": activity, "category": cat, "energy": energy}

    return slots_out, problems


def to_int_1_5(val):
    v = clean(val)
    return int(v) if v in ("1", "2", "3", "4", "5") else None


def to_float(val):
    v = clean(val)
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


def build_day(sections: dict, schema: dict):
    problems = []
    date = clean(sections.get("date", ""))
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        problems.append(f"date '{date}' is not YYYY-MM-DD")

    slots, slot_problems = parse_slots(sections.get("hourly slots", ""), schema)
    problems += slot_problems
    if not slots:
        problems.append("no valid slot lines")

    day = {
        "date": date,
        "slots": slots,
        "signals": {
            "sleep_hours": to_float(sections.get("sleep hours last night", "")),
            "woke_at": clean(sections.get("woke at (hh:mm)", "")),
            "mood": to_int_1_5(sections.get("overall mood", "")),
            "overall_energy": to_int_1_5(sections.get("overall energy", "")),
            "top_derailer": clean(sections.get("top derailer today", "")),
            "biggest_win": clean(sections.get("biggest win today", "")),
            "notes": clean(sections.get("notes", "")),
        },
    }
    return day, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--body", help="issue body text; if omitted, read stdin")
    args = ap.parse_args()

    body = args.body if args.body is not None else sys.stdin.read()
    schema = load_schema()
    sections = split_sections(body)
    day, problems = build_day(sections, schema)

    if problems:
        print("PARSE FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / f"{day['date']}.json"
    with open(out, "w") as f:
        json.dump(day, f, indent=2)
    print(str(out.relative_to(ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

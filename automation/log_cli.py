#!/usr/bin/env python3
"""Interactive CLI to log a day. Writes a valid JSON file to tracking/data/.

Usage:
    python automation/log_cli.py               # log today
    python automation/log_cli.py 2025-09-15    # log a specific date

Both this CLI and hand-editing produce the SAME schema. Many doors, one room.
Re-running for an existing date loads it so you can fill more slots (never wipes).
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "tracking" / "schema.json"
DATA_DIR = ROOT / "tracking" / "data"


def load_schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def ask(prompt, default=""):
    v = input(f"{prompt} " + (f"[{default}] " if default else "")).strip()
    return v or default


def ask_int_1_5(prompt):
    while True:
        v = input(f"{prompt} (1-5, blank to skip) ").strip()
        if v == "":
            return None
        if v in ("1", "2", "3", "4", "5"):
            return int(v)
        print("  please enter 1-5 or leave blank")


def pick_category(cats):
    while True:
        v = input("  category #: ").strip()
        if v == "":
            return None
        if v.isdigit() and 1 <= int(v) <= len(cats):
            return cats[int(v) - 1]
        print(f"  enter 1-{len(cats)} or blank to skip")


def main():
    schema = load_schema()
    cats = schema["categories"]
    slots = schema["hourly_slots"]

    the_date = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()
    out = DATA_DIR / f"{the_date}.json"

    if out.exists():
        with open(out) as f:
            day = json.load(f)
        print(f"Loaded existing log for {the_date}. Blank keeps current value.")
    else:
        day = {"date": the_date, "slots": {}, "signals": {}}
        print(f"New log for {the_date}.")

    print("\nCategories:")
    for i, c in enumerate(cats, 1):
        print(f"  {i:>2}. {c}")

    print("\n--- Hourly slots (blank category skips the slot) ---")
    for slot in slots:
        existing = day["slots"].get(slot, {})
        cur = f" (now: {existing.get('category')}/{existing.get('activity')})" if existing else ""
        print(f"\n{slot}{cur}")
        cat = pick_category(cats)
        if cat is None:
            continue
        activity = ask("  what did you do?", existing.get("activity", ""))
        energy = ask_int_1_5("  energy")
        day["slots"][slot] = {"activity": activity, "category": cat, "energy": energy}

    print("\n--- Daily signals ---")
    s = day.get("signals", {})
    sleep = ask("sleep hours last night?", str(s.get("sleep_hours", "")))
    s["sleep_hours"] = float(sleep) if sleep.replace(".", "", 1).isdigit() else None
    s["woke_at"] = ask("woke at (HH:MM)?", s.get("woke_at", "") or "")
    s["mood"] = ask_int_1_5("overall mood")
    s["overall_energy"] = ask_int_1_5("overall energy")
    s["top_derailer"] = ask("top derailer today?", s.get("top_derailer", "") or "")
    s["biggest_win"] = ask("biggest win today?", s.get("biggest_win", "") or "")
    s["notes"] = ask("notes?", s.get("notes", "") or "")
    day["signals"] = s

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(day, f, indent=2)
    print(f"\nSaved {out.relative_to(ROOT)}")
    print("Next: python automation/validate.py " + str(out.relative_to(ROOT)))


if __name__ == "__main__":
    main()

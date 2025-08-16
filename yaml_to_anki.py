#!/usr/bin/env python3
"""
yaml_to_anki_local.py

Reads pure YAML with entries like:
- word: example_word
  back: meaning... ("ex1") ("ex2")
  tags: noun

Writes anki_cards.csv with headers: Word, Back, Tags

Usage:
  python yaml_to_anki_local.py extracted.yaml
  cat extracted.yaml | python yaml_to_anki_local.py
"""

import sys
import yaml
import csv
import re
import os

OUTPUT_FILE = "anki_cards.csv"

def is_proper_name(word):
    return bool(re.match(r'^[A-Z]', word))

def process_data(data):
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise SystemExit("Parsed YAML is not a list/dict of entries.")

    seen = set()
    cleaned = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        word = str(entry.get("word", "")).strip()
        back = str(entry.get("back", "")).strip()
        tags = str(entry.get("tags", "")).strip()

        if not word:
            continue

        if not is_proper_name(word):
            word = word.lower()

        if word.lower() in seen:
            continue
        seen.add(word.lower())

        cleaned.append([word, back, tags])
    return cleaned

def main():
    if len(sys.argv) > 1:
        path = sys.argv[1]
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    else:
        raw = sys.stdin.read()

    raw = raw.strip()
    # strip ``` fences if present
    if raw.startswith("```") and raw.endswith("```"):
        raw = raw[3:-3].strip()

    try:
        data = yaml.safe_load(raw)
    except Exception as e:
        print("YAML parse error:", e, file=sys.stderr)
        sys.exit(2)

    cards = process_data(data)

    with open(OUTPUT_FILE, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Word", "Back", "Tags"])
        w.writerows(cards)

    print(f"✅ Wrote {len(cards)} cards to {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    main()


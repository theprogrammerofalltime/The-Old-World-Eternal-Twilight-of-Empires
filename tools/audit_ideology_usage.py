#!/usr/bin/env python3
"""Read-only audit to identify placeholder ideologies cluttering the political screen."""
from pathlib import Path
from collections import Counter
import re

ROOT = Path(__file__).resolve().parent.parent
source = (ROOT / "common/ideologies/00_ideologies.txt").read_text(encoding="utf-8-sig")
groups = re.findall(r"(?m)^\t([a-z_0-9]+)\s*=\s*\{", source)
if not groups:
    raise SystemExit("No ideology definitions found")
refs = Counter()
locations = {}
for folder in ["history/countries", "history/units", "common/characters", "common/national_focus", "common/decisions", "common/on_actions", "events", "common/dynamic_modifiers", "common/ideas", "common/scripted_effects", "common/scripted_guis", "common/scripted_localisation", "common/technologies", "interface"]:
    for path in (ROOT / folder).rglob("*.txt"):
        text = re.sub(r"(?m)#.*$", "", path.read_text(encoding="utf-8-sig", errors="replace"))
        for key in groups:
            n = len(re.findall(r"\b" + re.escape(key) + r"\b", text))
            if n:
                refs[key] += n
                locations.setdefault(key, set()).add(folder)
print(f"IDEOLOGY AUDIT: {len(groups)} registered groups; source references:")
for key in groups:
    print(f"{key:32s} {refs[key]:6d} {','.join(sorted(locations.get(key, [])))}")
print("Numbered groups with NO scenario/script references:")
print(", ".join(key for key in groups if re.search(r"_\d+$", key) and refs[key] == 0) or "None")

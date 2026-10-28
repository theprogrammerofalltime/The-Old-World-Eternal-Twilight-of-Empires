#!/usr/bin/env python3
"""Read-only audit for duplicate TOWE English localisation keys."""
from pathlib import Path
from collections import defaultdict
import re
root = Path(__file__).resolve().parent.parent
by_key = defaultdict(list)
for directory in ("localisation/english", "localisation/replace"):
    for path in sorted((root / directory).glob("*_l_english.yml")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1):
            match = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_.-]*):\d*\s*"', line)
            if match:
                by_key[match.group(1)].append(f"{path.relative_to(root)}:{lineno}")
dupes = {key: origins for key, origins in by_key.items() if len(origins) > 1}
print(f"TOWE localisation audit: {len(by_key)} keys, {len(dupes)} duplicated")
for key, locations in sorted(dupes.items()):
    print("DUPLICATE:", key, "|", " ".join(locations))

if dupes:
    raise SystemExit(1)

#!/usr/bin/env python3
"""Summarize HOI4 error.log without hiding or deleting any diagnostics.

Usage: python3 tools/summarize_rebuild_log.py /path/to/error.log
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

ISSUES = {
    "Missing/undefined GUI type": r"Undefined GUI_TYPE",
    "Missing GUI sprite": r"Failed to create gui object|Could not find sprite type",
    "Invalid dynamic-modifier reference": r"Invalid dynamic modifier",
    "Invalid modifier inside a definition": r"invalid modifier:",
    "Other malformed source tokens": r"Unexpected token:",
    "Localisation key collisions": r"loc key collisions",
    "Launcher/mod descriptor warnings": r"Invalid supported_version|mod/ugc_.*\.mod",
}
MODIFIER_NAME = re.compile(r"Invalid dynamic modifier\s+([A-Za-z0-9_]+)")
SOURCE_PATH = re.compile(r"(?:file:\s*[\"']|\b)(common/[^: \"']+|interface/[^: \"']+|gfx/[^: \"']+)")


def summarize(text: str) -> str:
    lines = text.splitlines()
    counter = Counter()
    names = Counter()
    source_files = Counter()

    for line in lines:
        for category, regex in ISSUES.items():
            if re.search(regex, line, re.IGNORECASE):
                counter[category] += 1
        match = MODIFIER_NAME.search(line)
        if match:
            names[match[1]] += 1
        match = SOURCE_PATH.search(line)
        if match:
            source_files[match[1]] += 1

    output = [
        "# TOWE error-log comparison",
        "",
        f"Log entries: {len(lines):,}",
        f"Distinct missing dynamic modifiers: {len(names):,}",
        "",
        "## Categories",
        "",
        "| Error pattern | Occurrences |",
        "|---|---:|",
    ]
    for name, _ in ISSUES.items():
        output.append(f"| {name} | {counter[name]:,} |")
    output.extend(["", "## Most frequent missing dynamic modifiers", ""])
    for name, count in names.most_common(15):
        output.append(f"- `{name}`: {count}")
    output.extend(["", "## Most frequently referenced source paths", ""])
    for name, count in source_files.most_common(15):
        output.append(f"- `{name}`: {count}")
    output.extend([
        "",
        "These are log-message counts, not unique engine defects. Compare logs",
        "captured using the same HOI4 build, DLC set, mod list, and game steps.",
    ])
    return "\n".join(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    args = parser.parse_args()
    print(summarize(args.log.read_text(encoding="utf-8-sig", errors="replace")))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Structural guardrails for the first TOWE 1905 reconstruction milestone.

Run from anywhere: python3 tools/validate_rebuild_foundation.py
This does not replace testing the actual game executable.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# An inherited vanilla definition is preferable to an incompatible copy of a
# full screen from another Hearts of Iron IV version. Rebuild each screen as a
# separately tested TOWE component before allowing these paths back.
QUARANTINED_OVERRIDES = (
    "interface/TNO_SG_Diplomacy.gui",
    "interface/TNO_SG_Politics.gui",
    "interface/countrydiplomacyview.gui",
    "interface/countrydiplomacyview.gfx",
    "interface/countryintelledger.gui",
    "interface/countrypoliticsview.gui",
    "interface/frontendgamesetupview.gui",
    "interface/towe_hide_vanilla_political.gui",
    "interface/towe_political_overrides.gui",
    "common/scripted_guis/zz_towe_tno_diplomacy.txt",
    "common/scripted_guis/zz_towe_tno_politics.txt",
    "common/scripted_guis/towe_political_scripted_gui.txt",
)

# The names below belong to HOI4's own views. A mod-side replacement needs an
# explicit, engine-version-matched review before it can be merged.
NATIVE_VIEWS = {
    "countrypoliticsview",
    "countrydiplomacyview",
    "country_intel_ledger_view",
    "frontendgamesetupview",
}


def unquoted_comments(source: str) -> str:
    """Remove Clausewitz '#' comments without removing quoted '#' text."""
    result = []
    for line in source.splitlines():
        quoted = False
        escaped = False
        kept = []
        for char in line:
            if char == '"' and not escaped:
                quoted = not quoted
            if char == "#" and not quoted:
                break
            kept.append(char)
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
        result.append("".join(kept))
    return "\n".join(result)


def named_block(source: str, name: str) -> str:
    """Find a named Clausewitz block, balancing its braces."""
    match = re.search(r"(?m)^\s*" + re.escape(name) + r"\s*=\s*\{", source)
    if not match:
        return ""
    start = source.find("{", match.start())
    depth = 0
    for offset in range(start, len(source)):
        if source[offset] == "{":
            depth += 1
        elif source[offset] == "}":
            depth -= 1
            if depth == 0:
                return source[start + 1 : offset]
    return ""


def validate() -> list[str]:
    failures: list[str] = []
    for path in QUARANTINED_OVERRIDES:
        if (ROOT / path).exists():
            failures.append(f"Legacy full-screen override remains active: {path}")

    name_pattern = re.compile(
        r"\bname\s*=\s*\"?(" + "|".join(sorted(NATIVE_VIEWS)) + r")\"?(?!\w)"
    )
    for path in sorted((ROOT / "interface").glob("*.gui")):
        source = unquoted_comments(path.read_text(encoding="utf-8-sig"))
        for match in name_pattern.finditer(source):
            failures.append(f"Native HOI4 view redeclared in {path.relative_to(ROOT)}: {match[1]}")

    for path in (ROOT / "common/scripted_guis").glob("*.txt"):
        source = unquoted_comments(path.read_text(encoding="utf-8-sig"))
        # A scripted overlay that is always visible defeats the purpose of
        # restoring an unmodified native Politics/Diplomacy screen.
        if re.search(r"parent_window_token\s*=\s*(politics_tab|selected_country_view_diplomacy)", source):
            if re.search(r"visible\s*=\s*\{\s*always\s*=\s*yes\s*\}", source):
                failures.append(f"Always-visible native screen overlay: {path.relative_to(ROOT)}")

    panel_path = ROOT / "common/scripted_guis/towe_custom_panel.txt"
    if not panel_path.is_file():
        failures.append("Protected Throne scripted GUI is missing")
    else:
        source = unquoted_comments(panel_path.read_text(encoding="utf-8-sig"))
        for widget in ("towe_throne_button_gui", "towe_throne_info_gui"):
            widget_source = named_block(source, widget)
            visible_source = named_block(widget_source, "visible")
            if not re.search(r"\bhas_country_flag\s*=\s*towe_throne_ui_enabled\b", visible_source):
                failures.append(f"Throne component is not explicitly gated: {widget}")

    if not (ROOT / "interface/towe_custom_political_panel.gui").is_file():
        failures.append("Protected Throne GUI definition is missing")
    bookmarks = list((ROOT / "common/bookmarks").glob("*.txt"))
    if not any("1905.12.1" in p.read_text(encoding="utf-8-sig") for p in bookmarks):
        failures.append("1905 campaign bookmark missing")
    for tag in ("JAS", "FUD"):
        if not list((ROOT / "history/countries").glob(f"{tag} -*.txt")):
            failures.append(f"Preserved 1905 country missing: {tag}")

    return failures


if __name__ == "__main__":
    problems = validate()
    if problems:
        for problem in problems:
            print("FAIL:", problem)
        sys.exit(1)
    print("PASS: vanilla GUI baseline, dormant Throne, and 1905 content guardrails")

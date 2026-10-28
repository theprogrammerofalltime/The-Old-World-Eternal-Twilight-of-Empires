#!/usr/bin/env python3
"""Static validation for TOWE source. This does not run Hearts of Iron IV."""
from __future__ import annotations
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []
warnings: list[str] = []

def check_braces(path: Path) -> None:
    depth = 0
    in_string = False
    escaped = False
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig", errors="replace").splitlines(), 1):
        for char in line:
            if char == "#" and not in_string:
                break
            if char == '"' and not escaped:
                in_string = not in_string
            elif not in_string:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth < 0:
                        errors.append(f"{path.relative_to(ROOT)}:{line_number}: extra closing brace")
                        return
            if char == "\\" and not escaped:
                escaped = True
            else:
                escaped = False
    if depth != 0 or in_string:
        errors.append(f"{path.relative_to(ROOT)}: unmatched braces or quotes")

def check_sprite_assets() -> None:
    sprites: dict[str, str] = {}
    for path in (ROOT / "interface").glob("*.gfx"):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for value in re.findall(r'(?im)^\s*texturefile\s*=\s*"([^"]+)"', text):
            item = value.replace("\\", "/").lstrip("/")
            if ("/towe_" in item.lower() or "/socdevicons/" in item.lower()) and not (ROOT / item).is_file():
                errors.append(f"{path.relative_to(ROOT)}: missing artwork {item}")
        # A sprite definition must not be duplicated in multiple GFX files.
        for match in re.finditer(r'(?im)^\s*name\s*=\s*["\']?(GFX_[A-Za-z0-9_]+)', text):
            key = match.group(1)
            previous = sprites.get(key)
            if previous is not None:
                errors.append(f"sprite {key} declared in both {previous} and {path.relative_to(ROOT)}")
            else:
                sprites[key] = str(path.relative_to(ROOT))

def check_idea_slots() -> None:
    path = ROOT / "common/idea_tags/zz_towe_idea_tags.txt"
    if not path.exists():
        errors.append("missing TOWE law-slot registration")
        return
    contents = path.read_text(encoding="utf-8-sig")
    slots = re.findall(r'(?m)^\s*slot\s*=\s*(towe_[A-Za-z0-9_]+)', contents)
    if len(slots) != 40 or len(set(slots)) != 40:
        errors.append(f"expected 40 distinct TOWE law/development slots, found {len(set(slots))}")
    all_ideas = "\n".join(
        f.read_text(encoding="utf-8-sig", errors="replace")
        for f in (ROOT / "common/ideas").glob("TOWE_zz_*.txt")
    )
    for slot in slots:
        if not re.search(r"(?m)^\s*" + re.escape(slot) + r"\s*=\s*\{", all_ideas):
            errors.append(f"idea category slot has no definition: {slot}")


def check_native_gui_fallback() -> None:
    """Guard against reactivating incompatible layered screen replacements."""
    disabled = {
        "interface/TOWE_SG_Politics.gui": "guiTypes",
        "interface/TOWE_SG_Diplomacy.gui": "guiTypes",
        "interface/towe_hide_vanilla_political.gui": "guiTypes",
        "interface/towe_political_overrides.gui": "guiTypes",
        "common/scripted_guis/zz_towe_politics.txt": "scripted_gui",
        "common/scripted_guis/zz_towe_diplomacy.txt": "scripted_gui",
        "common/scripted_guis/towe_political_scripted_gui.txt": "scripted_gui",
    }
    for name, root_key in disabled.items():
        path = ROOT / name
        if not path.is_file():
            errors.append(f"missing GUI fallback file: {name}")
            continue
        contents = path.read_text(encoding="utf-8-sig")
        contents = re.sub(r"(?m)#.*$", "", contents)
        if re.sub(r"\s+", "", contents) != f"{root_key}={{}}":
            errors.append(f"conflicting GUI override has been re-enabled: {name}")

    # These partial overrides must be absent so HOI4 loads its current native definitions.
    for name in ("interface/countryintelledger.gui", "interface/countrydiplomacyview.gfx"):
        if (ROOT / name).exists():
            errors.append(f"obsolete engine GUI override has returned: {name}")

    throne = ROOT / "common/scripted_guis/towe_custom_panel.txt"
    if not throne.exists():
        errors.append("missing protected Throne panel controller")
        return
    text = throne.read_text(encoding="utf-8-sig")
    if text.count("has_country_flag = towe_throne_ui_enabled") < 2:
        errors.append("Throne GUI button and panel must remain hidden by default")
    if "towe_throne_toggle_click" not in text or "towe_throne_close_click" not in text:
        errors.append("protected Throne panel toggle/close functionality is missing")


def check_focus_tree_targets() -> None:
    """Reject switches to focus trees that are not part of this mod."""
    definitions: set[str] = set()
    for path in (ROOT / "common/national_focus").glob("*.txt"):
        contents = path.read_text(encoding="utf-8-sig")
        definitions.update(re.findall(
            r"focus_tree\s*=\s*\{\s*id\s*=\s*(\w+)", contents
        ))
    to_check = [
        *(ROOT / "common/on_actions").glob("*.txt"),
        *(ROOT / "common/decisions").rglob("*.txt"),
        *(ROOT / "events").glob("*.txt"),
        *(ROOT / "history/countries").glob("*.txt"),
    ]
    for path in to_check:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for target in re.findall(r"(?m)^\s*load_focus_tree\s*=\s*(\w+)", text):
            if target not in definitions:
                errors.append(
                    f"{path.relative_to(ROOT)}: focus tree '{target}' is not defined"
                )


def check_october_error_log_regressions() -> None:
    """Guard known source-level faults from the 2026-10-28 19:48 game log."""
    opinion = ROOT / "common/opinion_modifiers/towe_great_game_opinion_modifiers.txt"
    if not opinion.is_file() or not re.search(
        r"(?m)^\s*opinion_modifiers\s*=\s*\{", opinion.read_text(encoding="utf-8-sig")
    ):
        errors.append("Great Game opinion modifiers require an opinion_modifiers root block")

    for path in [
        ROOT / "common/decisions/towe_great_game_decisions.txt",
        *(ROOT / "events").glob("*.txt"),
    ]:
        content = path.read_text(encoding="utf-8-sig", errors="replace")
        if re.search(r"(?m)^\s*exists\s*=\s*[A-Z]{3}\b", content):
            errors.append(f"{path.relative_to(ROOT)}: exists requires yes/no in a country scope")

    generic = ROOT / "common/national_focus/the_old_world_eternal_generic_basic.txt"
    if not generic.is_file() or "default = yes" in generic.read_text(encoding="utf-8-sig"):
        errors.append("TOWE generic focus tree must not compete with vanilla default")

    names = ROOT / "common/names/00_towe_scenario_names.txt"
    tagfile = ROOT / "common/country_tags/zyy_the_old_world_eternal_countries.txt"
    if not names.is_file():
        errors.append("TOWE scenario country character name pools are missing")
    else:
        defined = set(re.findall(r"(?m)^([A-Z]{3})\s*=\s*\{", names.read_text(encoding="utf-8-sig")))
        active_tags = set(re.findall(r'(?m)^([A-Z]{3})\s*=\s*"', tagfile.read_text(encoding="utf-8-sig")))
        for tag in sorted(active_tags - defined):
            errors.append(f"playable country {tag} has no random-character name pool")

    indices = ROOT / "common/modifier_definitions/towe_economic_society_indices.txt"
    if not indices.is_file():
        errors.append("TOWE economy and society modifier definitions are missing")
    else:
        ids = re.findall(r"(?m)^([A-Za-z_][A-Za-z_0-9]*)\s*=\s*\{", indices.read_text(encoding="utf-8-sig"))
        if len(ids) != len(set(ids)) or len(ids) < 164:
            errors.append("TOWE economy modifier index definitions missing or duplicated")

def main() -> int:
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix()
        if "tno" in relative.lower():
            errors.append(f"legacy branded filename remains: {relative}")
        if path.suffix.lower() in {".txt", ".gui", ".gfx", ".yml", ".lua"} and (
            relative.startswith(("common/", "interface/", "events/", "localisation/", "history/countries/"))
        ):
            if "tno" in path.read_text(encoding="utf-8-sig", errors="replace").lower():
                errors.append(f"legacy TNO identifier or branding remains in: {relative}")
        if path.suffix.lower() in {".txt", ".gfx", ".gui"} and (
            relative.startswith(("common/", "events/", "interface/", "history/countries/", "history/units/"))
        ):
            check_braces(path)
    check_idea_slots()
    check_sprite_assets()
    check_native_gui_fallback()
    check_focus_tree_targets()
    check_october_error_log_regressions()
    for warning in warnings:
        print("WARNING:", warning)
    for error in errors:
        print("ERROR:", error)
    if errors:
        print(f"Static validation failed: {len(errors)} errors. HOI4 launch is still required.")
        return 1
    print("TOWE static validation passed. This is NOT an in-game test.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

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

def main() -> int:
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix()
        if "tno" in relative.lower():
            errors.append(f"legacy branded filename remains: {relative}")
        if path.suffix.lower() in {".txt", ".gfx", ".gui"} and (
            relative.startswith(("common/", "events/", "interface/", "history/countries/", "history/units/"))
        ):
            check_braces(path)
    check_idea_slots()
    check_sprite_assets()
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

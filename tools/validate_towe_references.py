#!/usr/bin/env python3
"""Cross-check TOWE-owned starting ideas, source references, and policy hooks.

Static-only lint. This intentionally does not flag third-party or vanilla IDs.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent


def strings(path):
    return path.read_text(encoding="utf-8-sig", errors="replace")


def blocks(text, key):
    pattern = re.compile(r"(?m)\\b" + re.escape(key) + r"\\s*=\\s*\\{")
    for match in pattern.finditer(text):
        opening = text.find("{", match.start())
        level = 0
        in_quote = False
        escaped = False
        for i in range(opening, len(text)):
            char = text[i]
            if char == '"' and not escaped:
                in_quote = not in_quote
            elif not in_quote:
                if char == "{":
                    level += 1
                elif char == "}":
                    level -= 1
                    if level == 0:
                        yield text[opening + 1:i]
                        break
            escaped = char == "\\\\" and not escaped


def main():
    problems = []
    idea_files = sorted((ROOT / "common/ideas").glob("*.txt"))
    definitions = set()
    for path in idea_files:
        txt = strings(path)
        definitions.update(re.findall(r"(?m)^\\s*(towe_[A-Za-z_0-9]+)\\s*=\\s*\\{", txt, re.IGNORECASE))

    for path in sorted((ROOT / "history/countries").glob("*.txt")):
        txt = strings(path)
        for block in blocks(txt, "add_ideas"):
            # Scalar tokens, not assignments.
            for name in re.findall(r"(?<![A-Za-z_0-9])(towe_[A-Za-z_0-9]+)(?![A-Za-z_0-9])", block, re.IGNORECASE):
                if name not in definitions:
                    problems.append(f"{path.relative_to(ROOT)}: missing idea {name}")

    # The social-law helpers are expected to be defined and actually called.
    helper_file = ROOT / "common/scripted_effects/zz_towe_law_stubs.txt"
    helpers = set(re.findall(r"(?m)^(towe_[a-z0-9_]+_effect)\\s*=\\s*\\{", strings(helper_file)))
    laws_path = ROOT / "common/ideas/TOWE_zz_laws_misc.txt"
    laws = strings(laws_path)
    for helper in sorted(helpers):
        if not re.search(r"(?m)^\\s*" + re.escape(helper) + r"\\s*=\\s*yes", laws):
            # Only an unavailable refugee art-dependent variant may be absent.
            if helper != "towe_refugees_give_me_your_poor_effect":
                problems.append(f"{laws_path.relative_to(ROOT)}: helper never called: {helper}")

    for p in problems:
        print("ERROR:", p)
    if problems:
        print(f"Found {len(problems)} TOWE identifier mismatches.")
        return 1
    print("TOWE custom idea and helper references passed static checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

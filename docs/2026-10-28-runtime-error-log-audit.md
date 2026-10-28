# TOWE — 28 October 2026 runtime error-log repair pass

Source: user's 19:48–19:49 `error.log` extract, **3,787 lines**, reaches **1905.12.01.12**.
Repository: `theprogrammerofalltime/The-Old-World-Eternal-Twilight-of-Empires`.
Changes are in the **draft** repair PR, not the `main` branch.

## Repairs applied following this log

| Engine symptom | Source correction |
| --- | --- |
| `Undefined GUI_TYPE: country_intel_ledger_view` | Removed the empty, stale `interface/countryintelledger.gui` override; the game's own file can load again |
| `GFX_diplo_flag_frame` missing | Removed the imported `interface/countrydiplomacyview.gfx` override so the current native sprite atlas loads |
| Unexpected `towe_great_game_outreach` token | Added the required `opinion_modifiers = { ... }` root |
| Invalid `exists = PLC/AZT/FUD/GAU` in Great Game and other events | Replaced 14 instances with target country scopes and `exists = yes` |
| Invalid `independence_war` war-goal type | Uses a supported `annex_everything` type as a temporary engine-compatible fallback. **Review the rebel peace outcome before release.** |
| `FUD_strike_south` missing focus icon | Switched to an existing major-war icon |
| Duplicate Monroe Doctrine idea definitions | Removed the duplicate mod-side declarations; vanilla originals remain |
| 949 recurring default-tree conflict warnings | TOWE generic tree is selectable but no longer another `default = yes` tree |
| 818 unknown/invalid modifier errors, 166 distinct IDs | Registered **164** TOWE economic/social modifier indices in `common/modifier_definitions`; omitted two unrelated/special cases. This addresses the parser errors but **not** every intended economic interaction automatically |
| Social development had no GDP integration | The monthly TOWE GDP script now reads its registered growth and consumer-goods indices |
| Repeated missing names for TOWE random characters | Added first-name/surname pools for all 36 active scenario countries in `common/names` |
| Localisation key collision warning | Audited 6,384 unique English keys, removed **42 duplicate keys**, retained the explicit Jasmine party override; CI fails if duplicate keys recur |

## Remaining, not confirmed fixed

- The log includes **hundreds of vanilla/DLC Turkish, Soviet, Polish and Bulgarian scripted references** to dynamic modifiers absent in the running setup. These reference `TUR_scripted_effects.txt`, `SOV_scripted_effects.txt`, etc. which are **not files from this TOWE repository**. Do not insert meaningless dummy modifiers just to suppress their errors. Determine whether they originate from game-version/DLC mismatches or other installed mods.
- `D01`–`D75` dynamic-tag flag warnings: no suitable authentic flag assets exist in the repo; avoid assigning a real TOWE nation's flag to a placeholder simply to make warnings disappear.
- `gfx/train_gfx_database/NSB_generic.txt` and equipment entity errors refer to engine/vanilla sources absent from the repository.
- `mod/ugc_*.mod` malformed Workshop descriptor lines and missing music DLC come from local game/mod installation, not this repository.
- In-game appearance, runtime speed, economics, GUI interactions and error-count reduction **remain unverified** until a new game run with the updated branch.
- The imported economy contains country-specific modifiers whose logic may not match the 1905 TOWE world. Registering a custom numeric modifier allows scripts to parse and query its value; it does not, by itself, recreate an autonomous financial simulation.
- Review the temporary rebellion war-goal choice against the intended narrative outcome.

## Validation and reproducibility

On the repair branch, GitHub Actions executes:

1. `python3 tools/validate_towe_static.py`
2. `python3 tools/validate_towe_references.py`
3. `python3 tools/audit_ideology_usage.py`
4. `python3 tools/audit_towe_localisation.py`

These are **static checks**, not a HOI4 launch.

To produce a useful new log: install the repair branch as its **own** mod (do not use the Workshop copy), disable all other mods, clear the old `logs/error.log`, launch the **1905** bookmark, inspect Politics and Diplomacy as the Jasmine Empire, advance at least one month, and attach the complete fresh `error.log`. Please also attach `text.log` and `system.log` if visual or localisation problems remain.

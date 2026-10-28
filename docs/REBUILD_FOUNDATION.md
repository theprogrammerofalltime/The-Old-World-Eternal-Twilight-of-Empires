# The Old World Eternal: Twilight of Empires
## Reconstruction programme — clean foundation (Milestone R0)

**Date:** 28 October 2026  
**Branch:** `rebuild/1905-clean-foundation-2026-10-28`  
**Status:** Source-level reconstruction, **not yet verified in Hearts of Iron IV**

### Why this branch is independent

The previous draft repair PR attempted to rehabilitate a large collection of
imported UI and gameplay systems simultaneously. The subsequent screenshots
and logs still showed incompatible GUI definitions and cascading errors.
This branch instead starts directly from `main`, without merging PR #1.
It is a separate, reversible replacement strategy; both original branches
remain available for reference.

### Milestone R0: recover a usable interface baseline

The following obsolete **full-screen or always-visible UI overrides** have
been removed *from this branch only*:

- Full copies of Politics, Diplomacy, Intel Ledger and country-selection GUI.
- The legacy foreign-source Politics and Diplomacy popup layouts and mounts.
- Overrides that moved vanilla political tabs off-screen and disabled
  interaction with them.
- The incompatible diplomacy sprite override associated with a missing flag
  frame; let the installed game provide its own definition.

This is a **temporary vanilla UI fallback**, not the finished TOWE interface.
It sacrifices custom layouts for now so individual TOWE-native panels can
be rebuilt against a known HOI4 version and tested one at a time.

The Throne panel definition and click behavior remain in source, but its
button **and** floating window now require the country flag
`towe_throne_ui_enabled`. No default code sets this flag. Preserve this
feature for a later isolated, visible UI test.

### Preserved game foundations

- The 1 December 1905 scenario and country history, including Jasmine and Fu.
- Map, state and country files, focus trees, ideologies and existing diplomacy.
- Protected on-action and scripted infrastructure unrelated to deleted mounts.
- Asset files not proved safe to remove; subsequent milestones will audit
  stale images and sprites instead of deleting them blindly.

### Evidence from the 20:19–20:20 runtime log

The supplied log has **1,939 entries**. It includes:

- `Undefined GUI_TYPE: country_intel_ledger_view` and a missing
  `GFX_diplo_flag_frame` near the first day of gameplay.
- **1,005** messages referring to **75 distinct** invalid dynamic-modifier
  identifiers. These are **not fixed by R0**.
- Invalid modifiers in legacy Russia/Ukraine definitions and a malformed
  train graphics database.
- 31 installed-mod descriptor version warnings. These refer to the user's
  launcher and other Workshop entries, not necessarily this repository.

No one should interpret disappearing errors from a removed UI screen as
proof that the remaining gameplay mechanisms are functioning.

### Static checks

```sh
python3 tools/validate_rebuild_foundation.py
python3 tools/summarize_rebuild_log.py /path/to/error.log
```

The first command fails if an unreviewed native GUI replacement, always-on
Politics/Diplomacy mount, or unguarded Throne control is reintroduced. It
also checks that the 1905 bookmark and named JAS/FUD histories remain.
GitHub Actions runs this guard on rebuild-branch changes.
The second command reports error categories and frequent identifiers without
altering the log.

### Required HOI4 acceptance run before merge

1. Install this branch as a **separate local mod**, with a distinct launcher
   descriptor; do not overwrite the Workshop mod or enable both copies.
2. Disable other UI-changing mods and record the exact HOI4 build and DLC set.
3. Launch the 1905 bookmark and select JAS, then FUD.
4. Verify Politics, Diplomacy, Intel Ledger and country-selection screens:
   no blank modal pane, duplicate head of state, missing sprite or crash.
5. Resume through at least 1 January 1906; save/reload once.
6. Upload the *new* error.log and screenshots; compare it to this log with
   `tools/summarize_rebuild_log.py`.

**R0 is not an in-game-tested fix.** The error log must come from precisely
this reconstruction branch for conclusions about it to be valid.

### Planned independent reconstruction milestones

| Milestone | Workstream | Release gate |
|---|---|---|
| R0 | Safe native GUI fallback, guardrails, logging | Four views render and save/load correctly |
| R1 | Country/ideology and imported-script audit | 1905 scenario starts without critical script errors |
| R2 | TOWE-native economic model (GDP, debt, budgets) | Monthly values are calculated, localized and tested |
| R3 | Original geopolitics and Great Game rivalry | Influence, escalation and de-escalation decisions work |
| R4 | Custom economic/political UI panels | No native-widget override or overlapping geometry |
| R5 | Focuses, events and narrative integration | Full test paths complete with accurate localisation |
| R6 | Packaging, compatibility and regression tests | Repeatable clean installation and documented limits |

Each milestone should modify the smallest viable subsystem and stay in a
separate commit or reviewable follow-up PR. **Do not merge R0 until its
actual game UI has been verified**.

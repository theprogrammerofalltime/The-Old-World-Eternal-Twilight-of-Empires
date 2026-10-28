#!/usr/bin/env python3
"""Recolour the TNO-style UI textures to a dark green theme.

The ported TNO interface art is a mix of teal-black panels, warm grey frames
and a few stray bright-green line-art sheets. This script pulls all of that
chrome onto one dark emerald palette while keeping the original brightness
(so bevels, shadows and glows still read the same).

It only touches uncompressed 32-bit BGRA .dds files in the UI folders listed
in INCLUDE_DIRS, and it leaves semantic colours alone (red/orange alerts,
bright yellow warnings, vivid "good" greens, near-white text).

The transform is idempotent: running it twice gives the same result.

Usage (from the mod root):
    python3 tools/recolor_dark_green.py            # recolour in place
    python3 tools/recolor_dark_green.py --dry-run  # just list what would change
    python3 tools/recolor_dark_green.py --hue 150  # nudge the green hue

Needs: numpy
"""
import argparse
import os
import struct
import sys

import numpy as np

# UI chrome folders (relative to the mod root). Art folders such as anarchy,
# flags, leaders, SocDevIcons and factions are deliberately NOT listed.
INCLUDE_DIRS = [
    "gfx/interface",
    "gfx/interface/autonomy",
    "gfx/interface/buttons",
    "gfx/interface/diploview",
    "gfx/interface/hmb_dual_leader",
    "gfx/interface/intel_ledger",
    "gfx/interface/occupation",
    "gfx/interface/tiles",
    "gfx/interface/topbar",
]

DEFAULT_HUE = 146.0     # degrees; emerald, leaning slightly towards teal
MAX_SAT = 0.60          # never go more saturated than this


def read_dds(path):
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:4] != b"DDS ":
        return None
    pf_flags = struct.unpack_from("<I", data, 80)[0]
    bits = struct.unpack_from("<I", data, 88)[0]
    masks = struct.unpack_from("<IIII", data, 92)
    if pf_flags & 4 or bits != 32:           # compressed or not 32-bit
        return None
    if masks != (0xFF0000, 0xFF00, 0xFF, 0xFF000000):  # BGRA only
        return None
    return data


def smooth_sat_target(v):
    """Wanted saturation for a given brightness: rich in the darks, sage in the mids."""
    return 0.12 + 0.40 * np.exp(-((v / 0.30) ** 2))


def hsv_to_rgb(h, s, v):
    h6 = (h % 360.0) / 60.0
    i = np.floor(h6).astype(np.int32) % 6
    f = h6 - np.floor(h6)
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return r, g, b


def recolor_pixels(bgra, target_hue):
    """bgra: (N, 4) uint8 array. Returns a new (N, 4) uint8 array."""
    px = bgra.astype(np.float32) / 255.0
    b, g, r, a = px[:, 0], px[:, 1], px[:, 2], px[:, 3]

    v = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    d = v - mn
    s = np.where(v > 0, d / np.maximum(v, 1e-6), 0.0)

    # hue in degrees
    dd = np.maximum(d, 1e-6)
    hue = np.where(v == r, ((g - b) / dd) % 6,
          np.where(v == g, (b - r) / dd + 2, (r - g) / dd + 4)) * 60.0
    hue = np.where(d < 1e-6, 0.0, hue)

    luma = 0.2126 * r + 0.7152 * g + 0.0722 * b

    # --- pixels we leave alone -------------------------------------------
    red_alert = ((hue < 28) | (hue >= 335)) & (s > 0.35)
    bright_yellow = (hue >= 28) & (hue < 75) & (s > 0.55) & (v > 0.5)
    vivid_green = (hue >= 75) & (hue < 165) & (s > 0.62) & (v > 0.5)
    white_text = (v > 0.88) & (s < 0.12)
    transparent = a <= 0.0
    keep = red_alert | bright_yellow | vivid_green | white_text | transparent

    # --- recolour everything else ----------------------------------------
    s_new = np.minimum(np.maximum(s, smooth_sat_target(v)), MAX_SAT)
    nr, ng, nb = hsv_to_rgb(np.full_like(v, target_hue), s_new, v)

    # keep the original perceived brightness
    new_luma = 0.2126 * nr + 0.7152 * ng + 0.0722 * nb
    scale = np.where(new_luma > 1e-4, luma / np.maximum(new_luma, 1e-4), 1.0)
    nr, ng, nb = (np.clip(c * scale, 0, 1) for c in (nr, ng, nb))

    out = px.copy()
    out[:, 2] = np.where(keep, r, nr)
    out[:, 1] = np.where(keep, g, ng)
    out[:, 0] = np.where(keep, b, nb)
    return np.clip(np.rint(out * 255.0), 0, 255).astype(np.uint8)


def process(path, target_hue, dry_run):
    data = read_dds(path)
    if data is None:
        return "skipped (not raw 32-bit BGRA DDS)"
    header, body = data[:128], data[128:]
    if len(body) % 4:
        return "skipped (odd data size)"
    px = np.frombuffer(body, dtype=np.uint8).reshape(-1, 4)
    new = recolor_pixels(px, target_hue)
    if np.array_equal(new, px):
        return "unchanged"
    if not dry_run:
        with open(path, "wb") as fh:
            fh.write(header + new.tobytes())
    return "recoloured"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--hue", type=float, default=DEFAULT_HUE, help="target green hue in degrees (default %(default)s)")
    ap.add_argument("--root", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    counts = {}
    for rel in INCLUDE_DIRS:
        folder = os.path.join(root, rel)
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if not name.lower().endswith(".dds"):
                continue
            result = process(os.path.join(folder, name), args.hue, args.dry_run)
            counts[result] = counts.get(result, 0) + 1
            if result == "recoloured":
                print(f"{'would recolour' if args.dry_run else 'recoloured'}: {rel}/{name}")
    print()
    for k, v in sorted(counts.items()):
        print(f"{v:4d}  {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

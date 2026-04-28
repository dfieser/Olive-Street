"""
generate_logo.py
----------------
Generate Olive Street band logos as clean SVG files using pure Python code.
No AI, no image APIs — every element is drawn programmatically with svgwrite.

Styles:
  wordmark  — Horizontal band name between two ruled lines with accent dots
  stacked   — Two-line layout with a diamond-center decorative divider
  emblem    — Band name in a double-border rectangular frame with corner marks
  badge     — Circular stamp with concentric rings and tick marks
  block     — High-contrast split block with reversed-out band name

Color schemes:
  dark      — Olive Green (#6B7A3A) background, Cream text, Tan accents
  light     — Cream (#F5F0E1) background, Olive Green text, Tan accents
  tan       — Tan (#DDB892) background, Olive Green text, Cream accents
  mono      — Near-black background, Cream text (legibility test)

Usage:
  python scripts/generate_logo.py --style wordmark
  python scripts/generate_logo.py --style emblem --scheme light
  python scripts/generate_logo.py --all
  python scripts/generate_logo.py --style badge --scheme tan --png
  python scripts/generate_logo.py --name "MY BAND" --style wordmark

Requires:
  pip install svgwrite
  pip install cairosvg   (optional — only needed for --png export)
"""

import argparse
import json
import math
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    import svgwrite
except ImportError:
    sys.exit("Run: pip install svgwrite")

# ─── Band identity ────────────────────────────────────────────────────────────

BAND_NAME = "OLIVE STREET BAND"
OUTPUT_DIR = ROOT / "output" / "profiles"

# ─── Color schemes (sourced from criteria/color_palette.json) ─────────────────
# Palette: Olive Green #6B7A3A | Tan #DDB892 | Cream #F5F0E1

COLOR_SCHEMES: dict[str, dict] = {
    # Dark: olive bg, cream + tan elements  (primary profile image scheme)
    "dark": {
        "background": "#6B7A3A",
        "primary":    "#F5F0E1",
        "accent":     "#DDB892",
        "secondary":  "#DDB892",
    },
    # Light: cream bg, olive text  (reversed / light version)
    "light": {
        "background": "#F5F0E1",
        "primary":    "#6B7A3A",
        "accent":     "#DDB892",
        "secondary":  "#6B7A3A",
    },
    # Tan: tan bg, olive text, cream accents
    "tan": {
        "background": "#DDB892",
        "primary":    "#6B7A3A",
        "accent":     "#F5F0E1",
        "secondary":  "#6B7A3A",
    },
    # Mono: near-black bg, cream text  (single-color legibility test)
    "mono": {
        "background": "#1A1A1A",
        "primary":    "#F5F0E1",
        "accent":     "#F5F0E1",
        "secondary":  "#DDB892",
    },
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _out_path(style: str, scheme: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return OUTPUT_DIR / f"{ts}_logo_{style}_{scheme}.svg"


def _base(dwg: svgwrite.Drawing, c: dict, w: float, h: float) -> None:
    """Fill background."""
    dwg.add(dwg.rect((0, 0), (w, h), fill=c["background"]))


def _ensure_halftone(dwg: svgwrite.Drawing, color: str, tile: int = 18,
                      dot_r: float = 1.2, opacity: float = 0.13) -> str:
    """Tiled circular halftone pattern. Returns paint ref."""
    cid = color.lstrip("#")
    pid = f"halftone_{cid}_{tile}_{int(dot_r*10)}_{int(opacity*100)}"
    if pid not in getattr(dwg, "_halftone_ids", set()):
        p = dwg.defs.add(dwg.pattern(
            id=pid, insert=(0, 0), size=(tile, tile),
            patternUnits="userSpaceOnUse",
        ))
        p.add(dwg.circle(center=(tile / 2, tile / 2), r=dot_r,
                         fill=color, fill_opacity=opacity))
        dwg._halftone_ids = getattr(dwg, "_halftone_ids", set()) | {pid}
    return f"url(#{pid})"


def _wash(dwg: svgwrite.Drawing, c: dict, w: float, h: float) -> None:
    """Subtle halftone wash applied over the base fill for printed-paper feel."""
    dwg.add(dwg.rect((0, 0), (w, h),
                     fill=_ensure_halftone(dwg, c["primary"])))


def _diamond(dwg: svgwrite.Drawing, x: float, y: float, size: float,
             fill: str) -> "svgwrite.shapes.Polygon":
    return dwg.polygon(points=[(x, y - size), (x + size, y),
                                (x, y + size), (x - size, y)],
                       fill=fill)


# ─── Style: Wordmark ──────────────────────────────────────────────────────────

def draw_wordmark(dwg: svgwrite.Drawing, c: dict, w: float, h: float,
                  band: str, font: str) -> None:
    """
    Centered band name between two horizontal rules.
    Diamond ornaments anchor each rule end. Faint outer frame for depth.
    """
    cx, cy = w / 2, h / 2
    font_size = h * 0.20
    tracking = 6

    _base(dwg, c, w, h)
    _wash(dwg, c, w, h)

    # Faint outer frame
    dwg.add(dwg.rect(
        (w * 0.025, h * 0.08), (w * 0.95, h * 0.84),
        fill="none", stroke=c["secondary"],
        stroke_width=0.6, stroke_opacity=0.45,
    ))

    # Rules with diamond + dot end ornaments
    rule_margin = w * 0.07
    rule_y_top    = cy - font_size * 0.95
    rule_y_bottom = cy + font_size * 0.78
    for ry in (rule_y_top, rule_y_bottom):
        dwg.add(dwg.line(
            (rule_margin + 12, ry), (w - rule_margin - 12, ry),
            stroke=c["accent"], stroke_width=1.6,
        ))
        for dx in (rule_margin, w - rule_margin):
            dwg.add(_diamond(dwg, dx, ry, 5, c["accent"]))

    # Band name
    dwg.add(dwg.text(
        band,
        insert=(cx, cy),
        text_anchor="middle",
        dominant_baseline="middle",
        font_family=font,
        font_size=font_size,
        font_weight="bold",
        fill=c["primary"],
        letter_spacing=tracking,
    ))

    # EST · 2026 micro-mark sitting on top rule, centred
    dwg.add(dwg.rect((cx - 60, rule_y_top - 9), (120, 18),
                     fill=c["background"]))
    dwg.add(dwg.text(
        "EST · 2026",
        insert=(cx, rule_y_top + 1),
        text_anchor="middle", dominant_baseline="middle",
        font_family=font, font_size=12, font_weight="bold",
        fill=c["accent"], letter_spacing=2,
    ))


# ─── Style: Stacked ───────────────────────────────────────────────────────────

def draw_stacked(dwg: svgwrite.Drawing, c: dict, w: float, h: float,
                 band: str, font: str) -> None:
    """
    Three-line stack OLIVE / STREET / BAND with diamond-rule dividers.
    BAND is rendered in the accent colour as a punctuation chord.
    """
    words = band.split()
    if len(words) >= 3:
        l1, l2, l3 = words[0], words[1], " ".join(words[2:])
    elif len(words) == 2:
        l1, l2, l3 = words[0], words[1], ""
    else:
        l1, l2, l3 = band, "", ""

    cx = w / 2
    fs1 = h * 0.18      # OLIVE / STREET
    fs2 = h * 0.16      # BAND (slightly smaller as accent)

    y_top  = h * 0.30
    y_mid  = h * 0.50
    y_bot  = h * 0.78

    _base(dwg, c, w, h)
    _wash(dwg, c, w, h)

    # Two diamond-anchored rules between the lines
    rule_w = w * 0.62
    diamond = 5
    for div_y in ((y_top + y_mid) / 2, (y_mid + y_bot) / 2):
        x0 = cx - rule_w / 2
        x1 = cx + rule_w / 2
        for sx0, sx1 in ((x0, cx - diamond * 2),
                          (cx + diamond * 2, x1)):
            dwg.add(dwg.line((sx0, div_y), (sx1, div_y),
                             stroke=c["accent"], stroke_width=1.5))
        dwg.add(_diamond(dwg, cx, div_y, diamond, c["accent"]))

    # Three lines
    for txt, y, fs, fill in (
        (l1, y_top, fs1, c["primary"]),
        (l2, y_mid, fs1, c["primary"]),
        (l3, y_bot, fs2, c["accent"]),
    ):
        if not txt:
            continue
        dwg.add(dwg.text(
            txt, insert=(cx, y),
            text_anchor="middle", dominant_baseline="middle",
            font_family=font, font_size=fs, font_weight="bold",
            fill=fill, letter_spacing=fs * 0.10,
        ))

    # Faint outer frame
    dwg.add(dwg.rect((w * 0.05, h * 0.05), (w * 0.90, h * 0.90),
                     fill="none", stroke=c["secondary"],
                     stroke_width=0.6, stroke_opacity=0.45))


# ─── Style: Emblem ────────────────────────────────────────────────────────────

def draw_emblem(dwg: svgwrite.Drawing, c: dict, w: float, h: float,
                band: str, font: str) -> None:
    """
    Two-line band name in a double-border frame with L-cut corner ornaments.
      OLIVE STREET
      ─── BAND ───
    """
    cx, cy = w / 2, h / 2
    words = band.split()
    if len(words) >= 3:
        l1 = " ".join(words[:2])
        l2 = " ".join(words[2:])
    elif len(words) == 2:
        l1, l2 = words[0], words[1]
    else:
        l1, l2 = band, ""

    fs1 = h * 0.14
    fs2 = h * 0.11
    tracking1 = 4
    tracking2 = 8

    frame_mx, frame_my = w * 0.07, h * 0.10
    frame_w = w - frame_mx * 2
    frame_h = h - frame_my * 2
    inset = 8
    corner_len = 22

    _base(dwg, c, w, h)
    _wash(dwg, c, w, h)

    # Outer + inner borders
    dwg.add(dwg.rect((frame_mx, frame_my), (frame_w, frame_h),
                     fill="none", stroke=c["primary"], stroke_width=2))
    dwg.add(dwg.rect((frame_mx + inset, frame_my + inset),
                     (frame_w - inset * 2, frame_h - inset * 2),
                     fill="none", stroke=c["accent"], stroke_width=1))

    # Corner L-cut ornaments — punch through outer border, draw L in accent
    corners = [
        (frame_mx,           frame_my,           1,  1),
        (frame_mx + frame_w, frame_my,          -1,  1),
        (frame_mx,           frame_my + frame_h, 1, -1),
        (frame_mx + frame_w, frame_my + frame_h, -1, -1),
    ]
    for fx, fy, sx, sy in corners:
        dwg.add(dwg.line((fx - sx * corner_len, fy),
                         (fx + sx * corner_len, fy),
                         stroke=c["background"], stroke_width=5))
        dwg.add(dwg.line((fx, fy - sy * corner_len),
                         (fx, fy + sy * corner_len),
                         stroke=c["background"], stroke_width=5))
        dwg.add(dwg.line((fx - sx * corner_len, fy), (fx, fy),
                         stroke=c["accent"], stroke_width=2.5))
        dwg.add(dwg.line((fx, fy - sy * corner_len), (fx, fy),
                         stroke=c["accent"], stroke_width=2.5))
        dwg.add(dwg.circle(center=(fx, fy), r=3.5, fill=c["accent"]))

    # Top line — OLIVE STREET
    y1 = cy - fs1 * 0.2
    dwg.add(dwg.text(
        l1, insert=(cx, y1),
        text_anchor="middle", dominant_baseline="middle",
        font_family=font, font_size=fs1, font_weight="bold",
        fill=c["primary"], letter_spacing=tracking1,
    ))

    # Divider rule with diamond
    rule_y = y1 + fs1 * 0.85
    half_rule = w * 0.18
    for x0, x1 in ((cx - half_rule, cx - 14),
                   (cx + 14, cx + half_rule)):
        dwg.add(dwg.line((x0, rule_y), (x1, rule_y),
                         stroke=c["accent"], stroke_width=1.4))
    dwg.add(_diamond(dwg, cx, rule_y, 5, c["accent"]))

    # Bottom line — BAND
    y2 = rule_y + fs2 * 0.95
    if l2:
        dwg.add(dwg.text(
            l2, insert=(cx, y2),
            text_anchor="middle", dominant_baseline="middle",
            font_family=font, font_size=fs2, font_weight="bold",
            fill=c["accent"], letter_spacing=tracking2,
        ))

    # EST · 2026 micro-mark at bottom of frame
    dwg.add(dwg.text(
        "★ EST · 2026 ★",
        insert=(cx, frame_my + frame_h - 18),
        text_anchor="middle", dominant_baseline="middle",
        font_family=font, font_size=11,
        fill=c["secondary"], letter_spacing=2,
    ))


# ─── Style: Badge ─────────────────────────────────────────────────────────────

def draw_badge(dwg: svgwrite.Drawing, c: dict, w: float, h: float,
               band: str, font: str) -> None:
    """
    Circular stamp badge — three-line stack (OLIVE / STREET / BAND) with
    concentric rings, tick marks, and bracket diamonds at the cardinals.
    """
    cx, cy = w / 2, h / 2
    r_outer = min(w, h) * 0.46
    r_inner = r_outer * 0.82

    words = band.split()
    if len(words) >= 3:
        l1, l2, l3 = words[0], words[1], " ".join(words[2:])
    elif len(words) == 2:
        l1, l2, l3 = words[0], words[1], ""
    else:
        l1, l2, l3 = band, "", ""

    fs1 = r_inner * 0.26
    fs2 = r_inner * 0.22
    tracking = 4

    _base(dwg, c, w, h)
    _wash(dwg, c, w, h)

    # Solid centre disc keeps the type field clean
    dwg.add(dwg.circle(center=(cx, cy), r=r_inner * 0.99,
                       fill=c["background"]))

    # Outer ring + thin highlight ring just inside it
    dwg.add(dwg.circle(center=(cx, cy), r=r_outer,
                       fill="none", stroke=c["primary"], stroke_width=4))
    dwg.add(dwg.circle(center=(cx, cy), r=r_outer - 6,
                       fill="none", stroke=c["accent"],
                       stroke_width=1, stroke_opacity=0.6))
    # Inner ring
    dwg.add(dwg.circle(center=(cx, cy), r=r_inner,
                       fill="none", stroke=c["accent"], stroke_width=1.2))

    # Tick marks every 15°, majors at cardinals
    t_in  = r_outer - 12
    for i in range(24):
        deg = i * 15
        angle = math.radians(deg)
        major = (deg % 90 == 0)
        t_out = r_outer - (32 if major else 18)
        dwg.add(dwg.line(
            (cx + t_in  * math.cos(angle), cy + t_in  * math.sin(angle)),
            (cx + t_out * math.cos(angle), cy + t_out * math.sin(angle)),
            stroke=c["accent"],
            stroke_width=(2.4 if major else 1),
            stroke_opacity=(0.95 if major else 0.55),
        ))

    # Diamond ornaments at the cardinals (sit on the inner ring)
    for deg in (0, 90, 180, 270):
        angle = math.radians(deg)
        dx = cx + r_inner * math.cos(angle)
        dy = cy + r_inner * math.sin(angle)
        dwg.add(_diamond(dwg, dx, dy, 5, c["accent"]))

    # Three-line stack
    y1 = cy - fs1 * 1.05
    y2 = cy
    y3 = cy + fs1 * 1.05
    for txt, y, fs, fill in (
        (l1, y1, fs1, c["primary"]),
        (l2, y2, fs1, c["primary"]),
        (l3, y3, fs2, c["accent"]),
    ):
        if not txt:
            continue
        dwg.add(dwg.text(
            txt, insert=(cx, y),
            text_anchor="middle", dominant_baseline="middle",
            font_family=font, font_size=fs, font_weight="bold",
            fill=fill, letter_spacing=tracking,
        ))

    # Two thin rules flanking the middle word
    rule_w = r_inner * 0.55
    for ry in (y1 + fs1 * 0.62, y3 - fs2 * 0.62):
        for x0, x1 in ((cx - rule_w / 2, cx - 8),
                        (cx + 8, cx + rule_w / 2)):
            dwg.add(dwg.line((x0, ry), (x1, ry),
                             stroke=c["accent"], stroke_width=1,
                             stroke_opacity=0.65))
        dwg.add(dwg.circle(center=(cx, ry), r=2.5, fill=c["accent"]))


# ─── Style: Block ─────────────────────────────────────────────────────────────

def draw_block(dwg: svgwrite.Drawing, c: dict, w: float, h: float,
               band: str, font: str) -> None:
    """
    High-contrast split-block: filled primary bar with reversed-out band name
    on top, accent stripe divider, sub-label below.
    """
    split_y   = h * 0.68
    stripe_h  = h * 0.030
    font_size = h * 0.20
    tracking  = 6

    _base(dwg, c, w, h)

    # Primary bar with halftone wash inside it (subtle texture)
    dwg.add(dwg.rect((0, 0), (w, split_y), fill=c["primary"]))
    dwg.add(dwg.rect((0, 0), (w, split_y),
                     fill=_ensure_halftone(dwg, c["background"],
                                            tile=18, dot_r=1.2, opacity=0.13)))

    # Accent stripe with a thin secondary band above for layered edge
    dwg.add(dwg.rect((0, split_y - 4), (w, 3), fill=c["secondary"],
                     opacity=0.55))
    dwg.add(dwg.rect((0, split_y), (w, stripe_h), fill=c["accent"]))
    dwg.add(dwg.rect((0, split_y + stripe_h), (w, 2), fill=c["secondary"],
                     opacity=0.55))

    # Faint inner border on the primary bar
    dwg.add(dwg.rect((10, 10), (w - 20, split_y - 20),
                     fill="none", stroke=c["background"],
                     stroke_width=1, stroke_opacity=0.35))

    # Band name reversed out of the bar
    dwg.add(dwg.text(
        band,
        insert=(w / 2, split_y / 2),
        text_anchor="middle", dominant_baseline="middle",
        font_family=font, font_size=font_size, font_weight="bold",
        fill=c["background"], letter_spacing=tracking,
    ))

    # Diamond bullets flanking the band name
    diamond_y = split_y / 2
    for dx in (w * 0.06, w * 0.94):
        dwg.add(_diamond(dwg, dx, diamond_y, 6, c["accent"]))

    # Sub-label in the lower section, with end ornaments
    label_y = split_y + stripe_h + (h - split_y - stripe_h) / 2 + 2
    dwg.add(dwg.text(
        "★ EST · 2026 ★ MUSIC",
        insert=(w / 2, label_y),
        text_anchor="middle", dominant_baseline="middle",
        font_family=font, font_size=font_size * 0.30,
        fill=c["primary"], letter_spacing=font_size * 0.10,
    ))


# ─── Dispatcher ───────────────────────────────────────────────────────────────

# (draw_fn, canvas_width, canvas_height)
STYLE_FUNCS = {
    "wordmark": (draw_wordmark, 800, 220),
    "stacked":  (draw_stacked,  500, 420),
    "emblem":   (draw_emblem,   600, 480),
    "badge":    (draw_badge,    600, 600),
    "block":    (draw_block,    800, 300),
}


def generate(style: str, scheme: str, font: str, export_png: bool,
             band_name: str) -> Path:
    if style not in STYLE_FUNCS:
        sys.exit(f"Unknown style '{style}'. Choose: {list(STYLE_FUNCS)}")
    if scheme not in COLOR_SCHEMES:
        sys.exit(f"Unknown scheme '{scheme}'. Choose: {list(COLOR_SCHEMES)}")

    draw_fn, w, h = STYLE_FUNCS[style]
    c = COLOR_SCHEMES[scheme]
    out_path = _out_path(style, scheme)

    dwg = svgwrite.Drawing(str(out_path), size=(w, h))
    draw_fn(dwg, c, float(w), float(h), band_name, font)
    dwg.save()
    print(f"  [{style}/{scheme}] SVG -> {out_path.relative_to(ROOT)}")

    if export_png:
        try:
            import cairosvg
            png_path = out_path.with_suffix(".png")
            cairosvg.svg2png(url=str(out_path), write_to=str(png_path), scale=2.0)
            print(f"  [{style}/{scheme}] PNG -> {png_path.relative_to(ROOT)}")
        except ImportError:
            print("  (PNG skipped — run: pip install cairosvg)")

    return out_path


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate Olive Street logos as SVG")
    parser.add_argument("--style",  choices=list(STYLE_FUNCS), default=None,
                        help="Logo style to generate")
    parser.add_argument("--scheme", choices=list(COLOR_SCHEMES), default="dark",
                        help="Color scheme (default: dark)")
    parser.add_argument("--font",   type=str, default="Georgia",
                        help="Font family name (must be installed, default: Georgia)")
    parser.add_argument("--name",   type=str, default=BAND_NAME,
                        help=f"Band name text (default: '{BAND_NAME}')")
    parser.add_argument("--all",    action="store_true",
                        help="Generate every style × every scheme")
    parser.add_argument("--png",    action="store_true",
                        help="Also export PNG at 2× resolution (requires cairosvg)")
    args = parser.parse_args()

    if args.all:
        for s in STYLE_FUNCS:
            for sc in COLOR_SCHEMES:
                generate(s, sc, args.font, args.png, args.name)
    elif args.style:
        generate(args.style, args.scheme, args.font, args.png, args.name)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

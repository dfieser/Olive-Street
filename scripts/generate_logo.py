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
OUTPUT_DIR = ROOT / "output" / "logos"

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
    """Fill background and embed the font reference stylesheet."""
    dwg.add(dwg.rect((0, 0), (w, h), fill=c["background"]))


# ─── Style: Wordmark ──────────────────────────────────────────────────────────

def draw_wordmark(dwg: svgwrite.Drawing, c: dict, w: float, h: float,
                  band: str, font: str) -> None:
    """
    Centered band name between two horizontal rules.
    Small accent dots anchor each rule end.
    A faint outer frame adds depth without competing with the type.

      ·────────────────────────────────·
        O L I V E   S T R E E T
      ·────────────────────────────────·
    """
    cx, cy = w / 2, h / 2
    font_size = h * 0.26
    tracking = font_size * 0.25

    _base(dwg, c, w, h)

    # Faint outer frame
    dwg.add(dwg.rect(
        (w * 0.04, h * 0.08), (w * 0.92, h * 0.84),
        fill="none", stroke=c["secondary"],
        stroke_width=0.5, stroke_opacity=0.4,
    ))

    # Rules
    rule_margin = w * 0.08
    rule_y_top    = cy - font_size * 0.78
    rule_y_bottom = cy + font_size * 0.60
    for ry in (rule_y_top, rule_y_bottom):
        dwg.add(dwg.line(
            (rule_margin, ry), (w - rule_margin, ry),
            stroke=c["accent"], stroke_width=1.5,
        ))
        for dx in (rule_margin, w - rule_margin):
            dwg.add(dwg.circle(center=(dx, ry), r=3, fill=c["accent"]))

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


# ─── Style: Stacked ───────────────────────────────────────────────────────────

def draw_stacked(dwg: svgwrite.Drawing, c: dict, w: float, h: float,
                 band: str, font: str) -> None:
    """
    Split band name across two lines with a diamond-accented center divider.

      OLIVE
      ──◆──
      STREET
    """
    words = band.split()
    line1 = words[0] if words else band
    line2 = " ".join(words[1:]) if len(words) > 1 else ""
    cx = w / 2
    fs1 = h * 0.26
    fs2 = h * 0.22
    tracking = fs1 * 0.28
    gap = h * 0.06
    diamond_size = 5

    _base(dwg, c, w, h)

    # Divider line
    div_y  = h / 2
    div_w  = w * 0.55
    div_x0 = (w - div_w) / 2
    div_x1 = (w + div_w) / 2
    for x0, x1 in ((div_x0, cx - diamond_size * 2),
                   (cx + diamond_size * 2, div_x1)):
        dwg.add(dwg.line(
            (x0, div_y), (x1, div_y),
            stroke=c["accent"], stroke_width=1.5,
        ))

    # Center diamond
    dwg.add(dwg.polygon(
        points=[(cx, div_y - diamond_size),
                (cx + diamond_size, div_y),
                (cx, div_y + diamond_size),
                (cx - diamond_size, div_y)],
        fill=c["accent"],
    ))

    # Top word
    dwg.add(dwg.text(
        line1,
        insert=(cx, div_y - gap - fs1 * 0.15),
        text_anchor="middle",
        dominant_baseline="auto",
        font_family=font,
        font_size=fs1,
        font_weight="bold",
        fill=c["primary"],
        letter_spacing=tracking,
    ))

    # Bottom word
    if line2:
        dwg.add(dwg.text(
            line2,
            insert=(cx, div_y + gap + fs2 * 0.85),
            text_anchor="middle",
            dominant_baseline="auto",
            font_family=font,
            font_size=fs2,
            font_weight="bold",
            fill=c["primary"],
            letter_spacing=fs2 * 0.28,
        ))


# ─── Style: Emblem ────────────────────────────────────────────────────────────

def draw_emblem(dwg: svgwrite.Drawing, c: dict, w: float, h: float,
                band: str, font: str) -> None:
    """
    Band name centered in a double-border rectangular frame.
    Corner ornaments are computed L-cuts that give a refined typographic feel.
    """
    cx, cy = w / 2, h / 2
    font_size = h * 0.20
    tracking  = font_size * 0.30
    frame_mx, frame_my = w * 0.10, h * 0.14
    frame_w = w - frame_mx * 2
    frame_h = h - frame_my * 2
    inset = 6
    corner_len = 16

    _base(dwg, c, w, h)

    # Outer border
    dwg.add(dwg.rect(
        (frame_mx, frame_my), (frame_w, frame_h),
        fill="none", stroke=c["primary"], stroke_width=1.5,
    ))
    # Inner border
    dwg.add(dwg.rect(
        (frame_mx + inset, frame_my + inset),
        (frame_w - inset * 2, frame_h - inset * 2),
        fill="none", stroke=c["accent"], stroke_width=0.75,
    ))

    # Corner ornaments: cover the outer border to create an L-cut, then redraw
    corners = [
        (frame_mx,          frame_my,          1,  1),
        (frame_mx + frame_w, frame_my,         -1,  1),
        (frame_mx,          frame_my + frame_h, 1, -1),
        (frame_mx + frame_w, frame_my + frame_h, -1, -1),
    ]
    for fx, fy, sx, sy in corners:
        dwg.add(dwg.line(
            (fx - sx * corner_len, fy), (fx + sx * corner_len, fy),
            stroke=c["background"], stroke_width=4,
        ))
        dwg.add(dwg.line(
            (fx, fy - sy * corner_len), (fx, fy + sy * corner_len),
            stroke=c["background"], stroke_width=4,
        ))
        dwg.add(dwg.line(
            (fx - sx * corner_len, fy), (fx, fy),
            stroke=c["accent"], stroke_width=2,
        ))
        dwg.add(dwg.line(
            (fx, fy - sy * corner_len), (fx, fy),
            stroke=c["accent"], stroke_width=2,
        ))

    # Horizontal rule below band name
    rule_y = cy + font_size * 0.70
    dwg.add(dwg.line(
        (frame_mx + inset * 3, rule_y),
        (frame_mx + frame_w - inset * 3, rule_y),
        stroke=c["accent"], stroke_width=1,
    ))

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

    # Subtitle / year label
    dwg.add(dwg.text(
        "EST. ——",
        insert=(cx, cy + font_size * 1.2),
        text_anchor="middle",
        dominant_baseline="middle",
        font_family=font,
        font_size=font_size * 0.28,
        fill=c["secondary"],
        letter_spacing=font_size * 0.12,
    ))


# ─── Style: Badge ─────────────────────────────────────────────────────────────

def draw_badge(dwg: svgwrite.Drawing, c: dict, w: float, h: float,
               band: str, font: str) -> None:
    """
    Circular stamp badge with concentric rings and computed tick marks.
    Band name is split across two centered lines inside the inner ring.
    """
    cx, cy = w / 2, h / 2
    r_outer = min(w, h) * 0.44
    r_inner = r_outer * 0.80
    font_size = r_inner * 0.38
    tracking  = font_size * 0.28

    _base(dwg, c, w, h)

    # Outer ring
    dwg.add(dwg.circle(
        center=(cx, cy), r=r_outer,
        fill="none", stroke=c["primary"], stroke_width=3,
    ))
    # Inner ring
    dwg.add(dwg.circle(
        center=(cx, cy), r=r_inner,
        fill="none", stroke=c["accent"], stroke_width=1,
    ))

    # Tick marks around the inner ring (every 30°; cardinal ticks are thicker)
    t_in  = r_inner * 0.93
    t_out = r_inner * 1.065
    for deg in range(0, 360, 30):
        angle = math.radians(deg)
        x0 = cx + t_in  * math.cos(angle)
        y0 = cy + t_in  * math.sin(angle)
        x1 = cx + t_out * math.cos(angle)
        y1 = cy + t_out * math.sin(angle)
        dwg.add(dwg.line(
            (x0, y0), (x1, y1),
            stroke=c["accent"],
            stroke_width=2 if deg % 90 == 0 else 1,
        ))

    # Band name — split into two lines
    words = band.split()
    line1 = words[0]
    line2 = " ".join(words[1:]) if len(words) > 1 else ""
    line_gap = font_size * 0.65

    for text, yoff in ((line1, -line_gap / 2), (line2, line_gap / 2 + font_size * 0.15)):
        if not text:
            continue
        dwg.add(dwg.text(
            text,
            insert=(cx, cy + yoff),
            text_anchor="middle",
            dominant_baseline="middle",
            font_family=font,
            font_size=font_size,
            font_weight="bold",
            fill=c["primary"],
            letter_spacing=tracking,
        ))

    # Center dot accent
    dwg.add(dwg.circle(center=(cx, cy + line_gap * 1.35), r=3, fill=c["accent"]))


# ─── Style: Block ─────────────────────────────────────────────────────────────

def draw_block(dwg: svgwrite.Drawing, c: dict, w: float, h: float,
               band: str, font: str) -> None:
    """
    High-contrast split-block design.
    A filled primary bar occupies the top 65%; band name is reversed out.
    An accent stripe separates the two zones.
    """
    split_y   = h * 0.65
    stripe_h  = h * 0.025
    font_size = h * 0.24
    tracking  = font_size * 0.22

    _base(dwg, c, w, h)

    # Primary bar
    dwg.add(dwg.rect((0, 0), (w, split_y), fill=c["primary"]))
    # Accent stripe at the split
    dwg.add(dwg.rect((0, split_y), (w, stripe_h), fill=c["accent"]))

    # Band name reversed out of the bar
    dwg.add(dwg.text(
        band,
        insert=(w / 2, split_y / 2),
        text_anchor="middle",
        dominant_baseline="middle",
        font_family=font,
        font_size=font_size,
        font_weight="bold",
        fill=c["background"],
        letter_spacing=tracking,
    ))

    # Sub-label in the lower section
    label_y = split_y + stripe_h + (h - split_y - stripe_h) / 2
    dwg.add(dwg.text(
        "MUSIC",
        insert=(w / 2, label_y),
        text_anchor="middle",
        dominant_baseline="middle",
        font_family=font,
        font_size=font_size * 0.28,
        fill=c["primary"],
        letter_spacing=font_size * 0.18,
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

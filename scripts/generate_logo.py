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


def _starburst(dwg: svgwrite.Drawing, x: float, y: float, r_out: float,
                r_in: float, points: int, fill: str
                ) -> "svgwrite.shapes.Polygon":
    pts = []
    for i in range(points * 2):
        rr = r_out if i % 2 == 0 else r_in
        a = math.radians(i * (360 / (points * 2)) - 90)
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    return dwg.polygon(points=pts, fill=fill)


def _corner_bracket(dwg: svgwrite.Drawing, x: float, y: float,
                     length: float, sx: int, sy: int,
                     stroke: str, width: float
                     ) -> list:
    """L-shaped bracket starting at (x,y); sx/sy in {-1, 1} pick the quadrant."""
    return [
        dwg.line((x, y), (x + sx * length, y),
                 stroke=stroke, stroke_width=width, stroke_linecap="square"),
        dwg.line((x, y), (x, y + sy * length),
                 stroke=stroke, stroke_width=width, stroke_linecap="square"),
    ]


def _tick_row(dwg: svgwrite.Drawing, x_start: float, y: float, count: int,
               step: float, height: float, stroke: str,
               width: float = 1, opacity: float = 0.6) -> list:
    """A row of small vertical tick marks (calibration feel)."""
    return [
        dwg.line((x_start + i * step, y - height / 2),
                 (x_start + i * step, y + height / 2),
                 stroke=stroke, stroke_width=width, stroke_opacity=opacity)
        for i in range(count)
    ]


def _arc_text(dwg: svgwrite.Drawing, text: str, cx: float, cy: float,
               r: float, centre_deg: float, font_size: float,
               fill: str, font: str, letter_spacing: float = 0,
               flip_bottom: bool = False) -> list:
    """
    Place each character along a circular arc, tangent to the ring and reading
    upright. centre_deg=0 is top, 180 is bottom; bottom text is automatically
    flipped so it reads right-side up.
    """
    def char_w(ch: str) -> float:
        if ch == " ":      return font_size * 0.32
        if ch in "IJijl1": return font_size * 0.34
        if ch in "MWmw":   return font_size * 0.74
        return font_size * 0.58

    widths = [char_w(ch) for ch in text]
    gap = letter_spacing
    total = sum(widths) + gap * max(0, len(text) - 1)

    flip = (90 < centre_deg < 270) and flip_bottom
    direction = -1 if flip else 1
    centre_math = math.radians(centre_deg) - math.pi / 2
    # Start at the side the reader's eye expects: top arc starts from the left
    # of the centre, bottom arc (flipped) starts from the right of the centre
    # so each subsequent character moves visually rightward.
    start_offset = -direction * (total / 2)
    cur_rad = centre_math + start_offset / r

    elements = []
    for ch, cw in zip(text, widths):
        mid = cur_rad + direction * (cw / 2) / r
        x = cx + r * math.cos(mid)
        y = cy + r * math.sin(mid)
        rot = math.degrees(mid) + (90 if not flip else -90)
        elements.append(dwg.text(
            ch, insert=(x, y),
            font_size=font_size, font_family=font, font_weight="bold",
            fill=fill, text_anchor="middle", dominant_baseline="central",
            transform=f"rotate({rot:.2f},{x:.2f},{y:.2f})",
        ))
        cur_rad += direction * (cw + gap) / r
    return elements


# ─── Style: Wordmark ──────────────────────────────────────────────────────────

def draw_wordmark(dwg: svgwrite.Drawing, c: dict, w: float, h: float,
                  band: str, font: str) -> None:
    """
    Centered band name between two diamond-anchored rules. Side ornament
    panels carry small starbursts + EST micro-mark; corner brackets and a
    faint outer frame add stamped-paper depth.
    """
    cx, cy = w / 2, h / 2
    font_size = h * 0.20
    tracking = 6

    _base(dwg, c, w, h)
    _wash(dwg, c, w, h)

    # Faint double frame
    dwg.add(dwg.rect(
        (w * 0.025, h * 0.08), (w * 0.95, h * 0.84),
        fill="none", stroke=c["secondary"],
        stroke_width=0.7, stroke_opacity=0.55,
    ))
    dwg.add(dwg.rect(
        (w * 0.04, h * 0.14), (w * 0.92, h * 0.72),
        fill="none", stroke=c["secondary"],
        stroke_width=0.5, stroke_opacity=0.35,
    ))

    # Corner brackets
    bx0, by0 = w * 0.025, h * 0.08
    bx1, by1 = w * 0.975, h * 0.92
    bracket_len = h * 0.10
    for x, y, sx, sy in ((bx0, by0, 1, 1), (bx1, by0, -1, 1),
                         (bx0, by1, 1, -1), (bx1, by1, -1, -1)):
        for el in _corner_bracket(dwg, x, y, bracket_len, sx, sy,
                                   c["accent"], 2):
            dwg.add(el)

    # Rules with diamond ends — stop short to leave room for side ornaments
    rule_margin = w * 0.13
    rule_y_top    = cy - font_size * 0.95
    rule_y_bottom = cy + font_size * 0.78
    for ry in (rule_y_top, rule_y_bottom):
        dwg.add(dwg.line(
            (rule_margin + 14, ry), (w - rule_margin - 14, ry),
            stroke=c["accent"], stroke_width=1.8,
        ))
        for dx in (rule_margin, w - rule_margin):
            dwg.add(_diamond(dwg, dx, ry, 5, c["accent"]))

    # Side ornaments: small starbursts framing the wordmark
    for sx_pos in (rule_margin - 18, w - rule_margin + 18):
        dwg.add(_starburst(dwg, sx_pos, cy, r_out=10, r_in=4,
                           points=4, fill=c["accent"]))

    # Tick rows just above and below the rules — calibration detail
    tick_count = 9
    tick_step = (w - rule_margin * 2 - 28) / (tick_count - 1)
    for ty in (rule_y_top - 8, rule_y_bottom + 8):
        for el in _tick_row(dwg, rule_margin + 14, ty, tick_count,
                             tick_step, 5, c["accent"],
                             width=0.9, opacity=0.45):
            dwg.add(el)

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

    # MUSIC sub-mark on the bottom rule
    dwg.add(dwg.rect((cx - 36, rule_y_bottom - 9), (72, 18),
                     fill=c["background"]))
    dwg.add(dwg.text(
        "MUSIC",
        insert=(cx, rule_y_bottom + 1),
        text_anchor="middle", dominant_baseline="middle",
        font_family=font, font_size=11,
        fill=c["secondary"], letter_spacing=3,
    ))


# ─── Style: Stacked ───────────────────────────────────────────────────────────

def draw_stacked(dwg: svgwrite.Drawing, c: dict, w: float, h: float,
                 band: str, font: str) -> None:
    """
    Three-line stack OLIVE / STREET / BAND with diamond-rule dividers,
    corner brackets, starburst crown, and a tick-mark calibration band.
    """
    words = band.split()
    if len(words) >= 3:
        l1, l2, l3 = words[0], words[1], " ".join(words[2:])
    elif len(words) == 2:
        l1, l2, l3 = words[0], words[1], ""
    else:
        l1, l2, l3 = band, "", ""

    cx = w / 2
    fs1 = h * 0.16      # OLIVE / STREET
    fs2 = h * 0.14      # BAND (smaller, accent colour)

    y_top  = h * 0.30
    y_mid  = h * 0.48
    y_bot  = h * 0.74

    _base(dwg, c, w, h)
    _wash(dwg, c, w, h)

    # Double frame
    dwg.add(dwg.rect((w * 0.05, h * 0.05), (w * 0.90, h * 0.90),
                     fill="none", stroke=c["secondary"],
                     stroke_width=0.7, stroke_opacity=0.55))
    dwg.add(dwg.rect((w * 0.075, h * 0.075), (w * 0.85, h * 0.85),
                     fill="none", stroke=c["secondary"],
                     stroke_width=0.4, stroke_opacity=0.35))

    # Corner brackets in accent
    bx0, by0 = w * 0.05, h * 0.05
    bx1, by1 = w * 0.95, h * 0.95
    bl = min(w, h) * 0.06
    for x, y, sx, sy in ((bx0, by0, 1, 1), (bx1, by0, -1, 1),
                         (bx0, by1, 1, -1), (bx1, by1, -1, -1)):
        for el in _corner_bracket(dwg, x, y, bl, sx, sy, c["accent"], 2):
            dwg.add(el)
        dwg.add(dwg.circle(center=(x, y), r=2.5, fill=c["accent"]))

    # Starburst crown above OLIVE
    dwg.add(_starburst(dwg, cx, h * 0.16, r_out=10, r_in=4,
                       points=4, fill=c["accent"]))
    # Mirror starburst at the bottom
    dwg.add(_starburst(dwg, cx, h * 0.88, r_out=10, r_in=4,
                       points=4, fill=c["accent"]))

    # Two diamond-anchored rules between the lines
    rule_w = w * 0.62
    diamond = 5
    for div_y in ((y_top + y_mid) / 2, (y_mid + y_bot) / 2):
        x0 = cx - rule_w / 2
        x1 = cx + rule_w / 2
        for sx0, sx1 in ((x0, cx - diamond * 2),
                          (cx + diamond * 2, x1)):
            dwg.add(dwg.line((sx0, div_y), (sx1, div_y),
                             stroke=c["accent"], stroke_width=1.6))
        dwg.add(_diamond(dwg, cx, div_y, diamond, c["accent"]))
        # Tiny dots flanking the diamond
        for sd in (-diamond * 4, diamond * 4):
            dwg.add(dwg.circle(center=(cx + sd, div_y), r=2,
                               fill=c["accent"], fill_opacity=0.7))

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

    # EST · 2026 micro-mark just below the bottom rule
    dwg.add(dwg.text(
        "★ EST · 2026 ★",
        insert=(cx, h * 0.92),
        text_anchor="middle", dominant_baseline="middle",
        font_family=font, font_size=10,
        fill=c["secondary"], letter_spacing=2,
    ))


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

    # Starburst crowns at top centre of the inner frame
    crown_y = frame_my + 22
    dwg.add(_starburst(dwg, cx, crown_y, r_out=10, r_in=4,
                       points=5, fill=c["accent"]))
    # Calibration tick row beneath the crown
    tick_count = 13
    tick_w = frame_w * 0.42
    tick_step = tick_w / (tick_count - 1)
    tick_x0 = cx - tick_w / 2
    for el in _tick_row(dwg, tick_x0, crown_y + 16, tick_count, tick_step,
                         6, c["accent"], width=1, opacity=0.55):
        dwg.add(el)

    # Top line — OLIVE STREET
    y1 = cy - fs1 * 0.2
    dwg.add(dwg.text(
        l1, insert=(cx, y1),
        text_anchor="middle", dominant_baseline="middle",
        font_family=font, font_size=fs1, font_weight="bold",
        fill=c["primary"], letter_spacing=tracking1,
    ))

    # Divider rule with diamond + flanking starbursts
    rule_y = y1 + fs1 * 0.85
    half_rule = w * 0.22
    for x0, x1 in ((cx - half_rule, cx - 14),
                   (cx + 14, cx + half_rule)):
        dwg.add(dwg.line((x0, rule_y), (x1, rule_y),
                         stroke=c["accent"], stroke_width=1.6))
    dwg.add(_diamond(dwg, cx, rule_y, 6, c["accent"]))
    for x in (cx - half_rule, cx + half_rule):
        dwg.add(_starburst(dwg, x, rule_y, r_out=7, r_in=3,
                           points=4, fill=c["accent"]))

    # Bottom line — BAND
    y2 = rule_y + fs2 * 0.95
    if l2:
        dwg.add(dwg.text(
            l2, insert=(cx, y2),
            text_anchor="middle", dominant_baseline="middle",
            font_family=font, font_size=fs2, font_weight="bold",
            fill=c["accent"], letter_spacing=tracking2,
        ))

    # Mirror tick row above the EST mark
    tick_y_bot = frame_my + frame_h - 32
    for el in _tick_row(dwg, tick_x0, tick_y_bot, tick_count, tick_step,
                         6, c["accent"], width=1, opacity=0.55):
        dwg.add(el)

    # EST · 2026 micro-mark at bottom of frame
    dwg.add(dwg.text(
        "★ EST · 2026 ★ MUSIC ★",
        insert=(cx, frame_my + frame_h - 16),
        text_anchor="middle", dominant_baseline="middle",
        font_family=font, font_size=11,
        fill=c["secondary"], letter_spacing=2,
    ))


# ─── Style: Badge ─────────────────────────────────────────────────────────────

def draw_badge(dwg: svgwrite.Drawing, c: dict, w: float, h: float,
               band: str, font: str) -> None:
    """
    Circular badge — perimeter arc text, dense calibration rim, sunburst
    medallion, and a ribbon banner at the bottom.
    """
    cx, cy = w / 2, h / 2
    r_outer = min(w, h) * 0.48
    r_arc   = r_outer * 0.91     # radius for arc text
    r_inner = r_outer * 0.76     # inner type field

    fs_centre = r_inner * 0.34
    tracking  = 6

    _base(dwg, c, w, h)
    _wash(dwg, c, w, h)

    # Outer rim — thick + thin double ring
    dwg.add(dwg.circle(center=(cx, cy), r=r_outer,
                       fill="none", stroke=c["primary"], stroke_width=5))
    dwg.add(dwg.circle(center=(cx, cy), r=r_outer - 8,
                       fill="none", stroke=c["accent"],
                       stroke_width=1.2, stroke_opacity=0.7))
    dwg.add(dwg.circle(center=(cx, cy), r=r_outer - 22,
                       fill="none", stroke=c["primary"],
                       stroke_width=1.2, stroke_opacity=0.55))

    # Inner type-field disc
    dwg.add(dwg.circle(center=(cx, cy), r=r_inner,
                       fill=c["background"]))
    dwg.add(dwg.circle(center=(cx, cy), r=r_inner,
                       fill="none", stroke=c["accent"], stroke_width=1.4))
    dwg.add(dwg.circle(center=(cx, cy), r=r_inner - 6,
                       fill="none", stroke=c["accent"],
                       stroke_width=0.6, stroke_opacity=0.5))

    # Calibration ticks — dense between rim and inner ring (skip top/bottom
    # arc spans where text and ribbon will sit).
    t_in  = r_outer - 24
    t_out_minor = r_inner + 8
    for i in range(120):
        deg = i * 3
        # Skip ranges where arc text (top) and ribbon (bottom) live
        if 300 <= deg or deg <= 60:    continue   # top text band
        if 120 <= deg <= 240:          continue   # bottom ribbon band
        angle = math.radians(deg - 90)
        major = (i % 5 == 0)
        t_out = t_out_minor if not major else (t_out_minor + 4)
        dwg.add(dwg.line(
            (cx + t_in  * math.cos(angle), cy + t_in  * math.sin(angle)),
            (cx + t_out * math.cos(angle), cy + t_out * math.sin(angle)),
            stroke=c["accent"],
            stroke_width=(1.8 if major else 0.7),
            stroke_opacity=(0.85 if major else 0.4),
        ))

    # Arc text "OLIVE STREET BAND" along the top, between rim and inner ring
    arc_fs = r_outer * 0.10
    for el in _arc_text(dwg, band, cx, cy, r_arc, centre_deg=0,
                         font_size=arc_fs, fill=c["primary"], font=font,
                         letter_spacing=arc_fs * 0.12):
        dwg.add(el)

    # Bracket diamonds at the 9 o'clock and 3 o'clock positions
    for deg in (90, 270):
        angle = math.radians(deg - 90)
        dx = cx + r_arc * math.cos(angle)
        dy = cy + r_arc * math.sin(angle)
        dwg.add(_diamond(dwg, dx, dy, 6, c["accent"]))

    # Faint radial sunburst spokes between rings
    # Faint sunburst spokes radiating from inside the inner ring
    for i in range(48):
        deg = i * 7.5
        angle = math.radians(deg - 90)
        s_in = r_inner * 0.42
        s_out = r_inner * 0.95
        dwg.add(dwg.line(
            (cx + s_in  * math.cos(angle), cy + s_in  * math.sin(angle)),
            (cx + s_out * math.cos(angle), cy + s_out * math.sin(angle)),
            stroke=c["accent"], stroke_width=0.4, stroke_opacity=0.18,
        ))

    # Big starburst medallion behind the centre type
    dwg.add(_starburst(dwg, cx, cy, r_out=r_inner * 0.65,
                       r_in=r_inner * 0.32, points=12, fill=c["accent"]))
    dwg.add(dwg.circle(center=(cx, cy), r=r_inner * 0.55,
                       fill=c["background"], stroke=c["accent"],
                       stroke_width=2))
    dwg.add(dwg.circle(center=(cx, cy), r=r_inner * 0.49,
                       fill="none", stroke=c["accent"],
                       stroke_width=0.6, stroke_opacity=0.5))

    # Centre word "OSB" monogram + sub-line
    dwg.add(dwg.text(
        "OSB", insert=(cx, cy - fs_centre * 0.08),
        text_anchor="middle", dominant_baseline="middle",
        font_family=font, font_size=fs_centre, font_weight="bold",
        fill=c["primary"], letter_spacing=tracking,
    ))
    dwg.add(dwg.text(
        "MUSIC", insert=(cx, cy + fs_centre * 0.62),
        text_anchor="middle", dominant_baseline="middle",
        font_family=font, font_size=fs_centre * 0.30,
        fill=c["accent"], letter_spacing=4,
    ))

    # Hairline rule above MUSIC
    rule_y = cy + fs_centre * 0.40
    rule_w_inner = r_inner * 0.42
    for x0, x1 in ((cx - rule_w_inner / 2, cx - 6),
                   (cx + 6, cx + rule_w_inner / 2)):
        dwg.add(dwg.line((x0, rule_y), (x1, rule_y),
                         stroke=c["accent"], stroke_width=1,
                         stroke_opacity=0.7))
    dwg.add(dwg.circle(center=(cx, rule_y), r=2.4, fill=c["accent"]))

    # Ribbon banner across the bottom of the badge
    rib_w = r_outer * 1.55
    rib_h = r_outer * 0.20
    rib_y = cy + r_outer * 0.62
    rib_x = cx - rib_w / 2
    # Tail flourishes (triangle ends extending past the body)
    tail = rib_h * 0.55
    body = dwg.polygon(points=[
        (rib_x,           rib_y),
        (rib_x + tail,    rib_y + rib_h * 0.5),
        (rib_x,           rib_y + rib_h),
        (rib_x + rib_w,   rib_y + rib_h),
        (rib_x + rib_w - tail, rib_y + rib_h * 0.5),
        (rib_x + rib_w,   rib_y),
    ], fill=c["accent"], stroke=c["primary"], stroke_width=2)
    dwg.add(body)
    # Inner stitch line
    dwg.add(dwg.polygon(points=[
        (rib_x + 6,       rib_y + 4),
        (rib_x + tail,    rib_y + rib_h * 0.5),
        (rib_x + 6,       rib_y + rib_h - 4),
        (rib_x + rib_w - 6, rib_y + rib_h - 4),
        (rib_x + rib_w - tail, rib_y + rib_h * 0.5),
        (rib_x + rib_w - 6, rib_y + 4),
    ], fill="none", stroke=c["primary"], stroke_width=0.8,
                          stroke_opacity=0.6))
    # Banner text
    dwg.add(dwg.text(
        "★ EST · 2026 ★",
        insert=(cx, rib_y + rib_h / 2 + 1),
        text_anchor="middle", dominant_baseline="middle",
        font_family=font, font_size=rib_h * 0.42, font_weight="bold",
        fill=c["primary"], letter_spacing=3,
    ))

    # Final hairline outer ring (drawn on top so the ribbon doesn't overflow visually)
    dwg.add(dwg.circle(center=(cx, cy), r=r_outer + 4,
                       fill="none", stroke=c["accent"],
                       stroke_width=0.7, stroke_opacity=0.55))


# ─── Style: Seal ──────────────────────────────────────────────────────────────

def draw_seal(dwg: svgwrite.Drawing, c: dict, w: float, h: float,
               band: str, font: str) -> None:
    """
    Circular government-style seal: BAND NAME arcing along the top, "EST · 2026"
    arcing along the bottom (right-side up via flip), bold three-line stack
    inside, with notched cardinals and a perimeter dot ring.
    """
    cx, cy = w / 2, h / 2
    r_outer = min(w, h) * 0.48
    r_text  = r_outer * 0.86
    r_inner = r_outer * 0.74

    words = band.split()
    if len(words) >= 3:
        l1, l2, l3 = words[0], words[1], " ".join(words[2:])
    elif len(words) == 2:
        l1, l2, l3 = words[0], words[1], ""
    else:
        l1, l2, l3 = band, "", ""

    fs1 = r_inner * 0.30
    fs2 = r_inner * 0.22

    _base(dwg, c, w, h)
    _wash(dwg, c, w, h)

    # Triple ring frame
    dwg.add(dwg.circle(center=(cx, cy), r=r_outer,
                       fill="none", stroke=c["primary"], stroke_width=4))
    dwg.add(dwg.circle(center=(cx, cy), r=r_outer - 7,
                       fill="none", stroke=c["primary"],
                       stroke_width=1, stroke_opacity=0.55))
    dwg.add(dwg.circle(center=(cx, cy), r=r_inner,
                       fill="none", stroke=c["accent"], stroke_width=1.6))
    dwg.add(dwg.circle(center=(cx, cy), r=r_inner - 6,
                       fill="none", stroke=c["accent"],
                       stroke_width=0.6, stroke_opacity=0.55))

    # Perimeter dot ring (on the outer frame)
    n_dots = 60
    for i in range(n_dots):
        angle = math.radians(i * (360 / n_dots) - 90)
        # Skip top arc (0±55°) and bottom arc (180±35°) to avoid colliding text
        deg = (i * (360 / n_dots)) % 360
        if deg <= 55 or deg >= 305:    continue
        if 145 <= deg <= 215:          continue
        x = cx + (r_outer - 14) * math.cos(angle)
        y = cy + (r_outer - 14) * math.sin(angle)
        dwg.add(dwg.circle(center=(x, y), r=1.6,
                           fill=c["accent"], fill_opacity=0.7))

    # Cardinal notches — small filled triangles cutting into the inner ring
    for deg in (90, 270):
        angle = math.radians(deg - 90)
        x = cx + r_inner * math.cos(angle)
        y = cy + r_inner * math.sin(angle)
        dwg.add(_diamond(dwg, x, y, 7, c["accent"]))
        dwg.add(dwg.circle(center=(x, y), r=2.2, fill=c["background"]))

    # Arc text — band name across the top
    arc_fs_top = r_outer * 0.10
    for el in _arc_text(dwg, band, cx, cy, r_text, centre_deg=0,
                         font_size=arc_fs_top, fill=c["primary"], font=font,
                         letter_spacing=arc_fs_top * 0.18):
        dwg.add(el)

    # Arc text — EST mark along the bottom (flipped to read upright)
    arc_fs_bot = r_outer * 0.075
    for el in _arc_text(dwg, "★ EST · 2026 · MUSIC ★", cx, cy, r_text,
                         centre_deg=180, font_size=arc_fs_bot,
                         fill=c["accent"], font=font,
                         letter_spacing=arc_fs_bot * 0.20,
                         flip_bottom=True):
        dwg.add(el)

    # Three-line centre stack
    y1 = cy - fs1 * 1.0
    y2 = cy
    y3 = cy + fs1 * 1.0
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
            fill=fill, letter_spacing=4,
        ))

    # Centre starburst between OLIVE and STREET (subtle behind the type)
    dwg.add(_starburst(dwg, cx, y1 + fs1 * 0.55, r_out=6, r_in=2.5,
                       points=4, fill=c["accent"]))
    dwg.add(_starburst(dwg, cx, y3 - fs2 * 0.55, r_out=6, r_in=2.5,
                       points=4, fill=c["accent"]))


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

    # Double inner border on the primary bar
    dwg.add(dwg.rect((10, 10), (w - 20, split_y - 20),
                     fill="none", stroke=c["background"],
                     stroke_width=1.2, stroke_opacity=0.4))
    dwg.add(dwg.rect((18, 18), (w - 36, split_y - 36),
                     fill="none", stroke=c["accent"],
                     stroke_width=0.8, stroke_opacity=0.4))

    # Corner brackets in the primary bar corners
    bl = h * 0.10
    for x, y, sx, sy in ((10, 10, 1, 1), (w - 10, 10, -1, 1),
                          (10, split_y - 10, 1, -1),
                          (w - 10, split_y - 10, -1, -1)):
        for el in _corner_bracket(dwg, x, y, bl, sx, sy,
                                   c["accent"], 2.5):
            dwg.add(el)

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
    for dx in (w * 0.07, w * 0.93):
        dwg.add(_diamond(dwg, dx, diamond_y, 7, c["accent"]))
        # tiny mirror dot inside the bar margin
        dwg.add(dwg.circle(center=(dx + (1 if dx < w / 2 else -1) * 18,
                                    diamond_y), r=2.5,
                           fill=c["accent"], fill_opacity=0.6))

    # EQ-bar pattern in the lower section — graphic anchor below the wordmark
    bar_count = 11
    bar_zone_w = w * 0.30
    bar_zone_x = w / 2 - bar_zone_w / 2
    bar_w_each = bar_zone_w / (bar_count * 1.7)
    bar_gap = (bar_zone_w - bar_count * bar_w_each) / (bar_count - 1)
    bar_max_h = (h - split_y - stripe_h) * 0.55
    bar_base_y = h - (h - split_y - stripe_h) * 0.18
    heights = [0.55, 0.75, 0.90, 1.0, 0.92, 0.78, 0.92, 1.0, 0.90, 0.75, 0.55]
    for i in range(bar_count):
        bx = bar_zone_x + i * (bar_w_each + bar_gap)
        bh = bar_max_h * heights[i]
        dwg.add(dwg.rect((bx, bar_base_y - bh), (bar_w_each, bh),
                         fill=c["primary"], rx=1))

    # EST · 2026 mark to the LEFT of the EQ cluster, MUSIC mark to the RIGHT
    label_y = bar_base_y - bar_max_h * 0.50
    label_size = font_size * 0.30
    dwg.add(dwg.text(
        "★ EST · 2026",
        insert=(bar_zone_x - 24, label_y),
        text_anchor="end", dominant_baseline="middle",
        font_family=font, font_size=label_size,
        fill=c["primary"], letter_spacing=2,
    ))
    dwg.add(dwg.text(
        "MUSIC ★",
        insert=(bar_zone_x + bar_zone_w + 24, label_y),
        text_anchor="start", dominant_baseline="middle",
        font_family=font, font_size=label_size, font_weight="bold",
        fill=c["primary"], letter_spacing=2,
    ))


# ─── Dispatcher ───────────────────────────────────────────────────────────────

# (draw_fn, canvas_width, canvas_height)
STYLE_FUNCS = {
    "wordmark": (draw_wordmark, 800, 220),
    "stacked":  (draw_stacked,  500, 420),
    "emblem":   (draw_emblem,   600, 480),
    "badge":    (draw_badge,    600, 600),
    "seal":     (draw_seal,     600, 600),
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

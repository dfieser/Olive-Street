"""generate_profile.py
--------------------
Generate circular social-media profile images for Olive Street Band.
All designs are bold and graphic — optimised to read clearly at small sizes.

Designs:
  stack   — OLIVE / STREET / BAND in large bold stacked type, pure typography
  arc     — Band name arcing along the top, bold EQ bars in the centre
  stripe  — Wide horizontal colour stripe with band name reversed out in it
  target  — Bullseye concentric rings with bold text on a bar at the centre
  split   — Circle cut horizontally in two contrasting halves
    wavefield — Layered horizontal waveforms with a center title medallion
    ripple    — Circular audio-ripple wave built from radial sine contours
    scope     — Oscilloscope dial with calibration ticks and waveform screen
    boombox   — Geometric boombox seal with speakers, slot, and EQ deck
    lattice   — Radial wave lattice with phase-shifted concentric ripples
    funkgrid  — Syncopated rhythm block matrix with circular title ring
    signstamp — Rotated abstract street-sign plate inside a circular stamp

Color schemes: dark | light | tan | mono

Usage:
  python scripts/generate_profile.py --design stack
  python scripts/generate_profile.py --design stripe --scheme tan
  python scripts/generate_profile.py --all
  python scripts/generate_profile.py --all --png

Requires:
  pip install svgwrite
  pip install cairosvg   (optional — only needed for --png export)
"""

from __future__ import annotations

import argparse
import math
from datetime import datetime
from pathlib import Path

import svgwrite

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output" / "profiles"

# ─── Identity ─────────────────────────────────────────────────────────────────
BAND_NAME = "OLIVE STREET BAND"

# ─── Canvas ───────────────────────────────────────────────────────────────────
SIZE = 1080        # square canvas; social platforms crop to a circle
CX   = SIZE // 2   # 540
CY   = SIZE // 2   # 540
R    = SIZE // 2   # 540 — circle fills edge-to-edge

# ─── Colour schemes ───────────────────────────────────────────────────────────
# Palette: Olive Green #6B7A3A | Tan #DDB892 | Cream #F5F0E1
COLOR_SCHEMES: dict[str, dict] = {
    "dark":  {"bg": "#6B7A3A", "fg": "#F5F0E1", "ac": "#DDB892"},
    "light": {"bg": "#F5F0E1", "fg": "#6B7A3A", "ac": "#DDB892"},
    "tan":   {"bg": "#DDB892", "fg": "#6B7A3A", "ac": "#F5F0E1"},
    "mono":  {"bg": "#1A1A1A", "fg": "#F5F0E1", "ac": "#DDB892"},
}

DESIGNS = ["stack", "arc", "stripe", "target", "split", "wavefield", "ripple"]


DESIGNS += ["scope", "boombox", "lattice", "funkgrid", "signstamp"]

# ─── Shared helpers ───────────────────────────────────────────────────────────

def _clip_circle(dwg: svgwrite.Drawing) -> str:
    """Add a full-canvas circle clip-path to defs; return its id."""
    cid = "cc"
    cp  = dwg.defs.add(dwg.clipPath(id=cid))
    cp.add(dwg.circle(center=(CX, CY), r=R))
    return cid


def _bg(g, dwg: svgwrite.Drawing, color: str) -> None:
    g.add(dwg.circle(center=(CX, CY), r=R, fill=color))


def _chord(dist: float) -> float:
    """Full chord width of the master circle at `dist` pixels from centre."""
    return 2 * math.sqrt(max(R * R - dist * dist, 0))


def _halo_color(c: dict, fill: str) -> str:
    """Pick a contrasting halo color from the palette for readable text overlays."""
    if fill == c["bg"]:
        return c["fg"]
    return c["bg"]


def _text(g, dwg: svgwrite.Drawing, txt: str, x: float, y: float,
          font_size: int, fill: str, letter_spacing: int = 0,
          c: dict | None = None, halo: bool = True,
          halo_scale: float = 0.08) -> None:
    if halo and c is not None:
        g.add(dwg.text(
            txt, insert=(x, y),
            font_size=font_size,
            font_family="Georgia, serif",
            font_weight="bold",
            fill="none",
            stroke=_halo_color(c, fill),
            stroke_width=max(2, int(font_size * halo_scale)),
            stroke_opacity=0.9,
            text_anchor="middle",
            dominant_baseline="central",
            letter_spacing=letter_spacing,
        ))

    g.add(dwg.text(
        txt, insert=(x, y),
        font_size=font_size,
        font_family="Georgia, serif",
        font_weight="bold",
        fill=fill,
        text_anchor="middle",
        dominant_baseline="central",
        letter_spacing=letter_spacing,
    ))


def _arc_chars(g, dwg: svgwrite.Drawing, text: str, r: float,
               centre_deg: float, font_size: int, fill: str,
               c: dict | None = None, halo: bool = True,
               halo_scale: float = 0.075) -> None:
    """
    Place each character individually along a circular arc.
    centre_deg = 0 means the text is centred at the top of the circle.
    Characters are tangent to the arc and read clockwise.
    """
    def char_px(ch: str) -> float:
        if ch == " ":        return font_size * 0.32
        if ch in "IJijlf1": return font_size * 0.38
        if ch in "MWmw":    return font_size * 0.72
        return font_size * 0.60

    widths   = [char_px(ch) for ch in text]
    gap_px   = font_size * 0.09
    total_px = sum(widths) + gap_px * (len(text) - 1)

    # centre_deg 0 = top → math angle = −π/2
    centre_math = math.radians(centre_deg) - math.pi / 2
    cur_rad     = centre_math - (total_px / 2) / r

    for ch, w in zip(text, widths):
        mid     = cur_rad + (w / 2) / r
        x       = CX + r * math.cos(mid)
        y       = CY + r * math.sin(mid)
        rot_deg = math.degrees(mid) + 90        # tangent rotation
        if halo and c is not None:
            g.add(dwg.text(
                ch, insert=(x, y),
                font_size=font_size,
                font_family="Georgia, serif",
                font_weight="bold",
                fill="none",
                stroke=_halo_color(c, fill),
                stroke_width=max(2, int(font_size * halo_scale)),
                stroke_opacity=0.9,
                text_anchor="middle",
                dominant_baseline="central",
                transform=f"rotate({rot_deg:.2f},{x:.2f},{y:.2f})",
            ))

        g.add(dwg.text(
            ch, insert=(x, y),
            font_size=font_size,
            font_family="Georgia, serif",
            font_weight="bold",
            fill=fill,
            text_anchor="middle",
            dominant_baseline="central",
            transform=f"rotate({rot_deg:.2f},{x:.2f},{y:.2f})",
        ))
        cur_rad += (w + gap_px) / r


# ─── Depth, texture & ornament helpers ───────────────────────────────────────

def _ensure_grain_filter(dwg: svgwrite.Drawing, freq: float = 0.9,
                         opacity: float = 0.16) -> str:
    """Lazily add a fractal-noise filter to defs; return its url(#id) reference."""
    fid = f"grain_{int(freq*100)}_{int(opacity*100)}"
    if fid not in getattr(dwg, "_grain_ids", set()):
        f = dwg.defs.add(dwg.filter(id=fid, x="-5%", y="-5%",
                                    width="110%", height="110%"))
        f.feTurbulence(type_="fractalNoise", baseFrequency=str(freq),
                       numOctaves="2", seed="7", stitchTiles="stitch")
        f.feColorMatrix(type_="matrix", values=(
            f"0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 {opacity} 0"
        ))
        dwg._grain_ids = getattr(dwg, "_grain_ids", set()) | {fid}
    return f"url(#{fid})"


def _grain_overlay(g, dwg: svgwrite.Drawing, opacity: float = 0.18) -> None:
    """Add a soft printed-paper grain over the current circle."""
    fid = _ensure_grain_filter(dwg, freq=0.95, opacity=opacity)
    g.add(dwg.circle(center=(CX, CY), r=R, fill="#ffffff", filter=fid,
                     style="mix-blend-mode:multiply"))


def _vignette(g, dwg: svgwrite.Drawing, opacity: float = 0.35) -> None:
    """Soft dark edge vignette for depth."""
    vid = "vig_overlay"
    if vid not in getattr(dwg, "_vignette_ids", set()):
        rg = dwg.defs.add(dwg.radialGradient(
            id=vid, center=(CX, CY), r=R, focal=(CX, CY),
            gradientUnits="userSpaceOnUse",
        ))
        rg.add_stop_color(0.0, "#000000", 0)
        rg.add_stop_color(0.62, "#000000", 0)
        rg.add_stop_color(1.0, "#000000", opacity)
        dwg._vignette_ids = getattr(dwg, "_vignette_ids", set()) | {vid}
    g.add(dwg.circle(center=(CX, CY), r=R, fill=f"url(#{vid})"))


def _inner_highlight(g, dwg: svgwrite.Drawing, c: dict, r: float,
                      width: float = 2, opacity: float = 0.45) -> None:
    """Thin highlight ring just inside an outer band — adds depth."""
    g.add(dwg.circle(center=(CX, CY), r=r, fill="none",
                     stroke=c["ac"], stroke_width=width,
                     stroke_opacity=opacity))


def _perimeter_marks(g, dwg: svgwrite.Drawing, color: str, n: int = 24,
                      r: float = R - 36, dot_r: float = 3.2,
                      skip_top: int = 0) -> None:
    """Evenly spaced ornament dots around the perimeter.

    skip_top: number of dots to omit from the top arc (clears space for text).
    """
    half_skip = skip_top // 2
    for i in range(n):
        if half_skip and (i < half_skip or i > n - half_skip - 1):
            continue
        rad = math.radians(i * (360 / n) - 90)
        x = CX + r * math.cos(rad)
        y = CY + r * math.sin(rad)
        g.add(dwg.circle(center=(x, y), r=dot_r, fill=color))


def _compass_marks(g, dwg: svgwrite.Drawing, color: str, r: float,
                    size: float = 10, opacity: float = 0.9) -> None:
    """Four diamond ornaments at N/E/S/W."""
    for deg in (0, 90, 180, 270):
        rad = math.radians(deg - 90)
        x = CX + r * math.cos(rad)
        y = CY + r * math.sin(rad)
        pts = [(x, y - size), (x + size, y), (x, y + size), (x - size, y)]
        g.add(dwg.polygon(points=pts, fill=color, opacity=opacity))


def _starburst(g, dwg: svgwrite.Drawing, x: float, y: float, r_out: float,
                r_in: float, points: int, fill: str,
                opacity: float = 1.0) -> None:
    """Pointed starburst ornament."""
    pts = []
    for i in range(points * 2):
        rr = r_out if i % 2 == 0 else r_in
        a = math.radians(i * (360 / (points * 2)) - 90)
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    g.add(dwg.polygon(points=pts, fill=fill, opacity=opacity))


def _radial_spokes(g, dwg: svgwrite.Drawing, color: str, n: int,
                    r_in: float, r_out: float, width: float = 2,
                    opacity: float = 0.55) -> None:
    """Radial spokes from r_in to r_out."""
    for i in range(n):
        rad = math.radians(i * (360 / n) - 90)
        x1, y1 = CX + r_in  * math.cos(rad), CY + r_in  * math.sin(rad)
        x2, y2 = CX + r_out * math.cos(rad), CY + r_out * math.sin(rad)
        g.add(dwg.line(start=(x1, y1), end=(x2, y2),
                       stroke=color, stroke_width=width,
                       stroke_opacity=opacity))


def _ensure_glow_filter(dwg: svgwrite.Drawing, color: str,
                         std_dev: float = 4.5) -> str:
    """Soft Gaussian blur filter for phosphor / glow effects."""
    cid = color.lstrip("#")
    fid = f"glow_{cid}_{int(std_dev*10)}"
    if fid not in getattr(dwg, "_glow_ids", set()):
        f = dwg.defs.add(dwg.filter(id=fid, x="-30%", y="-30%",
                                    width="160%", height="160%"))
        f.feGaussianBlur(stdDeviation=str(std_dev))
        dwg._glow_ids = getattr(dwg, "_glow_ids", set()) | {fid}
    return f"url(#{fid})"


def _ensure_halftone_pattern(dwg: svgwrite.Drawing, color: str,
                              tile: int = 20, dot_r: float = 2.4,
                              opacity: float = 0.45) -> str:
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


# ─── Design 1: STACK ──────────────────────────────────────────────────────────
# OLIVE / STREET / BAND in large stacked bold type — pure typography.
# Accent rules with end diamonds separate the three words.

def draw_stack(dwg: svgwrite.Drawing, c: dict) -> None:
    cid = _clip_circle(dwg)
    g   = dwg.add(dwg.g(clip_path=f"url(#{cid})"))
    _bg(g, dwg, c["bg"])

    # Subtle halftone wash for printed-paper depth
    g.add(dwg.circle(center=(CX, CY), r=R,
                     fill=_ensure_halftone_pattern(dwg, c["fg"], tile=22,
                                                    dot_r=1.3, opacity=0.13)))

    # Outer accent ring + thin inner highlight
    g.add(dwg.circle(center=(CX, CY), r=R - 15,
                     fill="none", stroke=c["ac"], stroke_width=7))
    _inner_highlight(g, dwg, c, r=R - 26, width=1.4, opacity=0.55)

    # Decorative perimeter dots, leaving the top + bottom clear for type
    _perimeter_marks(g, dwg, c["ac"], n=24, r=R - 36, dot_r=2.6, skip_top=10)

    # Vertical layout — generous gaps so nothing touches
    fs_outer  = 130    # OLIVE and BAND
    fs_street = 148    # STREET
    rule_w    = 400
    rule_h    = 5
    diam      = 10
    y_olive   = CY - 190
    y_r1      = CY - 100
    y_street  = CY
    y_r2      = CY + 100
    y_band    = CY + 190

    # Accent rules + end diamonds
    for ry in (y_r1, y_r2):
        g.add(dwg.rect(insert=(CX - rule_w // 2, ry - rule_h // 2),
                       size=(rule_w, rule_h), fill=c["ac"]))
        for dx in (-rule_w // 2 - diam - 4, rule_w // 2 + diam + 4):
            pts = [
                (CX + dx,        ry - diam),
                (CX + dx + diam, ry),
                (CX + dx,        ry + diam),
                (CX + dx - diam, ry),
            ]
            g.add(dwg.polygon(points=pts, fill=c["ac"]))

    _text(g, dwg, "OLIVE",  CX, y_olive,  fs_outer,  c["fg"], letter_spacing=10, c=c)
    _text(g, dwg, "STREET", CX, y_street, fs_street, c["fg"], letter_spacing=8, c=c)
    _text(g, dwg, "BAND",   CX, y_band,   fs_outer,  c["ac"], letter_spacing=14, c=c)

    # Tiny "EST · 2026" star bar at the bottom edge
    _text(g, dwg, "★ EST · 2026 ★", CX, CY + 320, 28, c["ac"], c=c)

    _vignette(g, dwg, opacity=0.22)


# ─── Design 2: ARC ────────────────────────────────────────────────────────────
# "OLIVE STREET BAND" curved along the top arc.
# Bold EQ-style vertical bars fill the lower centre.

def draw_arc(dwg: svgwrite.Drawing, c: dict) -> None:
    cid = _clip_circle(dwg)
    g   = dwg.add(dwg.g(clip_path=f"url(#{cid})"))
    _bg(g, dwg, c["bg"])

    # Halftone wash for warmth
    g.add(dwg.circle(center=(CX, CY), r=R,
                     fill=_ensure_halftone_pattern(dwg, c["fg"], tile=22,
                                                    dot_r=1.3, opacity=0.13)))

    # Double outer ring + thin highlight inside
    g.add(dwg.circle(center=(CX, CY), r=R - 15,
                     fill="none", stroke=c["ac"], stroke_width=7))
    _inner_highlight(g, dwg, c, r=R - 26, width=1.4, opacity=0.5)
    g.add(dwg.circle(center=(CX, CY), r=R - 46,
                     fill="none", stroke=c["ac"], stroke_width=2))

    # Tick marks — bottom 240° only; leave top 120° clear for arc text
    # In loop: i=0 is top. Skip i=0..9 and i=51..59 (±60° from top).
    for i in range(60):
        if i < 10 or i > 50:
            continue
        major  = (i % 5 == 0)
        r_out  = R - 17
        r_in   = r_out - (18 if major else 9)
        rad    = math.radians(i * 6 - 90)
        g.add(dwg.line(
            start=(CX + r_out * math.cos(rad), CY + r_out * math.sin(rad)),
            end  =(CX + r_in  * math.cos(rad), CY + r_in  * math.sin(rad)),
            stroke=c["ac"], stroke_width=(3.5 if major else 1.5),
        ))

    # EQ bars — bold vertical bars in the lower half, with caps + reflection.
    bar_heights = [0.50, 0.70, 0.85, 0.95, 1.00, 0.92, 0.80, 0.65, 0.45]
    n_bars  = len(bar_heights)
    bar_w   = 44
    gap     = 14
    total_w = n_bars * bar_w + (n_bars - 1) * gap
    bot_y   = CY + 255
    max_h   = 240

    # Baseline rule under the bars
    g.add(dwg.line(start=(CX - total_w / 2 - 12, bot_y + 4),
                   end=(CX + total_w / 2 + 12, bot_y + 4),
                   stroke=c["ac"], stroke_width=4))

    for i, h in enumerate(bar_heights):
        bh = int(max_h * h)
        bx = CX - total_w / 2 + i * (bar_w + gap)
        by = bot_y - bh
        # Faded mirror reflection beneath baseline
        ref_h = int(bh * 0.32)
        g.add(dwg.rect(insert=(bx, bot_y + 6), size=(bar_w, ref_h),
                       fill=c["fg"], opacity=0.18, rx=3))
        # Main bar with darker base shadow
        g.add(dwg.rect(insert=(bx, by),      size=(bar_w, bh), fill=c["fg"], rx=4))
        g.add(dwg.rect(insert=(bx + 4, by + bh - 8), size=(bar_w - 8, 8),
                       fill=c["ac"], opacity=0.35, rx=2))
        # Bright cap
        g.add(dwg.rect(insert=(bx, by - 11), size=(bar_w, 11), fill=c["ac"], rx=3))
        # Tiny LED dot on every cap
        g.add(dwg.circle(center=(bx + bar_w / 2, by - 5), r=2.4, fill=c["bg"]))

    # Band name arced along the top
    _arc_chars(g, dwg, BAND_NAME, r=400, centre_deg=0,
               font_size=70, fill=c["fg"], c=c)

    # Bottom ornament — diamond bullets with rule
    g.add(dwg.line(start=(CX - 200, CY + 316), end=(CX - 60, CY + 316),
                   stroke=c["ac"], stroke_width=2))
    g.add(dwg.line(start=(CX + 60, CY + 316), end=(CX + 200, CY + 316),
                   stroke=c["ac"], stroke_width=2))
    _text(g, dwg, "★ ★ ★", CX, CY + 318, 30, c["ac"], c=c)

    _vignette(g, dwg, opacity=0.22)


# ─── Design 3: STRIPE ─────────────────────────────────────────────────────────
# A wide horizontal stripe in the fg colour crosses the centre.
# Band name is reversed out of the stripe.
# Decorative fading rules fill the top and bottom caps.

def draw_stripe(dwg: svgwrite.Drawing, c: dict) -> None:
    cid = _clip_circle(dwg)
    g   = dwg.add(dwg.g(clip_path=f"url(#{cid})"))
    _bg(g, dwg, c["bg"])

    # Halftone wash across the whole circle
    g.add(dwg.circle(center=(CX, CY), r=R,
                     fill=_ensure_halftone_pattern(dwg, c["fg"], tile=22,
                                                    dot_r=1.3, opacity=0.13)))

    sh = 260             # stripe height — tall enough to hold two lines with breathing room
    sy = CY - sh // 2   # stripe top y

    # Stripe fill
    g.add(dwg.rect(insert=(0, sy), size=(SIZE, sh), fill=c["fg"]))

    # Accent borders on top and bottom edge of stripe
    for by in (sy - 6, sy + sh - 4):
        g.add(dwg.rect(insert=(0, by), size=(SIZE, 10), fill=c["ac"]))

    # Text inside stripe — two lines with ~40px gap between them
    # "OLIVE STREET" centred at CY-60, "BAND" centred at CY+68
    _text(g, dwg, "OLIVE STREET", CX, CY - 60, 86, c["bg"], letter_spacing=4, c=c)
    _text(g, dwg, "BAND",         CX, CY + 68, 76, c["ac"], letter_spacing=14, c=c)

    # Fading horizontal rules above the stripe
    base_above = sh // 2
    for i in range(5):
        dist = base_above + 36 + i * 44
        w    = _chord(dist) * 0.86
        if w > 40:
            g.add(dwg.rect(
                insert=(CX - w / 2, CY - dist - 3),
                size=(w, 6), fill=c["ac"],
                opacity=str(round(0.55 - i * 0.10, 2)),
            ))

    # Fading horizontal rules below the stripe
    base_below = sh // 2
    for i in range(5):
        dist = base_below + 36 + i * 44
        w    = _chord(dist) * 0.86
        if w > 40:
            g.add(dwg.rect(
                insert=(CX - w / 2, CY + dist - 3),
                size=(w, 6), fill=c["ac"],
                opacity=str(round(0.55 - i * 0.10, 2)),
            ))

    # Star ornament corners flanking the stripe text
    for sx in (CX - 380, CX + 380):
        _starburst(g, dwg, sx, CY, r_out=18, r_in=7, points=4, fill=c["ac"])

    _vignette(g, dwg, opacity=0.22)

    # Outer accent ring + thin highlight inset
    g.add(dwg.circle(center=(CX, CY), r=R - 15,
                     fill="none", stroke=c["ac"], stroke_width=7))
    _inner_highlight(g, dwg, c, r=R - 26, width=1.4, opacity=0.5)


# ─── Design 4: TARGET ─────────────────────────────────────────────────────────
# Bullseye concentric rings (bg/fg alternating).
# A solid accent-colour bar crosses the centre; band name inside the bar.

def draw_target(dwg: svgwrite.Drawing, c: dict) -> None:
    cid = _clip_circle(dwg)
    g   = dwg.add(dwg.g(clip_path=f"url(#{cid})"))

    # Concentric rings, outermost first
    n_rings = 8
    for i in range(n_rings, 0, -1):
        col = c["fg"] if i % 2 == 0 else c["bg"]
        g.add(dwg.circle(center=(CX, CY),
                         r=int(R * i / n_rings), fill=col))

    # Outer accent ring + thin inner highlight for depth
    g.add(dwg.circle(center=(CX, CY), r=R - 11,
                     fill="none", stroke=c["ac"], stroke_width=11))
    _inner_highlight(g, dwg, c, r=R - 24, width=1.4, opacity=0.55)

    # Crosshair tick marks at the four cardinal points (over the rings)
    for deg in (0, 90, 180, 270):
        rad = math.radians(deg - 90)
        x_in,  y_in  = CX + (R - 28) * math.cos(rad), CY + (R - 28) * math.sin(rad)
        x_out, y_out = CX + (R - 60) * math.cos(rad), CY + (R - 60) * math.sin(rad)
        g.add(dwg.line(start=(x_in, y_in), end=(x_out, y_out),
                       stroke=c["ac"], stroke_width=4))

    # Text bar (accent fill) with thin fg edges for solidity.
    bh = 230
    by = CY - bh // 2
    g.add(dwg.rect(insert=(0, by), size=(SIZE, bh), fill=c["ac"]))
    g.add(dwg.rect(insert=(0, by - 5), size=(SIZE, 5), fill=c["fg"]))
    g.add(dwg.rect(insert=(0, by + bh), size=(SIZE, 5), fill=c["fg"]))

    # End-of-bar bullseye ornaments
    for dot_x in (96, SIZE - 96):
        g.add(dwg.circle(center=(dot_x, CY), r=12, fill=c["bg"]))
        g.add(dwg.circle(center=(dot_x, CY), r=5,  fill=c["ac"]))

    # Two-line text — sized to clear the bar with breathing room.
    _text(g, dwg, "OLIVE STREET", CX, CY - 44, 76, c["bg"],
          letter_spacing=3, c=c, halo=False)
    g.add(dwg.line(start=(CX - 170, CY + 8), end=(CX + 170, CY + 8),
                   stroke=c["bg"], stroke_width=2, stroke_opacity=0.55))
    _text(g, dwg, "BAND", CX, CY + 56, 60, c["bg"],
          letter_spacing=12, c=c, halo=False)

    _vignette(g, dwg, opacity=0.22)


# ─── Design 5: SPLIT ──────────────────────────────────────────────────────────
# Circle cut horizontally in half: top = bg colour, bottom = fg colour.
# "OLIVE STREET" sits in the top half; "BAND" in the bottom half.
# Thick accent line at the divide; outer accent ring.

def draw_split(dwg: svgwrite.Drawing, c: dict) -> None:
    cid = _clip_circle(dwg)
    g   = dwg.add(dwg.g(clip_path=f"url(#{cid})"))

    # Top half — bg colour
    _bg(g, dwg, c["bg"])

    # Bottom half — fg colour
    g.add(dwg.rect(insert=(0, CY), size=(SIZE, SIZE), fill=c["fg"]))

    # Halftone wash on the top half (subtle texture)
    g.add(dwg.rect(insert=(0, 0), size=(SIZE, CY),
                   fill=_ensure_halftone_pattern(dwg, c["fg"], tile=22,
                                                  dot_r=1.3, opacity=0.18)))
    # Halftone on the bottom half (using bg colour)
    g.add(dwg.rect(insert=(0, CY), size=(SIZE, CY),
                   fill=_ensure_halftone_pattern(dwg, c["bg"], tile=22,
                                                  dot_r=1.3, opacity=0.18)))

    # Decorative stars in the top half corners
    _starburst(g, dwg, CX - 320, CY - 320, r_out=18, r_in=7, points=4, fill=c["ac"])
    _starburst(g, dwg, CX + 320, CY - 320, r_out=18, r_in=7, points=4, fill=c["ac"])

    # Tiny accent dots in the bottom half flanking BAND
    for dx in (-360, 360):
        g.add(dwg.circle(center=(CX + dx, CY + 175), r=10, fill=c["ac"]))

    # Accent dividing line — with end ornaments
    g.add(dwg.rect(insert=(0, CY - 6), size=(SIZE, 12), fill=c["ac"]))
    for dx in (-1, 1):
        x = CX + dx * 460
        g.add(dwg.polygon(points=[(x, CY - 18), (x + dx * 18, CY),
                                    (x, CY + 18), (x - dx * 18, CY)],
                          fill=c["ac"]))

    # Outer accent ring + thin highlight inset
    g.add(dwg.circle(center=(CX, CY), r=R - 13,
                     fill="none", stroke=c["ac"], stroke_width=8))
    _inner_highlight(g, dwg, c, r=R - 26, width=1.4, opacity=0.5)

    # Top half: OLIVE and STREET — both fully above the divider at CY.
    # OLIVE centred at CY-305, font 130 → spans CY-370 to CY-240.
    # STREET centred at CY-155, font 110 → spans CY-210 to CY-100.
    # Both lines are above CY with ~30px gap between them.
    _text(g, dwg, "OLIVE",  CX, CY - 305, 130, c["fg"], letter_spacing=8, c=c)
    _text(g, dwg, "STREET", CX, CY - 155, 110, c["fg"], letter_spacing=5, c=c)

    # Bottom half: BAND — fully below the divider.
    # Centred at CY+175, font 148 → spans CY+101 to CY+249.
    _text(g, dwg, "BAND", CX, CY + 175, 148, c["bg"], letter_spacing=12, c=c)


# ─── Design 6: WAVEFIELD ─────────────────────────────────────────────────────
# 11 horizontal waveforms distributed evenly top-to-bottom across the full circle.
# Amplitude envelope: quiet at the top and bottom edges, loudest through the
# centre — like viewing a real audio waveform from the side.
# The band name arcs once along the top. Nothing else.

def draw_wavefield(dwg: svgwrite.Drawing, c: dict) -> None:
    cid = _clip_circle(dwg)
    g = dwg.add(dwg.g(clip_path=f"url(#{cid})"))
    _bg(g, dwg, c["bg"])

    # Concentric calibration rings sit behind the waveforms for depth
    for rr, op, w in ((R - 70, 0.18, 1.4), (R - 150, 0.12, 1.2),
                      (R - 230, 0.10, 1.2)):
        g.add(dwg.circle(center=(CX, CY), r=rr, fill="none",
                         stroke=c["fg"], stroke_width=w, stroke_opacity=op))

    # Centre band that the loudest waves sit on — sets the horizon
    band_h = 18
    g.add(dwg.rect(insert=(0, CY - band_h / 2), size=(SIZE, band_h),
                   fill=c["ac"], opacity=0.18))
    g.add(dwg.line(start=(60, CY), end=(SIZE - 60, CY),
                   stroke=c["ac"], stroke_width=1.6, stroke_opacity=0.55,
                   stroke_dasharray="2,8"))

    # Tighter spacing + chunkier strokes so the waves actually read at thumbnail size.
    n_waves = 13
    y_step = 62
    half = (n_waves - 1) / 2
    for i in range(n_waves):
        y_off = -half * y_step + i * y_step
        t = abs(i - half) / half       # 0 at centre → 1 at top/bottom edge
        amp = 12 + 56 * math.cos(t * math.pi / 2) ** 2
        freq = 1.3 + (1 - t) * 0.7
        phase = i * 0.95

        points = []
        for x in range(-60, SIZE + 61, 8):
            xn = x / SIZE
            y = CY + y_off
            y += amp        * math.sin(2 * math.pi * freq * xn + phase)
            y += amp * 0.32 * math.sin(2 * math.pi * freq * 2.4 * xn - phase * 0.6)
            y += amp * 0.12 * math.sin(2 * math.pi * freq * 4.7 * xn + phase * 1.3)
            points.append((x, y))

        if i in (5, 6, 7):
            color, width, opacity = c["ac"], 12, 0.95
        elif i in (4, 8):
            color, width, opacity = c["ac"], 8, 0.78
        elif i in (3, 9):
            color, width, opacity = c["fg"], 6, 0.78
        elif i in (2, 10):
            color, width, opacity = c["fg"], 4, 0.62
        else:
            color, width, opacity = c["fg"], 2.4, 0.48

        g.add(dwg.polyline(
            points=points, fill="none",
            stroke=color, stroke_width=width,
            stroke_opacity=opacity,
            stroke_linecap="round", stroke_linejoin="round",
        ))

    # Centre amplitude markers (left + right of the loud band)
    for sign in (-1, 1):
        x = CX + sign * 230
        g.add(dwg.line(start=(x, CY - 6), end=(x, CY + 6),
                       stroke=c["ac"], stroke_width=3))

    # Curved title with bracket diamonds at either side of the arc
    _arc_chars(g, dwg, BAND_NAME, r=450, centre_deg=0,
               font_size=60, fill=c["fg"], c=c)
    for ang in (-58, 58):
        rad = math.radians(ang - 90)
        x = CX + 450 * math.cos(rad)
        y = CY + 450 * math.sin(rad)
        pts = [(x, y - 8), (x + 8, y), (x, y + 8), (x - 8, y)]
        g.add(dwg.polygon(points=pts, fill=c["ac"]))

    _vignette(g, dwg, opacity=0.28)

    # Outer accent ring + thin highlight inset
    g.add(dwg.circle(center=(CX, CY), r=R - 14,
                     fill="none", stroke=c["ac"], stroke_width=8))
    _inner_highlight(g, dwg, c, r=R - 26, width=1.5, opacity=0.55)


# ─── Design 7: RIPPLE ────────────────────────────────────────────────────────
# 5 closed radial ripple rings emanate from the centre of the circle.
# Each ring is a lightly undulating closed curve — like sound propagating
# outward through air. The undulation amplitude decays with radius so inner
# rings are more energetic, outer rings almost circular.
# The band name arcs once just inside the outer ring. Centre is pure graphic.

def draw_ripple(dwg: svgwrite.Drawing, c: dict) -> None:
    cid = _clip_circle(dwg)
    g = dwg.add(dwg.g(clip_path=f"url(#{cid})"))
    _bg(g, dwg, c["bg"])

    # More rings, denser cadence — reads as energy radiating from the centre.
    ring_radii = [70, 120, 170, 222, 275, 328, 381, 432]

    for idx, base_r in enumerate(ring_radii):
        amp = 5 + 6 * (1 - base_r / R) ** 1.8
        f1, f2 = 8, 14
        phase = idx * 1.05

        points = []
        for deg in range(0, 361, 2):
            t = math.radians(deg)
            r_wave = base_r
            r_wave += amp       * math.sin(f1 * t + phase)
            r_wave += amp * 0.4 * math.sin(f2 * t - phase * 0.8)
            points.append((CX + r_wave * math.cos(t),
                           CY + r_wave * math.sin(t)))

        # Alternate accent / foreground; thicker toward the centre for impact.
        accent = (idx % 2 == 0)
        color = c["ac"] if accent else c["fg"]
        width = max(2.2, 7.5 - idx * 0.55)
        opacity = max(0.55, 0.95 - idx * 0.05)

        g.add(dwg.polyline(
            points=points, fill="none",
            stroke=color, stroke_width=width,
            stroke_opacity=opacity,
            stroke_linecap="round", stroke_linejoin="round",
        ))

    # Centre medallion — solid disc with a starburst, anchors the composition.
    g.add(dwg.circle(center=(CX, CY), r=46, fill=c["ac"],
                     stroke=c["bg"], stroke_width=4))
    _starburst(g, dwg, CX, CY, r_out=30, r_in=11, points=8, fill=c["bg"])
    g.add(dwg.circle(center=(CX, CY), r=8, fill=c["ac"]))

    # Cardinal tick marks on the outer ring
    tick_r_out = R - 18
    tick_r_in  = tick_r_out - 26
    for deg in (0, 90, 180, 270):
        t = math.radians(deg - 90)
        g.add(dwg.line(
            start=(CX + tick_r_in  * math.cos(t), CY + tick_r_in  * math.sin(t)),
            end  =(CX + tick_r_out * math.cos(t), CY + tick_r_out * math.sin(t)),
            stroke=c["ac"], stroke_width=5,
        ))

    # Twelve secondary perimeter dots between cardinals
    _perimeter_marks(g, dwg, c["ac"], n=24, r=R - 30, dot_r=2.4)

    _arc_chars(g, dwg, BAND_NAME, r=478, centre_deg=0,
               font_size=52, fill=c["fg"], c=c)

    _vignette(g, dwg, opacity=0.28)

    g.add(dwg.circle(center=(CX, CY), r=R - 14,
                     fill="none", stroke=c["ac"], stroke_width=7))
    _inner_highlight(g, dwg, c, r=R - 26, width=1.5, opacity=0.5)


# ─── Design 8: SCOPE ─────────────────────────────────────────────────────────
# Oscilloscope dial badge with radial calibration ticks and a waveform trace.

def draw_scope(dwg: svgwrite.Drawing, c: dict) -> None:
    cid = _clip_circle(dwg)
    g = dwg.add(dwg.g(clip_path=f"url(#{cid})"))
    _bg(g, dwg, c["bg"])

    # Subtle halftone wash for paper feel
    g.add(dwg.circle(center=(CX, CY), r=R,
                     fill=_ensure_halftone_pattern(dwg, c["fg"], tile=24,
                                                    dot_r=1.4, opacity=0.14)))

    # Dial rings
    g.add(dwg.circle(center=(CX, CY), r=R - 15,
                     fill="none", stroke=c["ac"], stroke_width=8))
    _inner_highlight(g, dwg, c, r=R - 27, width=1.4, opacity=0.5)
    g.add(dwg.circle(center=(CX, CY), r=R - 58,
                     fill="none", stroke=c["fg"], stroke_width=2,
                     stroke_opacity=0.65))

    # Major/minor ticks around the dial
    for i in range(120):
        deg = i * 3
        rad = math.radians(deg - 90)
        major = i % 10 == 0
        r_out = R - 19
        r_in = r_out - (24 if major else 11)
        g.add(dwg.line(
            start=(CX + r_in * math.cos(rad), CY + r_in * math.sin(rad)),
            end=(CX + r_out * math.cos(rad), CY + r_out * math.sin(rad)),
            stroke=c["ac" if major else "fg"],
            stroke_width=(4 if major else 1.6),
            stroke_opacity=(0.9 if major else 0.5),
        ))

    # Scope screen — bezel + recessed inner panel
    screen_w, screen_h = 680, 300
    sx, sy = CX - screen_w / 2, CY - screen_h / 2 + 10
    g.add(dwg.rect(insert=(sx - 10, sy - 10), size=(screen_w + 20, screen_h + 20),
                   rx=28, fill=c["fg"], stroke=c["ac"], stroke_width=4,
                   fill_opacity=0.85))
    g.add(dwg.rect(insert=(sx, sy), size=(screen_w, screen_h),
                   rx=22, fill=c["bg"], stroke=c["fg"], stroke_width=4))

    # Screen graticule
    for i in range(1, 8):
        x = sx + i * (screen_w / 8)
        g.add(dwg.line(start=(x, sy + 14), end=(x, sy + screen_h - 14),
                       stroke=c["fg"], stroke_width=1.2, stroke_opacity=0.22))
    for i in range(1, 6):
        y = sy + i * (screen_h / 5)
        g.add(dwg.line(start=(sx + 14, y), end=(sx + screen_w - 14, y),
                       stroke=c["fg"], stroke_width=1.2, stroke_opacity=0.22))

    # Centreline + axis ticks for additional depth
    g.add(dwg.line(start=(sx + 14, CY + 8), end=(sx + screen_w - 14, CY + 8),
                   stroke=c["fg"], stroke_width=1.4, stroke_opacity=0.4,
                   stroke_dasharray="3,5"))

    # Phosphor waveform trace — outer glow halo + crisp core line
    pts = []
    for x in range(int(sx + 26), int(sx + screen_w - 25), 6):
        xn = (x - sx) / screen_w
        y = CY + 8
        y += 34 * math.sin(2 * math.pi * 2.5 * xn + 0.55)
        y += 15 * math.sin(2 * math.pi * 6.0 * xn - 0.8)
        y +=  6 * math.sin(2 * math.pi * 11.0 * xn + 0.3)
        pts.append((x, y))
    glow = _ensure_glow_filter(dwg, c["ac"], std_dev=5.5)
    g.add(dwg.polyline(points=pts, fill="none", stroke=c["ac"],
                       stroke_width=10, stroke_opacity=0.55,
                       stroke_linecap="round", stroke_linejoin="round",
                       filter=glow))
    g.add(dwg.polyline(points=pts, fill="none", stroke=c["ac"],
                       stroke_width=6, stroke_linecap="round",
                       stroke_linejoin="round"))
    g.add(dwg.polyline(points=pts, fill="none", stroke=c["fg"],
                       stroke_width=1.6, stroke_opacity=0.85,
                       stroke_linecap="round", stroke_linejoin="round"))

    # Tiny corner LEDs on the bezel
    for cx_, cy_ in ((sx + 18, sy + 18), (sx + screen_w - 18, sy + 18)):
        g.add(dwg.circle(center=(cx_, cy_), r=5, fill=c["ac"]))
        g.add(dwg.circle(center=(cx_, cy_), r=2, fill=c["bg"]))

    # Twin knob ornaments below the screen
    for kx in (CX - 200, CX + 200):
        ky = CY + 165
        g.add(dwg.circle(center=(kx, ky), r=22, fill=c["fg"],
                         stroke=c["ac"], stroke_width=3))
        g.add(dwg.line(start=(kx, ky - 18), end=(kx, ky - 8),
                       stroke=c["ac"], stroke_width=4))
        g.add(dwg.circle(center=(kx, ky), r=4, fill=c["ac"]))

    # Label ring + lower readout strip with end caps
    _arc_chars(g, dwg, BAND_NAME, r=392, centre_deg=0,
               font_size=52, fill=c["fg"], c=c, halo=False)
    g.add(dwg.rect(insert=(CX - 215, CY + 218), size=(430, 56),
                   rx=12, fill=c["ac"], stroke=c["bg"], stroke_width=3))
    for cap_x in (CX - 215, CX + 215 - 8):
        g.add(dwg.rect(insert=(cap_x, CY + 226), size=(8, 40),
                       fill=c["bg"], opacity=0.4))
    _text(g, dwg, "★ EST · 2026 ★", CX, CY + 246, 30, c["bg"],
          letter_spacing=3, c=c, halo=False)

    _vignette(g, dwg, opacity=0.25)


# ─── Design 9: BOOMBOX ───────────────────────────────────────────────────────
# Geometric 80s boombox face abstracted into circles, slots, and bars.

def draw_boombox(dwg: svgwrite.Drawing, c: dict) -> None:
    cid = _clip_circle(dwg)
    g = dwg.add(dwg.g(clip_path=f"url(#{cid})"))
    _bg(g, dwg, c["bg"])

    # Halftone wash
    g.add(dwg.circle(center=(CX, CY), r=R,
                     fill=_ensure_halftone_pattern(dwg, c["fg"], tile=22,
                                                    dot_r=1.4, opacity=0.16)))

    # Outer stamp rings
    g.add(dwg.circle(center=(CX, CY), r=R - 14,
                     fill="none", stroke=c["ac"], stroke_width=8))
    _inner_highlight(g, dwg, c, r=R - 26, width=1.4, opacity=0.5)
    g.add(dwg.circle(center=(CX, CY), r=R - 56,
                     fill="none", stroke=c["fg"], stroke_width=2,
                     stroke_opacity=0.55))

    # Antenna jutting up from the top-right of the body
    g.add(dwg.line(start=(CX + 240, CY - 200), end=(CX + 320, CY - 320),
                   stroke=c["ac"], stroke_width=5, stroke_linecap="round"))
    g.add(dwg.circle(center=(CX + 320, CY - 320), r=8, fill=c["ac"]))

    # Carry handle
    g.add(dwg.path(d=f"M {CX - 80} {CY - 195} Q {CX} {CY - 248} {CX + 80} {CY - 195}",
                   fill="none", stroke=c["ac"], stroke_width=8,
                   stroke_linecap="round"))

    # Main boombox body with subtle inner outline
    bw, bh = 720, 430
    bx, by = CX - bw / 2, CY - bh / 2 + 30
    g.add(dwg.rect(insert=(bx, by), size=(bw, bh), rx=30,
                   fill=c["fg"], stroke=c["ac"], stroke_width=8))
    g.add(dwg.rect(insert=(bx + 8, by + 8), size=(bw - 16, bh - 16), rx=24,
                   fill="none", stroke=c["bg"], stroke_width=1.5,
                   stroke_opacity=0.35))

    # Top deck — EQ display with tan bars + accent bar caps
    g.add(dwg.rect(insert=(bx + 42, by + 40), size=(bw - 84, 100), rx=14,
                   fill=c["bg"], stroke=c["ac"], stroke_width=4))
    bar_pattern = [0.45, 0.7, 0.85, 0.95, 0.78, 0.62, 0.85, 0.95, 0.7, 0.5]
    for i, h_pct in enumerate(bar_pattern):
        x = bx + 58 + i * 62
        h = int(20 + 60 * h_pct)
        bar_y = by + 130 - h
        g.add(dwg.rect(insert=(x, bar_y), size=(38, h),
                       fill=c["ac"], rx=3))
        # bright cap on top
        g.add(dwg.rect(insert=(x, bar_y - 4), size=(38, 5),
                       fill=c["fg"], rx=2))

    # Cassette slot — two reels visible inside the window
    g.add(dwg.rect(insert=(CX - 148, by + 166), size=(296, 88), rx=12,
                   fill=c["bg"], stroke=c["ac"], stroke_width=5))
    g.add(dwg.rect(insert=(CX - 98, by + 195), size=(196, 30), rx=6,
                   fill=c["fg"], stroke="none"))
    for reel_x in (CX - 60, CX + 60):
        g.add(dwg.circle(center=(reel_x, by + 210), r=11,
                         fill=c["bg"], stroke=c["ac"], stroke_width=2))
        # spokes
        for sp in range(6):
            ang = math.radians(sp * 60)
            g.add(dwg.line(
                start=(reel_x + 3 * math.cos(ang), by + 210 + 3 * math.sin(ang)),
                end=(reel_x + 9 * math.cos(ang), by + 210 + 9 * math.sin(ang)),
                stroke=c["ac"], stroke_width=1.4))

    # Tiny play/pause/stop pad icons under the cassette
    pad_y = by + 268
    icon_specs = [("play",  CX - 64), ("pause", CX), ("stop", CX + 64)]
    for kind, ix in icon_specs:
        g.add(dwg.rect(insert=(ix - 18, pad_y - 14), size=(36, 28), rx=5,
                       fill=c["bg"], stroke=c["ac"], stroke_width=2))
        if kind == "play":
            g.add(dwg.polygon(points=[(ix - 5, pad_y - 7), (ix - 5, pad_y + 7),
                                       (ix + 7, pad_y)], fill=c["ac"]))
        elif kind == "pause":
            g.add(dwg.rect(insert=(ix - 6, pad_y - 7), size=(4, 14), fill=c["ac"]))
            g.add(dwg.rect(insert=(ix + 2, pad_y - 7), size=(4, 14), fill=c["ac"]))
        else:
            g.add(dwg.rect(insert=(ix - 6, pad_y - 6), size=(12, 12), fill=c["ac"]))

    # Twin speakers — heavier rim, multiple cone rings, centre dust cap
    speaker_y = by + 360
    for spk_x in (CX - 215, CX + 215):
        g.add(dwg.circle(center=(spk_x, speaker_y), r=110,
                         fill=c["bg"], stroke=c["ac"], stroke_width=6))
        g.add(dwg.circle(center=(spk_x, speaker_y), r=92,
                         fill="none", stroke=c["ac"], stroke_width=2,
                         stroke_opacity=0.5))
        g.add(dwg.circle(center=(spk_x, speaker_y), r=78, fill="none",
                         stroke=c["fg"], stroke_width=8))
        g.add(dwg.circle(center=(spk_x, speaker_y), r=58, fill="none",
                         stroke=c["fg"], stroke_width=6, stroke_opacity=0.75))
        g.add(dwg.circle(center=(spk_x, speaker_y), r=38, fill="none",
                         stroke=c["fg"], stroke_width=4, stroke_opacity=0.55))
        g.add(dwg.circle(center=(spk_x, speaker_y), r=22, fill=c["ac"]))
        g.add(dwg.circle(center=(spk_x, speaker_y), r=8, fill=c["bg"]))
        # mounting screws at NSEW
        for sd in (0, 90, 180, 270):
            ang = math.radians(sd)
            sx_, sy_ = spk_x + 100 * math.cos(ang), speaker_y + 100 * math.sin(ang)
            g.add(dwg.circle(center=(sx_, sy_), r=4, fill=c["ac"]))

    # Volume knob between the speakers
    g.add(dwg.circle(center=(CX, speaker_y), r=38, fill=c["bg"],
                     stroke=c["ac"], stroke_width=4))
    g.add(dwg.circle(center=(CX, speaker_y), r=24, fill=c["ac"]))
    g.add(dwg.line(start=(CX, speaker_y - 28), end=(CX, speaker_y - 16),
                   stroke=c["bg"], stroke_width=4, stroke_linecap="round"))

    # Perimeter title (top arc only — bottom stays clear of upside-down text)
    _arc_chars(g, dwg, BAND_NAME, r=394, centre_deg=0,
               font_size=50, fill=c["fg"], c=c, halo=False)
    # Horizontal "EST · 2026" mark just below the body, inside the bottom rim
    _text(g, dwg, "★ EST · 2026 ★", CX, CY + 478, 26, c["ac"],
          letter_spacing=3, c=c, halo=False)

    _vignette(g, dwg, opacity=0.22)


# ─── Design 10: LATTICE ──────────────────────────────────────────────────────
# Concentric wave lattice using phase-offset ripple circles.

def draw_lattice(dwg: svgwrite.Drawing, c: dict) -> None:
    cid = _clip_circle(dwg)
    g = dwg.add(dwg.g(clip_path=f"url(#{cid})"))
    _bg(g, dwg, c["bg"])

    # Outer band ring + thin inner ring framing the perimeter title
    g.add(dwg.circle(center=(CX, CY), r=R - 16,
                     fill="none", stroke=c["ac"], stroke_width=7))
    g.add(dwg.circle(center=(CX, CY), r=R - 62,
                     fill="none", stroke=c["fg"], stroke_width=2,
                     stroke_opacity=0.62))

    # Halftone wash for warmth + base contrast
    g.add(dwg.circle(center=(CX, CY), r=R - 70,
                     fill=_ensure_halftone_pattern(dwg, c["fg"], tile=20,
                                                    dot_r=1.5, opacity=0.22)))

    # Faint radial spokes for an etched dial feel
    _radial_spokes(g, dwg, c["fg"], n=36, r_in=110, r_out=R - 80,
                   width=1, opacity=0.28)

    # Eight phase-shifted ripple rings — denser & higher contrast than before.
    ring_radii = [122, 168, 214, 260, 306, 350, 392, 432]
    for idx, base_r in enumerate(ring_radii):
        amp = max(2.4, 10 - idx * 1.0)
        phase = idx * 0.9
        points = []
        for deg in range(0, 361, 3):
            t = math.radians(deg)
            rr = base_r
            rr += amp        * math.sin(8 * t + phase)
            rr += amp * 0.45 * math.sin(15 * t - phase * 1.1)
            points.append((CX + rr * math.cos(t), CY + rr * math.sin(t)))
        accent = (idx % 2 == 0)
        color  = c["ac"] if accent else c["fg"]
        width  = 5.5 - idx * 0.35
        op     = max(0.55, 0.95 - idx * 0.05)
        g.add(dwg.polyline(points=points, fill="none", stroke=color,
                           stroke_width=max(2.2, width),
                           stroke_opacity=op,
                           stroke_linejoin="round", stroke_linecap="round"))

    # Centre medallion — concentric dot stack with a star
    g.add(dwg.circle(center=(CX, CY), r=104, fill=c["ac"],
                     stroke=c["bg"], stroke_width=5))
    g.add(dwg.circle(center=(CX, CY), r=88, fill="none",
                     stroke=c["bg"], stroke_width=1.5,
                     stroke_opacity=0.45))
    _text(g, dwg, "BAND", CX, CY, 58, c["bg"], letter_spacing=8,
          c=c, halo=False)

    # Cardinal accent diamonds on the inner thin ring
    _compass_marks(g, dwg, c["ac"], r=R - 62, size=10)

    # Perimeter title (top arc only) + a horizontal star bar at the bottom
    _arc_chars(g, dwg, BAND_NAME, r=R - 40, centre_deg=0,
               font_size=46, fill=c["fg"], c=c, halo=False)
    _text(g, dwg, "★  ★  ★", CX, CY + 478, 30, c["ac"],
          c=c, halo=False)

    _vignette(g, dwg, opacity=0.25)


# ─── Design 11: FUNKGRID ─────────────────────────────────────────────────────
# Syncopated rhythm-block matrix surrounded by a calibrated title ring.

def draw_funkgrid(dwg: svgwrite.Drawing, c: dict) -> None:
    cid = _clip_circle(dwg)
    g = dwg.add(dwg.g(clip_path=f"url(#{cid})"))
    _bg(g, dwg, c["bg"])

    # Subtle halftone wash behind everything for depth
    g.add(dwg.circle(center=(CX, CY), r=R,
                     fill=_ensure_halftone_pattern(dwg, c["fg"], tile=22,
                                                    dot_r=1.5, opacity=0.18)))

    # Outer rings
    g.add(dwg.circle(center=(CX, CY), r=R - 14,
                     fill="none", stroke=c["ac"], stroke_width=8))
    _inner_highlight(g, dwg, c, r=R - 26, width=1.6, opacity=0.55)
    g.add(dwg.circle(center=(CX, CY), r=R - 76,
                     fill="none", stroke=c["fg"], stroke_width=2,
                     stroke_opacity=0.45))

    # Tick ring between the two outer rings (calibration feel)
    for i in range(60):
        deg = i * 6
        rad = math.radians(deg - 90)
        major = i % 5 == 0
        r_out = R - 32
        r_in = r_out - (16 if major else 7)
        g.add(dwg.line(
            start=(CX + r_in * math.cos(rad), CY + r_in * math.sin(rad)),
            end=(CX + r_out * math.cos(rad), CY + r_out * math.sin(rad)),
            stroke=c["ac"] if major else c["fg"],
            stroke_width=(2.6 if major else 1.2),
            stroke_opacity=(0.85 if major else 0.45),
        ))

    # 7×7 groove matrix — accent-filled hits, cream outlines on rests
    grid = 7
    cell = 64
    gap  = 12
    total = grid * cell + (grid - 1) * gap
    ox = CX - total / 2
    oy = CY - total / 2 - 6
    pattern = [
        [1, 0, 0, 1, 0, 1, 0],
        [0, 1, 0, 0, 1, 0, 1],
        [0, 0, 1, 0, 1, 0, 0],
        [1, 0, 1, 0, 0, 1, 0],
        [0, 1, 0, 1, 0, 0, 1],
        [1, 0, 0, 1, 0, 1, 0],
        [0, 1, 0, 0, 1, 0, 1],
    ]
    for r_i in range(grid):
        for col in range(grid):
            x = ox + col * (cell + gap)
            y = oy + r_i * (cell + gap)
            if pattern[r_i][col]:
                # Filled hit with inner highlight chip
                g.add(dwg.rect(insert=(x, y), size=(cell, cell), rx=8,
                               fill=c["ac"]))
                g.add(dwg.rect(insert=(x + 6, y + 6), size=(cell - 12, 8),
                               rx=3, fill=c["fg"], fill_opacity=0.32))
            else:
                g.add(dwg.rect(insert=(x + 12, y + 12),
                               size=(cell - 24, cell - 24),
                               rx=6, fill="none", stroke=c["fg"],
                               stroke_width=2, stroke_opacity=0.55))
                # tiny centre rest dot
                g.add(dwg.circle(center=(x + cell / 2, y + cell / 2),
                                 r=2.4, fill=c["fg"], fill_opacity=0.55))

    # Name ring + lockup banner (drawn ONCE, outside the loops)
    _arc_chars(g, dwg, BAND_NAME, r=398, centre_deg=0,
               font_size=50, fill=c["fg"], c=c, halo=False)

    banner_w, banner_h = 360, 64
    bx = CX - banner_w / 2
    by = CY + 200
    g.add(dwg.rect(insert=(bx, by), size=(banner_w, banner_h),
                   rx=12, fill=c["ac"], stroke=c["bg"], stroke_width=3))
    # banner notch ornaments
    for nx in (bx - 14, bx + banner_w - 6):
        g.add(dwg.polygon(points=[
            (nx, by + 8), (nx + 20, by + banner_h / 2),
            (nx, by + banner_h - 8),
        ], fill=c["ac"]))
    _text(g, dwg, "BAND", CX, by + banner_h / 2, 42, c["bg"],
          letter_spacing=8, c=c, halo=False)

    _vignette(g, dwg, opacity=0.22)


# ─── Design 12: SIGNSTAMP ────────────────────────────────────────────────────
# Abstract street-sign plate inside a circular stamp.

def draw_signstamp(dwg: svgwrite.Drawing, c: dict) -> None:
    cid = _clip_circle(dwg)
    g = dwg.add(dwg.g(clip_path=f"url(#{cid})"))
    _bg(g, dwg, c["bg"])

    # Halftone wash for grit
    g.add(dwg.circle(center=(CX, CY), r=R,
                     fill=_ensure_halftone_pattern(dwg, c["fg"], tile=22,
                                                    dot_r=1.4, opacity=0.16)))

    # Stamp rings + thin highlight inset
    g.add(dwg.circle(center=(CX, CY), r=R - 14,
                     fill="none", stroke=c["ac"], stroke_width=8))
    _inner_highlight(g, dwg, c, r=R - 26, width=1.4, opacity=0.5)
    g.add(dwg.circle(center=(CX, CY), r=R - 56,
                     fill="none", stroke=c["fg"], stroke_width=2,
                     stroke_opacity=0.55))

    # Subtle brick-line + offset stagger texture kept abstract
    for row in range(11):
        y = CY - 360 + row * 65
        w = _chord(abs(y - CY)) * 0.78
        if w < 40:
            continue
        g.add(dwg.line(start=(CX - w / 2, y), end=(CX + w / 2, y),
                       stroke=c["fg"], stroke_width=1.5, stroke_opacity=0.16))
        # vertical brick joins (every other row offset)
        offset = 60 if row % 2 == 0 else 0
        for bx in range(-int(w / 2) + offset, int(w / 2), 120):
            g.add(dwg.line(start=(CX + bx, y), end=(CX + bx, y + 65),
                           stroke=c["fg"], stroke_width=1.2,
                           stroke_opacity=0.13))

    # Rotated sign plate
    plate_w, plate_h = 640, 272
    px, py = CX - plate_w / 2, CY - plate_h / 2 + 30
    plate = dwg.g(transform=f"rotate(-11,{CX},{CY})")
    plate.add(dwg.rect(insert=(px, py), size=(plate_w, plate_h), rx=22,
                       fill=c["fg"], stroke=c["ac"], stroke_width=10))
    plate.add(dwg.rect(insert=(px + 18, py + 18), size=(plate_w - 36, plate_h - 36), rx=14,
                       fill="none", stroke=c["bg"], stroke_width=4, stroke_opacity=0.65))

    # Four bolt details
    for ox, oy in ((52, 50), (plate_w - 52, 50), (52, plate_h - 50), (plate_w - 52, plate_h - 50)):
        plate.add(dwg.circle(center=(px + ox, py + oy), r=12, fill=c["ac"]))
        plate.add(dwg.line(start=(px + ox - 8, py + oy), end=(px + ox + 8, py + oy),
                           stroke=c["bg"], stroke_width=2))
        plate.add(dwg.line(start=(px + ox, py + oy - 8), end=(px + ox, py + oy + 8),
                           stroke=c["bg"], stroke_width=2))

    # Plate text
    plate.add(dwg.text("OLIVE STREET", insert=(CX, CY + 4),
                       text_anchor="middle", dominant_baseline="central",
                       font_family="Georgia, serif", font_size=72,
                       font_weight="bold", fill=c["bg"], letter_spacing=4))
    plate.add(dwg.text("BAND", insert=(CX, CY + 86),
                       text_anchor="middle", dominant_baseline="central",
                       font_family="Georgia, serif", font_size=64,
                       font_weight="bold", fill=c["ac"], letter_spacing=10))
    g.add(plate)

    # Perimeter title (top arc only) + a horizontal star bar at the bottom
    _arc_chars(g, dwg, BAND_NAME, r=402, centre_deg=0,
               font_size=48, fill=c["fg"], c=c, halo=False)
    _text(g, dwg, "★ EST · 2026 ★", CX, CY + 478, 28, c["ac"],
          letter_spacing=3, c=c, halo=False)

    _vignette(g, dwg, opacity=0.22)


# ─── Output / generation ──────────────────────────────────────────────────────

DRAW_FN = {
    "stack":  draw_stack,
    "arc":    draw_arc,
    "stripe": draw_stripe,
    "target": draw_target,
    "split":  draw_split,
    "wavefield": draw_wavefield,
    "ripple": draw_ripple,
    "scope": draw_scope,
    "boombox": draw_boombox,
    "lattice": draw_lattice,
    "funkgrid": draw_funkgrid,
    "signstamp": draw_signstamp,
}


def _out_path(design: str, scheme: str) -> Path:
    folder = OUTPUT_DIR
    folder.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return folder / f"{ts}_profile_{design}_{scheme}.svg"


def _export_png(svg_path: Path) -> None:
    try:
        import cairosvg  # type: ignore
        png = svg_path.with_suffix(".png")
        cairosvg.svg2png(url=str(svg_path), write_to=str(png),
                         output_width=SIZE * 2, output_height=SIZE * 2)
        print(f"  saved → {png.name}")
    except ImportError:
        print("  (cairosvg not installed — skipping PNG export)")


def generate(design: str, scheme: str, png: bool) -> Path:
    c   = COLOR_SCHEMES[scheme]
    out = _out_path(design, scheme)
    dwg = svgwrite.Drawing(str(out), size=(SIZE, SIZE))
    DRAW_FN[design](dwg, c)
    dwg.save()
    print(f"  saved → {out.name}")
    if png:
        _export_png(out)
    return out


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    p = argparse.ArgumentParser(
        description="Generate Olive Street Band social-media profile images")
    p.add_argument("--design", choices=DESIGNS,
                   help="Which design to generate")
    p.add_argument("--scheme", choices=list(COLOR_SCHEMES), default="dark",
                   help="Color scheme (default: dark)")
    p.add_argument("--all", dest="all_designs", action="store_true",
                   help="Generate all designs x 4 schemes")
    p.add_argument("--png", action="store_true",
                   help="Also export PNG at 2× via cairosvg")
    args = p.parse_args()

    if args.all_designs:
        for d in DESIGNS:
            print(f"\n{d}:")
            for s in COLOR_SCHEMES:
                generate(d, s, args.png)
    elif args.design:
        generate(args.design, args.scheme, args.png)
    else:
        p.print_help()


if __name__ == "__main__":
    main()

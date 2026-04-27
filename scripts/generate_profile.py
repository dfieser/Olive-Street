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

DESIGNS = ["stack", "arc", "stripe", "target", "split"]

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


def _text(g, dwg: svgwrite.Drawing, txt: str, x: float, y: float,
          font_size: int, fill: str, letter_spacing: int = 0) -> None:
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
               centre_deg: float, font_size: int, fill: str) -> None:
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


# ─── Design 1: STACK ──────────────────────────────────────────────────────────
# OLIVE / STREET / BAND in large stacked bold type — pure typography.
# Accent rules with end diamonds separate the three words.

def draw_stack(dwg: svgwrite.Drawing, c: dict) -> None:
    cid = _clip_circle(dwg)
    g   = dwg.add(dwg.g(clip_path=f"url(#{cid})"))
    _bg(g, dwg, c["bg"])

    # Outer accent ring
    g.add(dwg.circle(center=(CX, CY), r=R - 15,
                     fill="none", stroke=c["ac"], stroke_width=7))

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

    _text(g, dwg, "OLIVE",  CX, y_olive,  fs_outer,  c["fg"], letter_spacing=10)
    _text(g, dwg, "STREET", CX, y_street, fs_street, c["fg"], letter_spacing=8)
    _text(g, dwg, "BAND",   CX, y_band,   fs_outer,  c["ac"], letter_spacing=14)


# ─── Design 2: ARC ────────────────────────────────────────────────────────────
# "OLIVE STREET BAND" curved along the top arc.
# Bold EQ-style vertical bars fill the lower centre.

def draw_arc(dwg: svgwrite.Drawing, c: dict) -> None:
    cid = _clip_circle(dwg)
    g   = dwg.add(dwg.g(clip_path=f"url(#{cid})"))
    _bg(g, dwg, c["bg"])

    # Double outer ring
    g.add(dwg.circle(center=(CX, CY), r=R - 15,
                     fill="none", stroke=c["ac"], stroke_width=7))
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

    # EQ bars — bold vertical bars in the lower half
    bar_heights = [0.50, 0.70, 0.85, 0.95, 1.00, 0.92, 0.80, 0.65, 0.45]
    n_bars  = len(bar_heights)
    bar_w   = 44
    gap     = 14
    total_w = n_bars * bar_w + (n_bars - 1) * gap
    bot_y   = CY + 255
    max_h   = 240
    for i, h in enumerate(bar_heights):
        bh = int(max_h * h)
        bx = CX - total_w / 2 + i * (bar_w + gap)
        by = bot_y - bh
        g.add(dwg.rect(insert=(bx, by),      size=(bar_w, bh), fill=c["fg"], rx=4))
        g.add(dwg.rect(insert=(bx, by - 11), size=(bar_w, 11), fill=c["ac"], rx=3))

    # Band name arced along the top — r=400 keeps text clear of the inner ring (R-46=494)
    _arc_chars(g, dwg, BAND_NAME, r=400, centre_deg=0,
               font_size=70, fill=c["fg"])

    # Bottom ornament dots
    _text(g, dwg, "◆  ◆  ◆", CX, CY + 318, 30, c["ac"])


# ─── Design 3: STRIPE ─────────────────────────────────────────────────────────
# A wide horizontal stripe in the fg colour crosses the centre.
# Band name is reversed out of the stripe.
# Decorative fading rules fill the top and bottom caps.

def draw_stripe(dwg: svgwrite.Drawing, c: dict) -> None:
    cid = _clip_circle(dwg)
    g   = dwg.add(dwg.g(clip_path=f"url(#{cid})"))
    _bg(g, dwg, c["bg"])

    sh = 260             # stripe height — tall enough to hold two lines with breathing room
    sy = CY - sh // 2   # stripe top y

    # Stripe fill
    g.add(dwg.rect(insert=(0, sy), size=(SIZE, sh), fill=c["fg"]))

    # Accent borders on top and bottom edge of stripe
    for by in (sy - 6, sy + sh - 4):
        g.add(dwg.rect(insert=(0, by), size=(SIZE, 10), fill=c["ac"]))

    # Text inside stripe — two lines with ~40px gap between them
    # "OLIVE STREET" centred at CY-60, "BAND" centred at CY+68
    _text(g, dwg, "OLIVE STREET", CX, CY - 60, 86, c["bg"], letter_spacing=4)
    _text(g, dwg, "BAND",         CX, CY + 68, 76, c["ac"], letter_spacing=14)

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

    # Outer accent ring
    g.add(dwg.circle(center=(CX, CY), r=R - 15,
                     fill="none", stroke=c["ac"], stroke_width=7))


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

    # Accent outer ring
    g.add(dwg.circle(center=(CX, CY), r=R - 11,
                     fill="none", stroke=c["ac"], stroke_width=11))

    # Text bar (accent fill) — tall enough for two lines with 40px gap
    bh = 250
    by = CY - bh // 2
    g.add(dwg.rect(insert=(0, by), size=(SIZE, bh), fill=c["ac"]))

    # Text in bar — reduced font to stay clear of the circle clip edges
    # "OLIVE STREET" at CY-56, font 88 → spans CY-100 to CY-12
    # "BAND" at CY+66, font 76 → spans CY+28 to CY+104
    _text(g, dwg, "OLIVE STREET", CX, CY - 56, 88, c["bg"], letter_spacing=3)
    _text(g, dwg, "BAND",         CX, CY + 66, 76, c["bg"], letter_spacing=14)


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

    # Accent dividing line
    g.add(dwg.rect(insert=(0, CY - 6), size=(SIZE, 12), fill=c["ac"]))

    # Outer accent ring
    g.add(dwg.circle(center=(CX, CY), r=R - 13,
                     fill="none", stroke=c["ac"], stroke_width=8))

    # Top half: OLIVE and STREET — both fully above the divider at CY.
    # OLIVE centred at CY-305, font 130 → spans CY-370 to CY-240.
    # STREET centred at CY-155, font 110 → spans CY-210 to CY-100.
    # Both lines are above CY with ~30px gap between them.
    _text(g, dwg, "OLIVE",  CX, CY - 305, 130, c["fg"], letter_spacing=8)
    _text(g, dwg, "STREET", CX, CY - 155, 110, c["fg"], letter_spacing=5)

    # Bottom half: BAND — fully below the divider.
    # Centred at CY+175, font 148 → spans CY+101 to CY+249.
    _text(g, dwg, "BAND", CX, CY + 175, 148, c["bg"], letter_spacing=12)


# ─── Output / generation ──────────────────────────────────────────────────────

DRAW_FN = {
    "stack":  draw_stack,
    "arc":    draw_arc,
    "stripe": draw_stripe,
    "target": draw_target,
    "split":  draw_split,
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
                   help="Generate all 5 designs × 4 schemes (20 files)")
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

"""
generate_asset.py
-----------------
Generate album art and social media assets as SVG files using pure Python code.
No AI — backgrounds are drawn with programmatic geometric patterns, then
optional text overlays (band name, album/asset title) are composited on top.

Background patterns:
  geometric   — Grid of alternating circles and rotated squares
  halftone    — Dot grid with radius driven by a sine-wave distance function
  lines       — Parallel ruled lines with sinusoidally varying stroke weight
  concentric  — Concentric rectangles radiating from the center
  minimal     — Clean flat canvas with a single offset geometric accent

Asset types and sizes:
  album_art              — 3000 × 3000 px  (square master)
  social instagram       — 1080 × 1080 px
  social twitter         — 1500 × 500 px
  social facebook        — 1200 × 630 px

Color schemes: dark | light | tan | mono

Usage:
  python scripts/generate_asset.py --type album_art --bg geometric --title "First Light"
  python scripts/generate_asset.py --type social --platform instagram --bg halftone
  python scripts/generate_asset.py --type social --platform twitter --bg lines --title "On Tour"
  python scripts/generate_asset.py --type social --all-platforms --bg concentric
  python scripts/generate_asset.py --type album_art --bg minimal --scheme light

Requires:
  pip install svgwrite
  pip install cairosvg   (optional — only needed for --png export)
"""

import argparse
import math
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

# ─── Asset dimensions ─────────────────────────────────────────────────────────

PLATFORM_SIZES: dict[str, tuple[int, int]] = {
    "album_art": (3000, 3000),
    "instagram": (1080, 1080),
    "twitter":   (1500, 500),
    "facebook":  (1200, 630),
}

# ─── Color schemes ────────────────────────────────────────────────────────────
# Palette: Olive Green #6B7A3A | Tan #DDB892 | Cream #F5F0E1

COLOR_SCHEMES: dict[str, dict] = {
    # Dark: olive bg, cream + tan elements  (primary scheme)
    "dark": {
        "background": "#6B7A3A",
        "primary":    "#F5F0E1",
        "accent":     "#DDB892",
        "secondary":  "#DDB892",
        "pattern":    "#7A8C45",  # slightly lighter than bg — for pattern shapes
    },
    # Light: cream bg, olive text  (reversed version)
    "light": {
        "background": "#F5F0E1",
        "primary":    "#6B7A3A",
        "accent":     "#DDB892",
        "secondary":  "#6B7A3A",
        "pattern":    "#E8E0CC",
    },
    # Tan: tan bg, olive text, cream accents
    "tan": {
        "background": "#DDB892",
        "primary":    "#6B7A3A",
        "accent":     "#F5F0E1",
        "secondary":  "#6B7A3A",
        "pattern":    "#C9A47E",
    },
    # Mono: near-black bg, cream text  (single-color legibility test)
    "mono": {
        "background": "#1A1A1A",
        "primary":    "#F5F0E1",
        "accent":     "#F5F0E1",
        "secondary":  "#DDB892",
        "pattern":    "#222222",
    },
}

# ─── Output routing ───────────────────────────────────────────────────────────

def _out_path(asset_type: str, platform: str, bg: str, scheme: str) -> Path:
    if asset_type == "album_art":
        folder = ROOT / "output" / "fliers"
    else:
        folder = ROOT / "output" / "posts"
    folder.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if asset_type == "album_art":
        return folder / f"{ts}_flier_{bg}_{scheme}.svg"
    else:
        return folder / f"{ts}_post_{platform}_{bg}_{scheme}.svg"


# ─── Background patterns ──────────────────────────────────────────────────────

def bg_geometric(dwg: svgwrite.Drawing, c: dict, w: float, h: float) -> None:
    """
    Grid of alternating circles (primary, translucent) and rotated squares
    (accent stroke, no fill) — creates a dense but restrained texture.
    """
    cols = 24
    rows = max(1, round(cols * h / w))
    cw   = w / cols
    ch   = h / rows
    r    = min(cw, ch) * 0.36

    for row in range(rows):
        for col in range(cols):
            cx = (col + 0.5) * cw
            cy = (row + 0.5) * ch
            if (row + col) % 2 == 0:
                dwg.add(dwg.circle(
                    center=(cx, cy), r=r,
                    fill=c["primary"], fill_opacity=0.08,
                    stroke=c["primary"], stroke_width=0.6, stroke_opacity=0.25,
                ))
            else:
                sq = r * 1.05
                dwg.add(dwg.rect(
                    (cx - sq, cy - sq), (sq * 2, sq * 2),
                    fill="none",
                    stroke=c["accent"], stroke_width=0.6, stroke_opacity=0.22,
                    transform=f"rotate(45 {cx} {cy})",
                ))


def bg_halftone(dwg: svgwrite.Drawing, c: dict, w: float, h: float) -> None:
    """
    Dot grid where each circle's radius is modulated by a 2D cosine function
    of its distance from the canvas center — creates a vignette / iris effect.
    """
    spacing = min(w, h) / 30
    cols = int(w / spacing) + 2
    rows = int(h / spacing) + 2
    cx_canvas = w / 2
    cy_canvas = h / 2
    max_dist = math.hypot(cx_canvas, cy_canvas)

    for row in range(rows):
        for col in range(cols):
            x = col * spacing
            y = row * spacing
            dist = math.hypot(x - cx_canvas, y - cy_canvas)
            # Radius varies from 0 to spacing*0.45 driven by a cosine falloff
            t = 1 - (dist / max_dist)
            r = spacing * 0.45 * (0.3 + 0.7 * math.cos(math.pi * (1 - t) * 0.5) ** 2)
            if r > 0.5:
                dwg.add(dwg.circle(
                    center=(x, y), r=r,
                    fill=c["primary"], fill_opacity=0.18,
                ))


def bg_lines(dwg: svgwrite.Drawing, c: dict, w: float, h: float) -> None:
    """
    Horizontal ruled lines. Stroke weight oscillates as a sine function of
    vertical position, producing a soft banding / ripple effect.
    """
    n_lines = int(h / 6)
    cy = h / 2
    for i in range(n_lines):
        y = (i + 0.5) * (h / n_lines)
        dist_norm = abs(y - cy) / cy   # 0 at center, 1 at edges
        # Thin at center, thicker at edges, then thin again
        weight = 0.4 + 1.8 * math.sin(math.pi * dist_norm) ** 2
        opacity = 0.12 + 0.25 * (1 - dist_norm)
        color = c["accent"] if i % 7 == 0 else c["primary"]
        dwg.add(dwg.line(
            (0, y), (w, y),
            stroke=color,
            stroke_width=weight,
            stroke_opacity=opacity,
        ))


def bg_concentric(dwg: svgwrite.Drawing, c: dict, w: float, h: float) -> None:
    """
    Concentric rectangles radiating outward from center.
    Alternates between primary (thin) and accent (ultra-thin) rings.
    """
    cx, cy = w / 2, h / 2
    step = min(w, h) / 28
    max_rings = int(math.hypot(cx, cy) / step) + 2

    for i in range(max_rings):
        rx = i * step * (w / min(w, h))
        ry = i * step * (h / min(w, h))
        is_accent = i % 5 == 0
        dwg.add(dwg.rect(
            (cx - rx, cy - ry), (rx * 2, ry * 2),
            fill="none",
            stroke=c["accent"] if is_accent else c["primary"],
            stroke_width=1.2 if is_accent else 0.5,
            stroke_opacity=0.30 if is_accent else 0.15,
        ))


def bg_minimal(dwg: svgwrite.Drawing, c: dict, w: float, h: float) -> None:
    """
    A single offset geometric accent — a large rectangle displaced toward
    the lower-right — providing structure and tension against the flat background.
    """
    # Offset square / rect
    size = min(w, h) * 0.72
    ox = w * 0.58
    oy = h * 0.52
    dwg.add(dwg.rect(
        (ox, oy), (size, size),
        fill="none",
        stroke=c["primary"], stroke_width=1.5, stroke_opacity=0.15,
    ))
    # Second inner offset rect
    inset = size * 0.06
    dwg.add(dwg.rect(
        (ox + inset, oy + inset), (size - inset * 2, size - inset * 2),
        fill="none",
        stroke=c["accent"], stroke_width=0.75, stroke_opacity=0.20,
    ))
    # Thin horizontal rule at golden ratio height
    phi_y = h * 0.382
    dwg.add(dwg.line(
        (w * 0.08, phi_y), (w * 0.55, phi_y),
        stroke=c["accent"], stroke_width=1, stroke_opacity=0.55,
    ))


BG_FUNCS = {
    "geometric":  bg_geometric,
    "halftone":   bg_halftone,
    "lines":      bg_lines,
    "concentric": bg_concentric,
    "minimal":    bg_minimal,
}

# ─── Text overlay ─────────────────────────────────────────────────────────────

def add_text_overlay(dwg: svgwrite.Drawing, c: dict, w: float, h: float,
                     band: str, title: str, font: str) -> None:
    """
    Places band name and optional title text within the design safe zone.
    Both lines are anchored to the lower-left of the safe area, mirroring
    common album art / social asset conventions.
    """
    safe_margin_x = w * 0.07
    safe_margin_y = h * 0.07
    baseline_y    = h - safe_margin_y

    # Album/asset title — larger, positioned above the band name
    if title:
        title_size = h * 0.065
        dwg.add(dwg.text(
            title,
            insert=(safe_margin_x, baseline_y - title_size * 1.25),
            text_anchor="start",
            dominant_baseline="auto",
            font_family=font,
            font_size=title_size,
            font_weight="bold",
            fill=c["primary"],
            letter_spacing=title_size * 0.04,
        ))

    # Band name — smaller, at the very bottom of the safe zone
    name_size = h * 0.035
    dwg.add(dwg.text(
        band,
        insert=(safe_margin_x, baseline_y),
        text_anchor="start",
        dominant_baseline="auto",
        font_family=font,
        font_size=name_size,
        fill=c["primary"],
        letter_spacing=name_size * 0.20,
        fill_opacity=0.80,
    ))


# ─── Main generator ───────────────────────────────────────────────────────────

def generate(asset_type: str, platform: str, bg: str, scheme: str,
             font: str, band: str, title: str, export_png: bool) -> Path:
    if bg not in BG_FUNCS:
        sys.exit(f"Unknown background '{bg}'. Choose: {list(BG_FUNCS)}")
    if scheme not in COLOR_SCHEMES:
        sys.exit(f"Unknown scheme '{scheme}'. Choose: {list(COLOR_SCHEMES)}")

    size_key = "album_art" if asset_type == "album_art" else platform
    if size_key not in PLATFORM_SIZES:
        sys.exit(f"Unknown platform '{platform}'. Choose: {list(PLATFORM_SIZES)}")

    w, h = PLATFORM_SIZES[size_key]
    c = COLOR_SCHEMES[scheme]
    out_path = _out_path(asset_type, platform or "album_art", bg, scheme)

    dwg = svgwrite.Drawing(str(out_path), size=(w, h))

    # Background fill
    dwg.add(dwg.rect((0, 0), (w, h), fill=c["background"]))

    # Pattern layer
    BG_FUNCS[bg](dwg, c, float(w), float(h))

    # Text overlay
    if band or title:
        add_text_overlay(dwg, c, float(w), float(h), band, title, font)

    dwg.save()
    label = platform if asset_type == "social" else "album_art"
    print(f"  [{label}/{bg}/{scheme}] SVG  {w}×{h}  -> {out_path.relative_to(ROOT)}")

    if export_png:
        try:
            import cairosvg
            png_path = out_path.with_suffix(".png")
            cairosvg.svg2png(url=str(out_path), write_to=str(png_path))
            print(f"  [{label}/{bg}/{scheme}] PNG -> {png_path.relative_to(ROOT)}")
        except ImportError:
            print("  (PNG skipped — run: pip install cairosvg)")

    return out_path


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate album art and social assets as SVG")
    parser.add_argument("--type", choices=["album_art", "social"], required=True)
    parser.add_argument("--platform", choices=["instagram", "twitter", "facebook"],
                        default=None, help="Platform (required when --type=social)")
    parser.add_argument("--all-platforms", action="store_true",
                        help="Generate for all social platforms")
    parser.add_argument("--bg", choices=list(BG_FUNCS), default="geometric",
                        help="Background pattern (default: geometric)")
    parser.add_argument("--scheme", choices=list(COLOR_SCHEMES), default="dark")
    parser.add_argument("--font",   type=str, default="Georgia")
    parser.add_argument("--name",   type=str, default=BAND_NAME,
                        help="Band name text overlay")
    parser.add_argument("--title",  type=str, default="",
                        help="Album or asset title text overlay")
    parser.add_argument("--no-text", action="store_true",
                        help="Omit all text overlays")
    parser.add_argument("--png", action="store_true",
                        help="Also export PNG (requires cairosvg)")
    args = parser.parse_args()

    band  = "" if args.no_text else args.name
    title = "" if args.no_text else args.title

    if args.type == "album_art":
        generate("album_art", None, args.bg, args.scheme,
                 args.font, band, title, args.png)

    elif args.type == "social":
        if args.all_platforms:
            for p in ["instagram", "twitter", "facebook"]:
                generate("social", p, args.bg, args.scheme,
                         args.font, band, title, args.png)
        elif args.platform:
            generate("social", args.platform, args.bg, args.scheme,
                     args.font, band, title, args.png)
        else:
            parser.error("--type=social requires --platform or --all-platforms")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()

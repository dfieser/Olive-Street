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
    Grid of alternating filled circles and rotated outlined squares.
    Bolder than the previous translucent pass — reads as actual pattern.
    """
    cols = 14
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
                    fill=c["primary"], fill_opacity=0.18,
                    stroke=c["primary"], stroke_width=1.6,
                    stroke_opacity=0.55,
                ))
                # inner accent dot
                dwg.add(dwg.circle(center=(cx, cy), r=r * 0.28,
                                   fill=c["accent"], fill_opacity=0.6))
            else:
                sq = r * 1.05
                dwg.add(dwg.rect(
                    (cx - sq, cy - sq), (sq * 2, sq * 2),
                    fill="none",
                    stroke=c["accent"], stroke_width=1.4,
                    stroke_opacity=0.55,
                    transform=f"rotate(45 {cx} {cy})",
                ))


def bg_halftone(dwg: svgwrite.Drawing, c: dict, w: float, h: float) -> None:
    """
    Dot grid with radius modulated by distance from centre — solid iris of
    accent dots that fade into the corners. Far more punchy than before.
    """
    spacing = min(w, h) / 28
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
            t = 1 - (dist / max_dist)
            r = spacing * 0.50 * (0.25 + 0.85 * math.cos(math.pi * (1 - t) * 0.5) ** 2)
            if r > 0.5:
                color = c["accent"] if t > 0.55 else c["primary"]
                dwg.add(dwg.circle(
                    center=(x, y), r=r,
                    fill=color, fill_opacity=0.55,
                ))


def bg_lines(dwg: svgwrite.Drawing, c: dict, w: float, h: float) -> None:
    """
    Horizontal ruled lines whose weight oscillates with position. Strong
    accent bands every 7th line carry the pattern visually.
    """
    n_lines = int(h / 14)
    cy = h / 2
    for i in range(n_lines):
        y = (i + 0.5) * (h / n_lines)
        dist_norm = abs(y - cy) / cy
        weight = 1.0 + 4.5 * math.sin(math.pi * dist_norm) ** 2
        opacity = 0.32 + 0.45 * (1 - dist_norm)
        accent_band = (i % 7 == 0)
        color = c["accent"] if accent_band else c["primary"]
        dwg.add(dwg.line(
            (0, y), (w, y),
            stroke=color,
            stroke_width=weight * (1.5 if accent_band else 1),
            stroke_opacity=opacity,
        ))


def bg_concentric(dwg: svgwrite.Drawing, c: dict, w: float, h: float) -> None:
    """
    Concentric rectangles radiating outward from centre — bolder rings, with
    every 5th ring rendered in accent for clear visual rhythm.
    """
    cx, cy = w / 2, h / 2
    step = min(w, h) / 22
    max_rings = int(math.hypot(cx, cy) / step) + 2

    for i in range(max_rings):
        rx = i * step * (w / min(w, h))
        ry = i * step * (h / min(w, h))
        is_accent = i % 5 == 0
        dwg.add(dwg.rect(
            (cx - rx, cy - ry), (rx * 2, ry * 2),
            fill="none",
            stroke=c["accent"] if is_accent else c["primary"],
            stroke_width=3 if is_accent else 1.4,
            stroke_opacity=0.65 if is_accent else 0.35,
        ))


def bg_minimal(dwg: svgwrite.Drawing, c: dict, w: float, h: float) -> None:
    """
    Editorial layout — a large offset double-rectangle composition, a
    horizontal rule at the golden-ratio line, and a small filled accent
    square that anchors the negative space.
    """
    size = min(w, h) * 0.78
    ox = w * 0.42
    oy = h * 0.18
    dwg.add(dwg.rect(
        (ox, oy), (size, size),
        fill="none",
        stroke=c["primary"], stroke_width=4, stroke_opacity=0.45,
    ))
    inset = size * 0.05
    dwg.add(dwg.rect(
        (ox + inset, oy + inset), (size - inset * 2, size - inset * 2),
        fill="none",
        stroke=c["accent"], stroke_width=2, stroke_opacity=0.55,
    ))
    # Solid filled accent block in the upper-left
    fill_size = min(w, h) * 0.12
    dwg.add(dwg.rect(
        (w * 0.08, h * 0.14), (fill_size, fill_size),
        fill=c["accent"], fill_opacity=0.85,
    ))
    # Thin horizontal rule at golden-ratio height
    phi_y = h * 0.382
    dwg.add(dwg.line(
        (w * 0.08, phi_y), (w * 0.55, phi_y),
        stroke=c["accent"], stroke_width=2.5, stroke_opacity=0.85,
    ))
    # End-of-rule diamond bullets
    for x in (w * 0.08, w * 0.55):
        dwg.add(dwg.polygon(points=[
            (x, phi_y - 6), (x + 6, phi_y), (x, phi_y + 6), (x - 6, phi_y)
        ], fill=c["accent"]))


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
    Lower-left typographic block with band name + optional title, framed
    by an accent rule and trailing "EST · 2025" mark for editorial polish.
    """
    safe_margin_x = w * 0.06
    safe_margin_y = h * 0.06
    baseline_y    = h - safe_margin_y

    # Build a stacked block from the bottom up.
    name_size  = max(18, h * 0.032)
    rule_y     = baseline_y - name_size * 1.6
    title_size = max(28, h * 0.075)

    # Band name — smaller, at the very bottom
    if band:
        dwg.add(dwg.text(
            band,
            insert=(safe_margin_x, baseline_y),
            text_anchor="start", dominant_baseline="auto",
            font_family=font, font_size=name_size,
            fill=c["primary"], letter_spacing=name_size * 0.20,
        ))
        # EST mark trailing the band name
        dwg.add(dwg.text(
            "★ EST · 2025",
            insert=(safe_margin_x, baseline_y - name_size * 1.05),
            text_anchor="start", dominant_baseline="auto",
            font_family=font, font_size=name_size * 0.62,
            fill=c["accent"], letter_spacing=name_size * 0.16,
        ))

    # Accent rule between band name and title
    rule_w = min(w * 0.42, max(220, len(title or band) * title_size * 0.55))
    dwg.add(dwg.line(
        (safe_margin_x, rule_y),
        (safe_margin_x + rule_w, rule_y),
        stroke=c["accent"], stroke_width=max(2, h * 0.003),
    ))
    # Diamond at the right end of the rule
    dx = safe_margin_x + rule_w
    diamond_r = max(5, h * 0.005)
    dwg.add(dwg.polygon(points=[
        (dx, rule_y - diamond_r), (dx + diamond_r, rule_y),
        (dx, rule_y + diamond_r), (dx - diamond_r, rule_y),
    ], fill=c["accent"]))

    # Album / asset title — large, anchored above the rule
    if title:
        dwg.add(dwg.text(
            title,
            insert=(safe_margin_x, rule_y - title_size * 0.30),
            text_anchor="start", dominant_baseline="auto",
            font_family=font, font_size=title_size, font_weight="bold",
            fill=c["primary"], letter_spacing=title_size * 0.03,
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
        png_path = out_path.with_suffix(".png")
        try:
            from resvg_py import svg_to_bytes
            png_path.write_bytes(svg_to_bytes(
                svg_path=str(out_path),
                width=w,
                height=h,
            ))
            print(f"  [{label}/{bg}/{scheme}] PNG -> {png_path.relative_to(ROOT)}")
        except ImportError:
            try:
                import cairosvg
                cairosvg.svg2png(url=str(out_path), write_to=str(png_path))
                print(f"  [{label}/{bg}/{scheme}] PNG -> {png_path.relative_to(ROOT)}")
            except Exception as exc:
                print(f"  (PNG skipped — install resvg_py or a working cairosvg backend: {exc})")
        except Exception as exc:
            print(f"  (resvg_py export failed: {exc} — trying cairosvg)")
            try:
                import cairosvg
                cairosvg.svg2png(url=str(out_path), write_to=str(png_path))
                print(f"  [{label}/{bg}/{scheme}] PNG -> {png_path.relative_to(ROOT)}")
            except Exception as fallback_exc:
                print(f"  (PNG skipped — install resvg_py or a working cairosvg backend: {fallback_exc})")

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
                        help="Also export PNG")
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

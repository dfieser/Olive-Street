"""
build_all.py
------------
Run all generators in one shot to produce a full set of Olive Street assets.

What this produces:
  • 5 logo styles × 4 color schemes = 20 logo lockups  →  output/profiles/
  • 5 profile designs × 4 schemes = 20 profile images  →  output/profiles/
  • 5 background patterns × 4 schemes = 20 fliers  →  output/fliers/
  • 5 backgrounds × 3 platforms × 4 schemes = 60 posts  →  output/posts/

Total: up to 120 SVG files across 3 purpose-based folders.

Usage:
  # Full run — all styles, schemes, backgrounds, platforms
  python scripts/build_all.py

  # Only logos
  python scripts/build_all.py --logos-only

  # Only assets (album art + social)
  python scripts/build_all.py --assets-only

  # Specific scheme only
  python scripts/build_all.py --scheme dark

  # With PNG export (requires cairosvg)
  python scripts/build_all.py --png

  # Dry-run — print what would be generated without writing files
  python scripts/build_all.py --dry-run

Requires:
  pip install svgwrite
  pip install cairosvg   (optional — for --png)
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT   = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).parent

LOGO_STYLES    = ["wordmark", "stacked", "emblem", "badge", "block"]
BG_PATTERNS    = ["geometric", "halftone", "lines", "concentric", "minimal"]
COLOR_SCHEMES  = ["dark", "light", "tan", "mono"]
SOCIAL_PLATFORMS = ["instagram", "twitter", "facebook"]


def run(cmd: list[str], dry_run: bool) -> None:
    label = " ".join(str(a) for a in cmd[2:])
    if dry_run:
        print(f"  [dry-run] {label}")
        return
    result = subprocess.run([sys.executable] + cmd)
    if result.returncode != 0:
        print(f"  WARNING: command failed (exit {result.returncode}): {label}")


def build_logos(schemes: list[str], font: str, png: bool, dry_run: bool) -> None:
    print("\n── Logos ─────────────────────────────────────────────────────────")
    script = str(SCRIPTS / "generate_logo.py")
    for style in LOGO_STYLES:
        for scheme in schemes:
            cmd = [script, "--style", style, "--scheme", scheme, "--font", font]
            if png:
                cmd.append("--png")
            run(cmd, dry_run)
    total = len(LOGO_STYLES) * len(schemes)
    print(f"  → {total} logo(s)")


def build_album_art(schemes: list[str], patterns: list[str],
                    font: str, title: str, png: bool, dry_run: bool) -> None:
    print("\n── Album Art ─────────────────────────────────────────────────────")
    script = str(SCRIPTS / "generate_asset.py")
    for bg in patterns:
        for scheme in schemes:
            cmd = [script, "--type", "album_art", "--bg", bg,
                   "--scheme", scheme, "--font", font]
            if title:
                cmd += ["--title", title]
            if png:
                cmd.append("--png")
            run(cmd, dry_run)
    total = len(patterns) * len(schemes)
    print(f"  → {total} album art file(s)")


def build_social(schemes: list[str], patterns: list[str],
                 font: str, png: bool, dry_run: bool) -> None:
    print("\n── Social Assets ─────────────────────────────────────────────────")
    script = str(SCRIPTS / "generate_asset.py")
    for bg in patterns:
        for platform in SOCIAL_PLATFORMS:
            for scheme in schemes:
                cmd = [script, "--type", "social", "--platform", platform,
                       "--bg", bg, "--scheme", scheme, "--font", font,
                       "--no-text"]
                if png:
                    cmd.append("--png")
                run(cmd, dry_run)
    total = len(patterns) * len(SOCIAL_PLATFORMS) * len(schemes)
    print(f"  → {total} social asset(s)")


def main():
    parser = argparse.ArgumentParser(
        description="Build all Olive Street design assets in one command")
    parser.add_argument("--logos-only",  action="store_true")
    parser.add_argument("--assets-only", action="store_true")
    parser.add_argument("--scheme", choices=COLOR_SCHEMES, default=None,
                        help="Restrict to a single color scheme")
    parser.add_argument("--bg", choices=BG_PATTERNS, default=None,
                        help="Restrict to a single background pattern")
    parser.add_argument("--font",  type=str, default="Georgia")
    parser.add_argument("--title", type=str, default="",
                        help="Album title for album art text overlay")
    parser.add_argument("--png",     action="store_true")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print commands without running them")
    args = parser.parse_args()

    schemes  = [args.scheme]  if args.scheme else COLOR_SCHEMES
    patterns = [args.bg]      if args.bg     else BG_PATTERNS

    print(f"Build All — schemes: {schemes}  patterns: {patterns}")
    if args.dry_run:
        print("(dry-run mode — no files will be written)\n")

    if not args.assets_only:
        build_logos(schemes, args.font, args.png, args.dry_run)

    if not args.logos_only:
        build_album_art(schemes, patterns, args.font, args.title,
                        args.png, args.dry_run)
        build_social(schemes, patterns, args.font, args.png, args.dry_run)

    print("\nDone.")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()

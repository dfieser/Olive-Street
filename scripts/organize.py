"""
organize.py
-----------
Keep the output folders clean and organized.

Commands:
    archive     Move all outputs older than N days to output/archive/
    rename      Rename all images in an output folder to a clean slug format
    report      Print a summary of all output files (count, size, dates)
    duplicates  Find visually similar images using perceptual hashing

Usage:
    python scripts/organize.py archive --days 30
    python scripts/organize.py rename --folder output/logos
    python scripts/organize.py report
    python scripts/organize.py duplicates

Requires:
    pip install pillow imagehash
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = ROOT / "output" / "archive"
OUTPUT_DIRS = [
    ROOT / "output" / "logos",
    ROOT / "output" / "album_art",
    ROOT / "output" / "social" / "instagram",
    ROOT / "output" / "social" / "twitter",
    ROOT / "output" / "social" / "facebook",
]
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def all_images(dirs=None) -> list[Path]:
    dirs = dirs or OUTPUT_DIRS
    imgs = []
    for d in dirs:
        if d.is_dir():
            imgs.extend(p for p in d.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    return imgs


def human_size(n_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} TB"


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_archive(days: int, dry_run: bool):
    cutoff = datetime.now() - timedelta(days=days)
    moved = 0
    for img in all_images():
        mtime = datetime.fromtimestamp(img.stat().st_mtime)
        if mtime < cutoff:
            # Preserve subfolder info in archive name
            rel = img.relative_to(ROOT / "output")
            dest = ARCHIVE_DIR / str(rel).replace(os.sep, "__")
            if not dry_run:
                ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
                shutil.move(str(img), dest)
                print(f"  Archived: {img.relative_to(ROOT)} -> archive/{dest.name}")
            else:
                print(f"  [dry-run] Would archive: {img.relative_to(ROOT)}")
            moved += 1
    print(f"\n{'Would move' if dry_run else 'Moved'} {moved} file(s) older than {days} day(s).")


def cmd_rename(folder: str):
    target = ROOT / folder
    if not target.is_dir():
        sys.exit(f"Folder not found: {target}")
    imgs = sorted(p for p in target.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    renamed = 0
    for img in imgs:
        # Already clean if it matches YYYYMMDD_HHMMSS_slug.ext
        if img.name[:8].isdigit():
            continue
        ts = datetime.fromtimestamp(img.stat().st_mtime).strftime("%Y%m%d_%H%M%S")
        stem = img.stem.lower().replace(" ", "_")[:50]
        new_name = f"{ts}_{stem}{img.suffix}"
        new_path = img.parent / new_name
        img.rename(new_path)
        print(f"  {img.name} -> {new_name}")
        renamed += 1
    print(f"\nRenamed {renamed} file(s) in {folder}")


def cmd_report():
    print(f"{'Folder':<45} {'Files':>6}  {'Total Size':>10}  {'Newest'}")
    print("-" * 80)
    grand_count = 0
    grand_size = 0
    for d in OUTPUT_DIRS:
        imgs = [p for p in d.iterdir() if p.suffix.lower() in IMAGE_EXTS] if d.is_dir() else []
        size = sum(p.stat().st_size for p in imgs)
        newest = max((datetime.fromtimestamp(p.stat().st_mtime) for p in imgs),
                     default=None)
        rel = str(d.relative_to(ROOT))
        newest_str = newest.strftime("%Y-%m-%d") if newest else "—"
        print(f"  {rel:<43} {len(imgs):>6}  {human_size(size):>10}  {newest_str}")
        grand_count += len(imgs)
        grand_size += size
    print("-" * 80)
    print(f"  {'TOTAL':<43} {grand_count:>6}  {human_size(grand_size):>10}")


def cmd_duplicates():
    try:
        import imagehash
    except ImportError:
        sys.exit("Run: pip install imagehash")
    from PIL import Image

    imgs = all_images()
    hashes: dict[str, Path] = {}
    dupes = []
    for p in imgs:
        try:
            h = str(imagehash.phash(Image.open(p)))
        except Exception:
            continue
        if h in hashes:
            dupes.append((hashes[h], p))
        else:
            hashes[h] = p

    if not dupes:
        print("No duplicate images found.")
    else:
        print(f"Found {len(dupes)} potential duplicate pair(s):\n")
        for a, b in dupes:
            print(f"  {a.relative_to(ROOT)}")
            print(f"  {b.relative_to(ROOT)}\n")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Organize output folders")
    sub = parser.add_subparsers(dest="command", required=True)

    p_archive = sub.add_parser("archive", help="Archive old files")
    p_archive.add_argument("--days", type=int, default=30)
    p_archive.add_argument("--dry-run", action="store_true")

    p_rename = sub.add_parser("rename", help="Rename files to clean slug format")
    p_rename.add_argument("--folder", type=str, required=True)

    sub.add_parser("report", help="Print summary of all outputs")
    sub.add_parser("duplicates", help="Find visually similar images")

    args = parser.parse_args()

    if args.command == "archive":
        cmd_archive(args.days, args.dry_run)
    elif args.command == "rename":
        cmd_rename(args.folder)
    elif args.command == "report":
        cmd_report()
    elif args.command == "duplicates":
        cmd_duplicates()


if __name__ == "__main__":
    main()

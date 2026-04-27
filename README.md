# Olive Street — Art Generation Workspace

A structured workspace for generating, organizing, and managing band logos, album art, and social media assets for **Olive Street** — using pure Python code and SVG, no AI APIs.

---

## Quick Start

### 1. Install dependencies
```powershell
pip install -r requirements.txt
```

### 2. Generate logos
```powershell
# One logo — specific style and scheme
python scripts/generate_logo.py --style wordmark --scheme dark

# One logo with a custom font (must be installed on your system)
python scripts/generate_logo.py --style emblem --scheme light --font "Palatino Linotype"

# All 5 styles × 4 color schemes = 20 logos
python scripts/generate_logo.py --all
```

### 3. Generate album art and social assets
```powershell
# Album art — 3000×3000 with a geometric background
python scripts/generate_asset.py --type album_art --bg geometric --title "First Light"

# Instagram post
python scripts/generate_asset.py --type social --platform instagram --bg halftone

# All social platforms in one shot
python scripts/generate_asset.py --type social --all-platforms --bg concentric

# Every combination — full build
python scripts/build_all.py

# Dry run — see what would be generated without writing files
python scripts/build_all.py --dry-run
```

---

## Workspace Structure

```
Olive Street Scripts/
│
├── scripts/
│   ├── generate_logo.py     # SVG logo generator (5 styles × 4 schemes)
│   ├── generate_asset.py    # SVG album art + social asset generator
│   ├── build_all.py         # Run all generators in one command
│   └── organize.py          # Archive, rename, report, deduplicate
│
├── prompts/                 # Design brief notes and concept text
│   ├── logos.txt
│   ├── album_art.txt
│   └── social_media.txt
│
├── criteria/
│   ├── brand_guidelines.md  # Hard design rules — READ BEFORE GENERATING
│   ├── color_palette.json   # Official colors (hex + CMYK)
│   └── typography.md        # Type system and rules
│
├── assets/
│   ├── fonts/               # Licensed font files (OTF, TTF, WOFF2)
│   ├── textures/            # Overlay textures and references
│   └── references/          # Mood board / reference images
│
├── output/
│   ├── logos/               # Generated logo SVGs
│   ├── album_art/           # Generated album art SVGs
│   ├── social/
│   │   ├── instagram/
│   │   ├── twitter/
│   │   └── facebook/
│   └── archive/             # Older outputs moved here by organize.py
│
├── config.json              # Default font, scheme, and generation settings
└── requirements.txt         # Python dependencies
```

---

## Scripts Reference

### `generate_logo.py`

Produces clean SVG logos drawn entirely in code.

| Flag | Description |
|------|-------------|
| `--style` | `wordmark`, `stacked`, `emblem`, `badge`, `block` |
| `--scheme` | `dark`, `light`, `mono`, `rust` (default: `dark`) |
| `--font` | Font family name — must be installed (default: `Georgia`) |
| `--name` | Override the band name text |
| `--all` | Generate every style × every scheme |
| `--png` | Also export PNG at 2× (requires `cairosvg`) |

**Logo styles:**
| Style | Description |
|-------|-------------|
| `wordmark` | Band name between two ruled lines with accent dots |
| `stacked` | Two-line split with diamond-center divider |
| `emblem` | Double-border frame with computed corner ornaments |
| `badge` | Circular stamp with concentric rings and tick marks |
| `block` | High-contrast split block, name reversed out |

---

### `generate_asset.py`

Produces SVG backgrounds with optional text overlay for album art and social.

| Flag | Description |
|------|-------------|
| `--type` | `album_art` or `social` |
| `--platform` | `instagram` (1080²), `twitter` (1500×500), `facebook` (1200×630) |
| `--all-platforms` | Generate for all three platforms |
| `--bg` | `geometric`, `halftone`, `lines`, `concentric`, `minimal` |
| `--scheme` | Color scheme (default: `dark`) |
| `--title` | Album / asset title text overlay |
| `--no-text` | Omit all text overlays |
| `--png` | Also export PNG (requires `cairosvg`) |

**Background patterns:**
| Pattern | Description |
|---------|-------------|
| `geometric` | Grid of alternating translucent circles and rotated squares |
| `halftone` | Dot grid, radius modulated by distance from canvas center |
| `lines` | Horizontal rules with sinusoidally varying stroke weight |
| `concentric` | Concentric rectangles radiating from center |
| `minimal` | Clean flat canvas with a single offset geometric accent |

---

### `build_all.py`

Runs all generators to produce the complete asset set.

```powershell
python scripts/build_all.py                   # Full run
python scripts/build_all.py --logos-only      # Logos only
python scripts/build_all.py --assets-only     # Album art + social only
python scripts/build_all.py --scheme dark     # One scheme only
python scripts/build_all.py --bg halftone     # One background only
python scripts/build_all.py --dry-run         # Print without writing
```

---

### `organize.py`

| Command | Description |
|---------|-------------|
| `archive --days 30` | Move outputs older than N days to `output/archive/` |
| `rename --folder output/logos` | Rename files to the standard timestamp slug format |
| `report` | Print file counts, sizes, and newest dates per folder |
| `duplicates` | Find visually similar images using perceptual hashing |

---

## PNG Export

SVG outputs can be opened directly in any browser or Inkscape.  
For PNG export, install `cairosvg`:

```powershell
pip install cairosvg
```

> On Windows, `cairosvg` requires the GTK runtime. If installation is difficult,
> open the SVG in **Inkscape** and use File → Export PNG — it handles this reliably.

---

## Fonts

Specify any font installed on your system with `--font "Font Name"`.  
To use a custom/licensed font:
1. Copy the OTF/TTF file into `assets/fonts/`
2. Install it system-wide (double-click → Install)
3. Pass its name to `--font`

See [criteria/typography.md](criteria/typography.md) for typeface rules.

---

## Design Criteria (Read These First)

1. [criteria/brand_guidelines.md](criteria/brand_guidelines.md) — sizes, safe zones, approval checklist
2. [criteria/color_palette.json](criteria/color_palette.json) — official colors, forbidden colors
3. [criteria/typography.md](criteria/typography.md) — type hierarchy, tracking rules

---

## Workflow

1. **Criteria** — fill in the blanks in `criteria/brand_guidelines.md` (genre, mood, typeface)
2. **Generate** — run `generate_logo.py --all` and `build_all.py --dry-run` to preview
3. **Run** — execute `build_all.py` (or individual scripts for targeted generation)
4. **Review** — open SVGs in a browser or Inkscape, shortlist keepers
5. **Finalize** — check against the brand guidelines approval checklist
6. **Organize** — run `organize.py report` then `organize.py archive --days 30`

# Olive Street — Art Generation Workspace

A Python-first workspace for generating Olive Street visual assets as SVG files (optionally PNG), with no AI image APIs.

## Quick Start

### 1. Install dependencies
```powershell
pip install -r requirements.txt
```

### 2. Generate assets
```powershell
# Logos (5 styles x 4 schemes)
python scripts/generate_logo.py --all

# Circular profile images (5 designs x 4 schemes)
python scripts/generate_profile.py --all

# Export a transparent PNG version
python scripts/generate_profile.py --design stack --scheme dark --png

# One album-art file (3000x3000)
python scripts/generate_asset.py --type album_art --bg geometric --title "First Light"

# One social post
python scripts/generate_asset.py --type social --platform instagram --bg halftone

# Batch build (logos + album_art + social)
python scripts/build_all.py
```

### 3. Dry-run the batch build
```powershell
python scripts/build_all.py --dry-run
```

## Current Workspace Structure

```text
Olive Street/
|
|-- scripts/
|   |-- generate_logo.py      # Logo SVG generator
|   |-- generate_profile.py   # Circular profile SVG generator
|   |-- generate_asset.py     # Album-art/social SVG generator
|   |-- build_all.py          # Batch runner (logos + assets)
|   `-- organize.py           # Archive/report/rename/duplicate checks
|
|-- prompts/
|   `-- design_brief.md
|
|-- criteria/
|   |-- brand_guidelines.md
|   |-- color_palette.json
|   `-- typography.md
|
|-- assets/
|   |-- fonts/
|   |-- textures/
|   `-- references/
|
|-- output/
|   |-- profiles/             # Logos + profile-image SVG/PNG outputs
|   |-- fliers/               # Album-art SVG/PNG outputs
|   |-- posts/                # Social SVG/PNG outputs
|   `-- archive/
|
|-- config.json
`-- requirements.txt
```

## Script Reference

### scripts/generate_logo.py

Generates logo SVGs to output/profiles. Each style applies a halftone wash,
diamond ornaments, and an "EST · 2026" mark for a polished printed feel.

| Flag | Description |
|------|-------------|
| --style | wordmark, stacked, emblem, badge, seal, block |
| --scheme | dark, light, tan, mono (default: dark) |
| --font | Font family name (default: Georgia) |
| --name | Override band name text |
| --all | Generate all style x scheme combinations (5 x 4 = 20 SVGs) |
| --png | Also export PNG at 2x (requires cairosvg) |

Styles:
- wordmark — single-line horizontal mark between two diamond-anchored rules
- stacked — three-line OLIVE / STREET / BAND with diamond-rule dividers
- emblem — two-line layout in a double-border frame with L-cut corner ornaments
- badge — circular stamp with concentric rings, tick marks, and cardinal diamonds
- block — high-contrast split block with reversed-out type and accent stripe

Examples:
```powershell
python scripts/generate_logo.py --style wordmark --scheme dark
python scripts/generate_logo.py --style emblem --scheme light --font "Palatino Linotype"
python scripts/generate_logo.py --all
```

### scripts/generate_profile.py

Generates circular profile-image SVGs to output/profiles. Twelve designs, each
rendered with halftone wash, inner highlight ring, vignette, and ornament
detail for a polished badge feel.

| Flag | Description |
|------|-------------|
| --design | stack, arc, stripe, target, split, wavefield, ripple, scope, boombox, lattice, funkgrid, signstamp |
| --scheme | dark, light, tan, mono (default: dark) |
| --all | Generate all design x scheme combinations (12 x 4 = 48 SVGs) |
| --png | Also export PNG at 2x (requires cairosvg) |

Designs:
- stack — OLIVE / STREET / BAND in stacked bold type
- arc — band name arced over EQ bars with caps + reflection
- stripe — wide colour stripe with reversed-out type and star ornaments
- target — bullseye rings with two-line text in an accent bar
- split — circle halved horizontally with corner stars and diamond ends
- wavefield — layered horizontal waveforms with a centre horizon band
- ripple — radial wave rings with a starburst medallion
- scope — oscilloscope dial with phosphor-glow trace, knobs, bezel LEDs
- boombox — geometric boombox with antenna, handle, transport pad, knob
- lattice — radial wave lattice with spokes and centre BAND medallion
- funkgrid — syncopated rhythm-block matrix inside a calibrated tick ring
- signstamp — rotated street-sign plate inside a stamped circle

Examples:
```powershell
python scripts/generate_profile.py --design stack --scheme dark
python scripts/generate_profile.py --design scope --scheme tan
python scripts/generate_profile.py --all
```

### scripts/generate_asset.py

Generates album-art and social SVGs.

| Flag | Description |
|------|-------------|
| --type | album_art or social |
| --platform | instagram, twitter, facebook (required for social unless --all-platforms) |
| --all-platforms | Generate social assets for all 3 platforms |
| --bg | geometric, halftone, lines, concentric, minimal |
| --scheme | dark, light, tan, mono (default: dark) |
| --font | Font family name (default: Georgia) |
| --name | Band name overlay text |
| --title | Optional title overlay text |
| --no-text | Omit all text overlays |
| --png | Also export PNG (requires cairosvg) |

Output folders:
- album_art -> output/fliers
- social -> output/posts

Examples:
```powershell
python scripts/generate_asset.py --type album_art --bg concentric --scheme tan --title "First Light"
python scripts/generate_asset.py --type social --platform twitter --bg lines --no-text
python scripts/generate_asset.py --type social --all-platforms --bg halftone
```

### scripts/build_all.py

Runs a full batch across:
- logos (generate_logo.py)
- album_art + social assets (generate_asset.py)

Notes:
- This script does not call generate_profile.py.
- Use generate_profile.py separately if you want profile designs.

Examples:
```powershell
python scripts/build_all.py
python scripts/build_all.py --logos-only
python scripts/build_all.py --assets-only
python scripts/build_all.py --scheme dark
python scripts/build_all.py --bg geometric
python scripts/build_all.py --dry-run
```

### scripts/organize.py

Organization and cleanup helpers for raster exports.

| Command | Description |
|---------|-------------|
| archive --days 30 | Move older files into output/archive |
| rename --folder <path> | Rename images to timestamp_slug.ext |
| report | Print counts, sizes, newest date by folder |
| duplicates | Find likely duplicate images via perceptual hash |

Important current behavior:
- organize.py only processes raster formats: .png, .jpg, .jpeg, .webp
- SVG files are not included in report/archive/duplicates
- The built-in report/archive scan paths currently target output/logos, output/album_art, and output/social/*

## PNG Export

Use PNG when you need transparency. JPG does not support transparent areas, so it will flatten invisible layers into a solid background.

`--png` writes a PNG alongside the SVG and preserves transparent areas outside the circular badge artwork.

The workspace now installs a portable PNG backend by default from [requirements.txt](requirements.txt). If you want a secondary fallback backend, you can also install CairoSVG:

```powershell
pip install cairosvg
```

If Cairo/GTK setup is difficult on Windows, export PNG via Inkscape from the generated SVG files.

## Design Criteria

Read these before generating:

1. [criteria/brand_guidelines.md](criteria/brand_guidelines.md)
2. [criteria/color_palette.json](criteria/color_palette.json)
3. [criteria/typography.md](criteria/typography.md)
4. [prompts/design_brief.md](prompts/design_brief.md)

## Typical Workflow

1. Review criteria and brief files.
2. Generate targeted sets with generate_logo.py, generate_profile.py, or generate_asset.py.
3. Use build_all.py for broad batch runs.
4. Review SVG outputs in a browser or Inkscape.
5. Export PNG variants if needed.
6. Use organize.py for raster output housekeeping.

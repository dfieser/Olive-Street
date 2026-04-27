# Olive Street Band — Workspace Instructions

This workspace generates **programmatic SVG logos and art assets** for the **Olive Street Band** using Python + svgwrite. No AI image generation. Read this file before taking any action.

## Project Brief

**Client:** Olive Street Band — a funk and R&B cover band  
**Goal:** Visual identity that works as a profile image and scales cleanly from large displays down to small thumbnails  
**Primary output format:** SVG (vector), optionally exported to PNG via cairosvg  
**Canvas size history:** Started at 1024×1024, moved to 1536×1536 for crisper detail

## Non-Negotiables (Enforce These Every Time)

- **Shape:** Circular format — all final logos must be circular / badge-style
- **Text:** "OLIVE STREET BAND" only. No abbreviations (OSB is retired). No taglines (no "FUNK SOUL RHYTHM" or similar).
- **No olive imagery** — no literal fruit, olives, or olive branches
- **Max 3 colors** — see palette below; do not introduce new colors without explicit approval
- **Must read clearly at small sizes** — test every design at 64×64 equivalent before finalizing

## Brand Colors

| Role | Name | Hex |
|------|------|-----|
| Primary | Olive Green | `#6B7A3A` |
| Secondary | Tan | `#DDB892` |
| Accent / highlights | Cream | `#F5F0E1` |

Dark backgrounds use olive green fill, tan and cream for text/elements.  
Light/reversed versions use cream background with olive text.

## Scripts

| Script | What it does |
|--------|-------------|
| `scripts/generate_logo.py` | Draws SVG logos — 5 styles × 4 color schemes |
| `scripts/generate_asset.py` | Draws album art + social media assets with geometric backgrounds |
| `scripts/generate_profile.py` | Draws circular profile images — 5 designs × 4 color schemes, bold at small sizes |
| `scripts/build_all.py` | Runs all generators in one shot |
| `scripts/organize.py` | Archive old outputs, rename files, report, deduplicate |

Run any script from the workspace root: `python scripts/<name>.py --help`

## Design History (16 designs across 6 rounds)

| Round | Concepts |
|-------|---------|
| v1 | Monogram, street sign, sunburst, vinyl record |
| v2 | Vinyl with grooves + curved text, ornamented sunburst with rays |
| v3 | Vinyl (diamonds replaced tagline), ring of soundwave bars, stamp/seal |
| v4 | Horizontal waveform, stacked pulsar lines (Joy Division-style), cassette tape |
| v5 | Detailed cassette (screws, wound reels, gears), brick wall + tilted street sign |
| v6 | Vintage oscilloscope with waveform trace, 1980s boombox with EQ visualizer |

**Direction so far:** Moved away from literal symbols (olives, music notes) toward graphic/geometric treatments — waveforms, soundbars, oscilloscope traces, and typographic badges.

## Recurring Technical Patterns

- **Diamond dividers:** `line + ◆ + line` ornament, used between text elements
- **Four-point diamond shapes:** Custom-drawn with Bézier or polygon points
- **Phillips-head screws:** Circle + two thin crossing rectangles
- **Concentric rings:** Drawn as progressively smaller filled circles or stroked ellipses
- **Circle masks / paste bug:** When pasting an RGBA layer with a circle mask in Pillow, transparent pixels overwrite what's underneath. Fix: use `alpha_composite` on an RGBA canvas, or composite onto an opaque source canvas before pasting.

## Known Good Techniques

- Curved text along a circle path: compute character positions along an arc, rotate each glyph
- Radial symmetry: draw one element, rotate copies around center point
- SVG text tracking: set `letter_spacing` to `font_size * 0.20–0.30` for the band name
- Safe-zone for circular logos: keep all elements within 88% of the canvas radius

## Criteria Files

- `criteria/brand_guidelines.md` — sizes, approval checklist, don'ts
- `criteria/color_palette.json` — exact hex + RGB values
- `criteria/typography.md` — type rules

## Output Folders

```
output/logos/          SVG/PNG logos
output/album_art/      3000×3000 album art
output/social/         instagram/ twitter/ facebook/ profile/
output/archive/        Old outputs moved here by organize.py
```

All filenames: `YYYYMMDD_HHMMSS_<descriptor>.<ext>`

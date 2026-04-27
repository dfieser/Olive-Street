# Olive Street Band — Design Brief & Concept Notes

Use this file to jot down design ideas, concepts to try next, and notes on what's
working or not. This is the brief that gets handed to any new session.

---

## Project Goal

A circular logo for the **Olive Street Band** (funk and R&B cover band) that works
as a profile image and scales cleanly from large displays down to small thumbnails.

---

## Colors (locked)

| Role | Hex |
|------|-----|
| Olive Green (primary) | `#6B7A3A` |
| Tan (secondary) | `#DDB892` |
| Cream (accent/highlights) | `#F5F0E1` |

Max 3 colors per design.

---

## Text (locked)

`OLIVE STREET BAND` — uppercase, full name, no abbreviations, no taglines.

---

## Design History — What's Been Made

| Round | Designs | Notes |
|-------|---------|-------|
| v1 | Monogram, street sign, sunburst, vinyl record | Simple concepts, 1024×1024 |
| v2 | Vinyl with grooves + curved text, ornamented sunburst | More detail |
| v3 | Vinyl v3 (diamonds replaced tagline), soundwave bars ring, stamp/seal | Removed tagline |
| v4 | Horizontal waveform, Joy Division-style pulsar lines, cassette tape | Moved non-radial |
| v5 | Detailed cassette (screws/reels/gears), brick wall + street sign | High detail |
| v6 | Vintage oscilloscope trace, 1980s boombox with EQ bars | Sound theme |

**Total: 16 designs across 6 rounds. Canvas bumped to 1536×1536 in v3.**

---

## Direction — What's Working

Moving **away from** literal symbols → **toward** graphic/geometric treatments:
- Waveforms and soundbars ✓
- Oscilloscope / signal traces ✓
- Vinyl record geometry (rings, grooves) ✓
- Typographic badges and stamps ✓
- Radial and concentric patterns ✓

---

## Ideas to Try Next

<!-- Add concepts here before starting a session -->

- 

---

## Techniques That Work Well

- Diamond dividers: `line + ◆ + line` ornament between text elements
- Four-point diamonds: drawn with polygon points (not rotated squares)
- Curved text: compute character positions along an arc, rotate each glyph
- Concentric rings: progressively smaller filled circles or stroked ellipses
- Radial symmetry: draw one element, rotate N copies around center

---

## Known Bugs / Gotchas

- **Pillow circle mask paste bug:** Pasting an RGBA layer with a circle mask
  erases underlying pixels because transparent pixels in the mask get copied.
  Fix: use `alpha_composite` on an RGBA canvas, or composite onto an opaque
  source canvas before pasting.
- SVG `letter_spacing` in svgwrite: use `font_size * 0.20–0.30` for good tracking
  on the band name.

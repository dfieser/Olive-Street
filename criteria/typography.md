# Olive Street Band — Typography

---

## Band Name Text

- Always render as: **`OLIVE STREET BAND`** — uppercase, full name
- No abbreviations, no "OSB"
- No taglines alongside the band name

## Tracking / Letter-Spacing

| Context | Letter-spacing |
|---------|----------------|
| Primary logo (large) | `font_size * 0.25–0.30` |
| Badge / stamp (compact) | `font_size * 0.20` |
| Supporting text (year, label) | `font_size * 0.12–0.15` |

In svgwrite: pass as the `letter_spacing` attribute on `dwg.text()`.

## Font Guidance

No specific typeface is locked in yet. When generating with code:
- Default: `Georgia` (universally available, serif, works for placeholder)
- Pass any installed font via `--font "Font Name"` on the command line
- Store licensed fonts in `assets/fonts/`

Character to look for in the final typeface:
- **Condensed, heavy or bold weight** — holds up in small sizes inside the circle
- **Strong, clean letterforms** — no decorative scripts
- **Consistent cap height** — all-caps band name must sit evenly

## Hierarchy in Circular Logos

In circular / badge layouts:
1. **Band name** — primary, largest, most prominent element
2. **Year or supporting line** (optional, subtle) — smaller, lower contrast
3. **No other text**

## Rules

- Never stretch or skew type manually
- Minimum readable size: band name must be legible at 64×64 px equivalent
- Text must stay inside the 88% safe zone radius of any circular canvas
- No system fonts in final approved outputs (Arial, Helvetica, Times)

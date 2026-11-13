---
name: מגרש (Magrash)
description: A Hebrew RTL football tactics app set on a European night under floodlights; formations glow on the pitch as discs.
colors:
  midnight-ground: "#060b2e"
  floodlight-bloom: "#1b3fa8"
  lit-panel-top: "#0f1d66"
  lit-panel-base: "#0a1347"
  flat-panel: "#0c1854"
  hairline-edge: "rgba(201, 212, 255, .18)"
  strong-edge: "rgba(201, 212, 255, .42)"
  ice-text: "#eef2ff"
  periwinkle-soft: "#c9d4ff"
  periwinkle-muted: "#8ea0e6"
  electric-blue: "#3f6bff"
  electric-ink: "#ffffff"
  live-coral: "#ff6b6b"
  pitch-centre: "#16308f"
  pitch-edge: "#0b1756"
  day-ground: "#e9eeff"
  day-bloom: "#c3d0ff"
  day-panel: "#ffffff"
  day-panel-base: "#f3f6ff"
  day-text: "#0a1b6e"
  day-soft: "#2a3f9e"
  day-muted: "#4a5aa0"
  day-electric: "#2d55f0"
  day-live: "#c62828"
typography:
  display:
    fontFamily: "Assistant, Arial Hebrew, system-ui, -apple-system, Segoe UI, Arial, sans-serif"
    fontSize: "30px"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "0.01em"
  score:
    fontFamily: "Assistant, Arial Hebrew, system-ui, sans-serif"
    fontSize: "34px"
    fontWeight: 800
    lineHeight: 1
    fontFeature: "tabular-nums"
  headline:
    fontFamily: "Assistant, Arial Hebrew, system-ui, sans-serif"
    fontSize: "22px"
    fontWeight: 800
    lineHeight: 1.2
  title:
    fontFamily: "Assistant, Arial Hebrew, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 800
    lineHeight: 1.35
  body:
    fontFamily: "Assistant, Arial Hebrew, system-ui, -apple-system, Segoe UI, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 500
    lineHeight: 1.5
  label:
    fontFamily: "Assistant, Arial Hebrew, system-ui, sans-serif"
    fontSize: "0.8rem"
    fontWeight: 700
    lineHeight: 1.5
    fontFeature: "tabular-nums"
rounded:
  inset: "14px"
  pitch: "16px"
  preview: "18px"
  panel: "22px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
components:
  view-switch:
    backgroundColor: "{colors.flat-panel}"
    rounded: "{rounded.pill}"
    padding: "4px"
  view-tab:
    backgroundColor: "transparent"
    textColor: "{colors.periwinkle-muted}"
    rounded: "{rounded.pill}"
    padding: "0 6px"
    height: "38px"
  view-tab-active:
    backgroundColor: "{colors.ice-text}"
    textColor: "{colors.lit-panel-base}"
  chip-league:
    backgroundColor: "transparent"
    textColor: "{colors.periwinkle-soft}"
    rounded: "{rounded.pill}"
    padding: "0 14px"
    height: "36px"
  chip-league-active:
    backgroundColor: "{colors.lit-panel-top}"
    textColor: "{colors.ice-text}"
  button-outline:
    backgroundColor: "transparent"
    textColor: "{colors.periwinkle-soft}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "40px"
  button-icon:
    backgroundColor: "transparent"
    textColor: "{colors.periwinkle-soft}"
    rounded: "{rounded.pill}"
    width: "40px"
    height: "40px"
  lit-panel:
    backgroundColor: "{colors.lit-panel-top}"
    textColor: "{colors.ice-text}"
    rounded: "{rounded.panel}"
    padding: "16px"
  match-card:
    backgroundColor: "{colors.lit-panel-top}"
    textColor: "{colors.ice-text}"
    typography: "{typography.score}"
    rounded: "{rounded.panel}"
    padding: "12px 16px 14px"
  player-disc-home:
    backgroundColor: "{colors.ice-text}"
    textColor: "{colors.day-text}"
    rounded: "{rounded.pill}"
    size: "20px"
  player-disc-away:
    backgroundColor: "{colors.electric-blue}"
    textColor: "{colors.electric-ink}"
    rounded: "{rounded.pill}"
    size: "20px"
  minute-pill:
    backgroundColor: "{colors.electric-blue}"
    textColor: "{colors.electric-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
---

# Design System: מגרש (Magrash)

## Overview

**Creative North Star: "European Nights" (לילות אירופה)**

The app is a stadium lit from above at night. A midnight-navy ground carries a soft floodlight bloom that falls from the top of the viewport and stays fixed while the content scrolls; every surface below it is a lit panel, a vertical gradient from a brighter navy at the top to a deeper one at the base, outlined by a single periwinkle hairline. Formations are the signature: on the pitch both teams appear as round discs, home in ice white and away in electric blue, and when a lineup opens they walk out from the centre spot to their positions, line by line.

Colour is disciplined. Everything is blue: ground, panels, text tints, league dots. Electric blue is the only saturated hue and means "active" or "the away side"; coral appears only for a live match state. Type is a single family, Assistant, held mostly at 700 to 800, so headings, scores and labels share one confident voice and Hebrew with mixed Latin names stays legible on a phone. A day theme keeps the same world in daylight: pale blue ground, white panels, navy text, while the pitch itself stays a night pitch.

**Key Characteristics:**
- Midnight ground with a fixed floodlight bloom; lit gradient panels with a 1px inset hairline instead of borders or drop shadows.
- One saturated colour (electric blue); league identity carried by small dots drawn only from the world's blue scale.
- Assistant only, 500 to 800, tabular figures on every number.
- Pills for every control: segmented view switcher, outlined league chips, outlined actions, round icon buttons.
- Player discs on a lit pitch, with a staggered walkout from the centre spot.
- RTL by default; layout uses logical properties.

## Colors

A blue-on-blue night with one electric accent; nothing outside the blue scale except the live state.

### Primary
- **Electric Blue** (electric-blue; day theme day-electric): active and selected accent, the away team's discs, the substitution minute pill, caret, selection, accent-color, the title-hover underline, and the concept panel's ring at 55% alpha. Translucent at 14% it tints the Hebrew summary block in articles.

### Secondary
- **Live Coral** (live-coral; day theme day-live): the status of a match in progress. Nothing else.

### Neutral
- **Midnight Ground** (midnight-ground): page background and theme-color; the sticky league bar is the ground at 88% with a 10px backdrop blur.
- **Floodlight Bloom** (floodlight-bloom): a radial glow (90% by 420px, centred 60px above the top edge, fading out by 72%) fixed to the viewport.
- **Lit Panel** (lit-panel-top to lit-panel-base): the 180deg gradient on every content surface: match cards, AI panels, analyses, previews, concepts, article cards, tables.
- **Flat Panel** (flat-panel): the track of the view switcher.
- **Hairline Edge** and **Strong Edge** (periwinkle at 18% and 42%): panel outlines, row rules, outlined control borders, the lesson rule; strong edge on hover and on outlined controls.
- **Ice Text** (ice-text): primary text, the active view tab fill, the home team's discs.
- **Periwinkle Soft** (periwinkle-soft): secondary text, control labels, lesson and sub-heads, focus ring.
- **Periwinkle Muted** (periwinkle-muted): meta lines, table headers, idle view tabs, dashes between scores.
- **Night Pitch** (pitch-centre to pitch-edge): radial pitch turf; in day theme the pitch deepens to #1d3fb0 / #0f2470 so it remains a lit night pitch.

### League dots
Seven league colours in js/app.js, all taken from the world's own blue scale (ice, periwinkle, electric and its tints #7f9dff, #5d84ff, #2f56e0, #a9bcff), injected as `--c` on a 9px dot.

### Named Rules
**The One Light Rule.** Electric blue is the only saturated colour. It marks active state, the away side and substitution minutes; coral is reserved for live.
**The Blue Scale Rule.** League identity is a small dot in a blue from the world's own scale; never a rainbow swatch, a coloured card, a side stripe or a row tint.

## Typography

**Display Font:** Assistant (with Arial Hebrew, system-ui, Segoe UI, Arial)
**Body Font:** Assistant, the same family

**Character:** One humanist sans at heavy weights. 800 gives the brand, scores and headings a floodlit, stadium-board weight; 500 keeps running Hebrew calm. Loaded from Google Fonts at 500, 600, 700 and 800.

### Hierarchy
- **Display** (800, 30px / 27px under 560px, line-height 1, +0.01em): the site name.
- **Score** (800, 34px, line-height 1, tabular): match card and analysis scores.
- **Headline** (800, 20 to 23px, 1.2 to 1.35, balanced wrap): section heads (22px), analysis titles (20px), concept titles (23px).
- **Title** (800, 17 to 19px, 1.3 to 1.35): article titles, AI panel sub-heads, the lesson heading (18px), analysis team row (19px).
- **Body** (500, 16px, 1.5; reading paragraphs at 1.65): base text.
- **Label** (600 to 800, 0.76 to 0.92rem): meta lines, chips, view tabs, buttons, table headers, figcaptions.

### Named Rules
**The One Family Rule.** Assistant for everything; hierarchy comes from weight and size, not from a second face.
**The Tabular Rule.** Scores, times, minutes, formations and table numbers all use tabular figures.

## Layout

A single centred column, max-width 760px, 16px inline padding. The header holds the brand row (name plus two 40px round icon buttons) and a full-width segmented view switcher; below it a sticky, blurred league bar scrolls its chips horizontally with no visible scrollbar. Content is a vertical stack of lit panels with 8 to 14px gaps. Match cards use a three-column line (home, score, away) with the away team mirrored; the pitch figure sits inside the card with a two-sided figcaption (formation, team, coach). Article cards are a two-column grid with a round thumbnail at the inline end. Spacing rhythm: 4, 8, 12, 16px, with 20 to 28px before day and section heads. One breakpoint at 560px tightens type, the score column and thumbnails. Touch targets are 36 to 44px.

## Elevation & Depth

Depth is light, not lift. Panels are separated from the ground by their own gradient and a 1px inset hairline (`box-shadow: inset 0 0 0 1px`), never by an outer shadow. Hover strengthens the hairline rather than raising the card. Real shadows exist only on objects that sit on a surface: player discs and round thumbnails.

### Shadow Vocabulary
- **Panel Edge** (`inset 0 0 0 1px` hairline edge; strong edge on hover): every lit panel.
- **Concept Ring** (`inset 0 0 0 1px rgba(63, 107, 255, .55)`): the concept panel.
- **Disc Drop** (`drop-shadow(0 3px 2px rgba(0, 0, 0, .45))`): player discs on the pitch.
- **Thumb Lift** (`0 0 0 2px` strong edge, `0 6px 14px rgba(0, 0, 0, .35)`): round article thumbnails.

### Named Rules
**The Lit-Not-Lifted Rule.** Panels glow from their gradient and hairline; outer shadows belong only to discs and round thumbnails.

## Shapes

Generous, soft and round. Panels share one 22px radius; previews 18px, the pitch 16px, inset blocks 14px. A match card followed by its AI panel fuses into one shape (top corners on the card, bottom corners on the panel). Every control is a full pill (999px); icon buttons, player discs, league dots and article thumbnails are true circles. Lines are 1px hairlines; outlined controls take a 1px strong edge, icon buttons 2px.

## Components

### Buttons
- **Shape:** full pill.
- **Outline (default action):** transparent, 1px strong edge, periwinkle-soft label at 700, 38 to 44px high, 16px inline padding (load-more 32px). Hover lifts the label to ice and the border to periwinkle-soft. Used for lineup, AI, analysis actions and load-more.
- **Icon:** 40px circle, 2px strong edge, drawn SVG icon (stroke 1.9, currentColor). Disabled at 50% opacity.
- **Focus:** 2px periwinkle-soft outline, 3px offset, on every focusable element.

### Chips (league pages)
- **Style:** outlined pill, 36px, 1px strong edge, periwinkle-soft 700 label with a 9px blue-scale dot.
- **State:** active fills with the lit panel top tone, periwinkle-soft border and ice text.

### Cards / Containers
- **Corner Style:** 22px.
- **Background:** lit panel gradient.
- **Shadow Strategy:** panel edge only (see Elevation).
- **Internal Padding:** 12 to 18px.
- **Match card:** meta line (league, day, time, status pushed to the inline end; coral when live), then home team, 34px score, mirrored away team with 24px crests.
- **Lesson ("מה לומדים"):** not a nested box; a 1px strong-edge rule above an 18px periwinkle-soft heading and body text.

### Navigation
A segmented control: a flat-panel pill track with 4px padding and five equal pill tabs, idle in periwinkle-muted 700, active filled ice with deep navy text, colour transitions at 0.25s on the expo ease-out. League chips are the second level.

### Lit Pitch (signature)
An SVG pitch (340 by 210) on a radial night turf with a soft top highlight, 16px radius, periwinkle hairline markings at 35%. Players are 10-unit-radius discs: home ice white with navy numbers, away electric blue with a periwinkle ring and white numbers, short names beneath. On open, each disc walks out from the centre spot (scale 0.4, fade in) over 0.7s on cubic-bezier(.16, 1, .3, 1), delayed by its depth on the pitch so the shape assembles line by line. Reduced motion shows the discs in place. Substitutions follow as a hairline-ruled list led by electric minute pills.

### Round Thumbnail
Article cards carry a 92px circle (76px on phones) with a 2px strong-edge ring and thumb lift; when there is no image, the source name sits on a translucent midnight pill plate.

## Do's and Don'ts

### Do:
- **Do** build every content surface as a lit panel: the top-to-base navy gradient, 22px radius, 1px inset hairline.
- **Do** keep electric blue for active state, the away side and substitution minutes; coral only for live.
- **Do** draw players as discs, home ice and away electric, and keep the centre-spot walkout with its reduced-motion fallback.
- **Do** make controls pills: segmented view tabs, outlined chips and actions, round icon buttons.
- **Do** set every number in tabular figures and every word in Assistant.
- **Do** take any new league or category colour from the world's blue scale.

### Don't:
- **Don't** introduce a second saturated hue, a rainbow of league colours, or a second typeface.
- **Don't** lift panels with outer drop shadows; depth on panels is gradient plus hairline.
- **Don't** draw players as squares, shirts or plain dots without numbers.
- **Don't** use side-stripe borders, gradient text, emoji or glyph icons; icons are drawn SVG in currentColor.
- **Don't** place small labels above titles as kickers.

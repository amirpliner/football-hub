---
name: מגרש (Magrash)
description: A Hebrew RTL football dashboard styled as a sticker album; reading an item sticks a sticker into today's tally.
colors:
  ultramarine-shell: "#1f3bd6"
  ink-navy-ground: "#0c1440"
  panel-navy: "#131e5b"
  panel-navy-raised: "#1a2776"
  text-ice: "#f2f4ff"
  muted-periwinkle: "#a9b6ff"
  foil-gold: "#f2c230"
  gold-ink: "#0c1440"
  sticker-white: "#ffffff"
  live-coral: "#ff6b5e"
  light-ground: "#eef1ff"
  light-panel: "#ffffff"
  light-panel-raised: "#e3e8ff"
  light-text-ink: "#0c1440"
  light-muted: "#3a4799"
  light-gold-text: "#7a5600"
  light-live-red: "#c2271a"
typography:
  display:
    fontFamily: "Secular One, Arial Hebrew, Heebo, system-ui, sans-serif"
    fontSize: "30px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.01em"
  headline:
    fontFamily: "Secular One, Arial Hebrew, Heebo, system-ui, sans-serif"
    fontSize: "19px"
    fontWeight: 400
    lineHeight: 1.3
  title:
    fontFamily: "Secular One, Arial Hebrew, Heebo, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.3
  body:
    fontFamily: "Heebo, system-ui, -apple-system, Segoe UI, Arial, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Heebo, system-ui, -apple-system, Segoe UI, Arial, sans-serif"
    fontSize: "0.82rem"
    fontWeight: 500
    lineHeight: 1.5
    fontFeature: "tabular-nums"
rounded:
  xs: "4px"
  sm: "8px"
  md: "10px"
  lg: "12px"
  xl: "16px"
  pill: "99px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
components:
  tab-view:
    backgroundColor: "transparent"
    textColor: "{colors.sticker-white}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "38px"
  tab-view-active:
    backgroundColor: "{colors.sticker-white}"
    textColor: "{colors.ultramarine-shell}"
  chip-league:
    backgroundColor: "{colors.panel-navy}"
    textColor: "{colors.text-ice}"
    rounded: "{rounded.md}"
    padding: "0 14px"
    height: "36px"
  chip-league-active:
    backgroundColor: "{colors.foil-gold}"
    textColor: "{colors.gold-ink}"
  button-action:
    backgroundColor: "transparent"
    textColor: "{colors.muted-periwinkle}"
    rounded: "{rounded.sm}"
    padding: "0 11px"
    height: "32px"
  button-action-on:
    backgroundColor: "{colors.foil-gold}"
    textColor: "{colors.gold-ink}"
  button-primary:
    backgroundColor: "{colors.foil-gold}"
    textColor: "{colors.gold-ink}"
    rounded: "{rounded.sm}"
    padding: "0 14px"
    height: "34px"
  input-field:
    backgroundColor: "{colors.panel-navy}"
    textColor: "{colors.text-ice}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "40px"
  sticker:
    backgroundColor: "{colors.panel-navy-raised}"
    rounded: "{rounded.md}"
    width: "104px"
    height: "78px"
  concept-panel:
    backgroundColor: "{colors.panel-navy}"
    rounded: "14px"
  ai-panel:
    backgroundColor: "{colors.panel-navy}"
    textColor: "{colors.text-ice}"
    rounded: "{rounded.lg}"
    padding: "14px"
  album-slot:
    rounded: "{rounded.xs}"
    width: "20px"
    height: "27px"
---

# Design System: מגרש (Magrash)

## Overview

**Creative North Star: "The Sticker Album"**

Reading is collecting. A saturated ultramarine shell holds the site name, view tabs and a per-day tally of dashed slots; below it an ink-navy ground carries a quiet, ruled list of articles. Each article owns a white-bordered, die-cut sticker thumbnail, and each item read fills one slot in the tally with a mini sticker in its league's colour. The loud colour lives in the shell, the stickers and the gold foil; the reading surface stays calm so Hebrew titles scan fast on a phone.

The system is dense but not cramped: hairline-ruled rows instead of cards-in-boxes, a single 860px reading column, 16px side padding. Gold foil is the only progress and active-state colour, so wherever gold appears it means "you are here" or "this is done". There are two themes, dark (default) and light, that share the shell, the gold and the stickers and swap only ground, panels, text and the two text-on-gold-sensitive tones.

**Key Characteristics:**
- Ultramarine shell over ink-navy ground; gold foil reserved for active, progress, primary action.
- White 3px die-cut border on every sticker; league identity carried by a coloured dot with a white ring.
- Secular One for titles, scores and numerals-as-display; Heebo for everything else; tabular figures on all numbers.
- RTL by default; layout uses logical properties (inline-start/end).
- Drawn SVG icons at one stroke weight (1.75) inheriting currentColor.

## Colors

A blue-on-blue field with one metallic accent; league colours appear only as small swatches and sticker fills.

### Primary
- **Ultramarine Shell** (#1f3bd6): the top band, the theme-color, and the active-tab text colour on white. Same in both themes.
- **Foil Gold** (#f2c230): active league chip, on-state action buttons, primary buttons, the full-day tally, hover underline on titles, focus ring, selection, caret and accent-color, search highlights.

### Secondary
- **Live Coral** (#ff6b5e, light theme #c2271a): live match minute and over-limit tweet counter only.

### Neutral
- **Ink-Navy Ground** (#0c1440; light #eef1ff): page background and sticky league bar.
- **Panel Navy** (#131e5b; light #ffffff): chips, inputs, AI panels, concept box, dialogs.
- **Raised Panel Navy** (#1a2776; light #e3e8ff): sticker placeholder, keyword pills, tweet angle blocks, scrollbar thumb.
- **Ice Text** (#f2f4ff; light #0c1440): primary text.
- **Muted Periwinkle** (#a9b6ff; light #3a4799): meta lines, read-item titles, secondary buttons, hints.
- **Sticker White** (#ffffff): sticker borders, tally slot borders, dot rings, the active view tab.
- **Gold Text** (#f2c230; light #7a5600): gold used as text or outline on panels, darkened in light theme for contrast.
- **Hairline** (rgba(169,182,255,.22); light rgba(12,20,64,.16)): all row rules and borders.

### League swatches
Ten league colours are assigned in js/app.js (israel #3aa0ff, premier league #a259ff, la liga #ffb01f, serie a #19a35b, bundesliga #e63a2e, ligue 1 #25c9e8, championship #ff5fa2, liga portugal #0fbf9a, eredivisie #ff6f3c, champions league #8fa6ff) and injected as `--c`. They are data, not UI chrome.

### Named Rules
**The Foil Rule.** Gold means active, progress or primary action; nothing decorative is gold. Gold text on light panels uses the darker #7a5600.
**The League Dot Rule.** League identity is a small dot or sticker fill with a white ring, never a coloured card, border-left stripe or full-row tint.

## Typography

**Display Font:** Secular One (with Arial Hebrew, Heebo, system-ui)
**Body Font:** Heebo (with system-ui, Segoe UI, Arial)

**Character:** Secular One gives titles and scores a chunky, sticker-label voice; Heebo keeps running Hebrew and Latin text neutral and legible. Both load from Google Fonts.

### Hierarchy
- **Display** (400, 30px / 27px under 560px, line-height 1, +0.01em): site name in the shell.
- **Headline** (400, 20px, 1.2; card titles 19px / 18px mobile, 1.3, balanced wrapping): section headings and article titles.
- **Title** (400, 15-18px, 1.3): day dividers, tally count, concept head, AI panel sub-heads.
- **Body** (400, 16px, 1.5): base text; summaries 0.9-0.96rem.
- **Label** (500/700, 0.76-0.88rem): meta lines, action buttons, table headers, tag text. Score digits use Secular One 20px.

### Named Rules
**The Tabular Rule.** Every score, time, count and table number uses tabular figures.
**The Two-Face Rule.** Secular One only for titles, scores, counts and headings; Heebo for all interface text. No third family.

## Layout

A single centred column, max-width 860px with 16px inline padding. The shell band is full-bleed, followed by a sticky bar (league chips plus a compact mini-tally that appears once scrolled). Article rows are a two-column grid: text at the inline start, sticker at the inline end (104x78, video 128x84; 92x70 and 112x74 under 560px). Match rows use a 52px / 1fr / auto / 1fr grid; tables scroll horizontally. Spacing rhythm: 4, 8, 12, 16, 24px, with 16px row padding and 24px day-divider top margin. Breakpoints: 700px (filters collapse behind a toggle), 560px (smaller type, stickers and slots; 40px minimum touch height on action buttons). Primary touch targets are 32-44px.

## Elevation & Depth

Flat by default: rows are separated by 1px hairlines and panels by tonal steps (ground, panel, raised panel). Depth is reserved for the sticker, which sits above the page with a soft two-layer shadow, and for filled tally slots.

### Shadow Vocabulary
- **Sticker Lift** (`0 3px 8px rgba(0,0,0,.4), 0 1px 1px rgba(0,0,0,.3)`; light theme uses rgba(12,20,64,.3/.25)): sticker thumbnails.
- **Slot Lift** (`0 2px 4px rgba(0,0,0,.35)`): filled tally slots.
- **Stick Landing** (`0 10px 18px rgba(0,0,0,.45)` fading to rest): start frame of the stick animation.

### Named Rules
**The Soft Lift Rule.** Shadows are soft and blurred, only under stickers and slots; never a hard offset, never on rows or panels.

## Shapes

Rounded, sticker-like geometry. Stickers 10px radius with a 3px white border and clipped image; tally slots are 20x27 portrait rectangles with 4px radius (dashed 1.5px when empty, solid 2px white border plus fill when stuck). Chips 10px, inputs 10px, action buttons 8px, panels 12px, concept box 14px with a 1.5px gold border, dialogs 16px. Tabs, tools and the load-more button are full pills (99px). Dots are circles with a 1.5px white ring.

## Components

### Buttons
- **Shape:** 8px radius for actions, 10px in dialogs, pill for shell tools and load-more.
- **Primary:** foil gold fill, ink text, 700 weight, 34px high (tweet row, keyword add).
- **Action (secondary):** transparent with hairline border, muted text, 32px high; hover brightens text and border; `.on` becomes gold fill. AI and tweet-angle buttons use gold text with a translucent gold border.
- **Focus:** 2px gold outline, 2px offset, on every focusable element.
- **Shell tools:** 36px pills on translucent white (14%, 24% on hover); disabled at 50% opacity.

### Chips (league pages)
- **Style:** panel fill, hairline border, 10px radius, 36px high, colour dot with white ring, muted count.
- **State:** active is solid foil gold with ink text and bold weight. The row scrolls horizontally with hidden scrollbar.

### Cards / Containers
Article rows are not boxed: grid with hairline bottom border. Read items drop to 78% opacity with muted titles. Title hover adds a 2px gold underline. Panels (AI, concept, dialog, tweet angle) use the panel tones with 12-16px radius and no shadow.

### Inputs / Fields
- **Style:** panel fill, hairline border, 10px radius, 40px high; placeholder in muted at 85%.
- **Focus:** the global 2px gold ring; caret is gold.

### Navigation
View tabs sit in the shell: pills, white at 80% text when idle, solid white with ultramarine bold text when active. League chips below are the second-level navigation (see Chips).

### Album Tally (signature)
A row of 20 portrait slots under the view tabs with a Secular One count ("היום 7/20"). Empty slots are dashed white-55%. Each item read fills a slot with the league colour, a 2px white border and Slot Lift; the new slot plays a 0.5s "stick" animation (scale 1.7, rotate -16deg to rest, ease cubic-bezier(.16,1,.3,1)). When the day is complete all slots turn gold. A compact 5x15px mini-tally shows in the sticky bar after scrolling. Reduced motion disables the animation.

### Sticker
The article thumbnail: 3px white border, 10px radius, soft lift, league colour as fallback fill. Tile variant shows the source name on a translucent ink plate; video variant adds a 36px round play button that turns gold on hover.

## Do's and Don'ts

### Do:
- **Do** use foil gold (#f2c230) only for active, progress and primary-action states.
- **Do** put league identity in a dot or sticker fill with a white ring.
- **Do** keep rows flat with 1px hairlines; reserve soft shadows for stickers and tally slots.
- **Do** set every number in tabular figures and every title in Secular One.
- **Do** write new layout with logical properties for RTL, and keep the 2px gold focus ring.
- **Do** test any new gold text in light theme against #7a5600.

### Don't:
- **Don't** introduce a third typeface or a second accent colour for state.
- **Don't** wrap rows in boxed cards or tint rows by league.
- **Don't** use hard offset shadows, side-stripe borders, or gradient text.
- **Don't** use emoji or glyph icons; icons are drawn SVG at stroke 1.75 in currentColor.
- **Don't** place small headings or labels above titles as kickers.

---
version: 1
slug: "index-html"
primary_target: "index.html"
related_targets: ["css/style.css","js/app.js"]
---

# Surface brief: מגרש (feed, matches, tables)

Mode: Operate. Personal football dashboard for one Hebrew-speaking fan, mostly on a phone in short glances, sometimes at a desk. Static HTML/CSS/JS, RTL, source-language article text inside a Hebrew UI.

Job: see what is new across ten leagues in seconds, learn tactics from analysis items, keep or turn items into tweet angles. Content: articles (with Hebrew summaries), videos, fixtures/results, tables, watchlist, saved. Constraints: no frameworks, mixed Hebrew/Latin text must stay correct, AI text is labeled as AI.

Unresolved: none. The user picked the sticker-album sketch (.impeccable/mocks/decision/assigned.html).

## Direction contract

THESIS: Reading is collecting. Every article is a die-cut sticker, and every item read sticks one sticker into tonight's album tally; it refuses the generic dark news list with one flat accent.

OWN-WORLD: Ultramarine shell (#1f3bd6) over an ink-navy ground (#0c1440); stickers carry a 3-4px white die-cut border with a soft offset shadow and a faint gloss; foil gold (#f2c230) for progress, active page tab and live state; signal red and pitch green as league swatches. Display face Secular One, body Heebo, tabular figures for every score, time and table number; drawn SVG icons in one stroke weight; native selection, scrollbar, focus and caret themed from the palette.

STORY: At a glance the visitor knows how much is new and which league it belongs to; scans titles on a phone, opens the source, and watches the album fill. Saved and watchlist items stay one tap away, and an angle button turns analysis into tweet drafts.

FIRST VIEWPORT: 390px wide. A full-width ultramarine band: site name in Secular One 28px with the view tabs (news, matches, tables, watch, saved) beneath it; below that the album tally, twenty dashed slots, filled slots show a mini white-bordered sticker in the league's colour, with the count "היום 7/20". Then the league page tabs as pills with a colour dot, gold when active. Then the first cards: title in Secular One, a meta line below it, the Hebrew summary, actions, and the sticker thumbnail at the inline end. No kicker above any heading.

FORM: Sticker Album, candidate 5 of 7 on the grounded list, seed:a5ed7fdf811124ce.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

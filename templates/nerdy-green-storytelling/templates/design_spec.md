---
style_id: nerdy-green-storytelling
kind: style
summary: Nerdy-green knowledge-card aesthetic fused with Storytelling-with-Data discipline — table data in, one-sentence-conclusion pages out, native editable charts.
keywords: [data, storytelling, dashboard, card, green, analysis, decision]
---

# Nerdy Green Storytelling — Style Specification

> Method and design defaults only. No project communication contract, brand identity, page structure, or SVG prototypes.

## I. Style Overview

| Property | Value |
|---|---|
| Style Name | Nerdy Green Storytelling |
| Best Fit | Decision summaries built from tabular data: weekly/monthly business reviews, metric deep-dives, attribution analysis, executive readouts |
| Reusable Intent | Turn a table into a decision: every page states one testable conclusion, every chart marks only what deserves attention, and the deck walks conflict → magnitude → attribution → action |
| Sources | Authored 2026-09-06 from the "nerdy green" Xiaohongshu knowledge-card series (11 reference images) and Cole Knaflic, *Storytelling with Data* |

## II. Communication Method

- **Preferred Mode**: reader-led decision summary. Pyramid structure: one governing conclusion, supported by MECE evidence pages, each backed by chart-level facts. Support and contradicting evidence both appear; never argue one side silently.
- **One-Sentence Discipline (hard rule)**: every page and every chart must be stateable in one sentence of ≤30 characters that a decision-maker can act on. The sentence IS the page title — descriptive titles ("GMV 趋势图") are forbidden. A page or chart that cannot carry its sentence is cut.
- **Page Message Discipline**: each page carries exactly one beat of the four-beat skeleton — 冲突 (what happened) → 放大 (how big, who is affected) → 归因 (≤3 ranked causes) → 行动 (what to do next). Cover states the governing conclusion; optional appendix holds full data tables.
- **Claim Discipline**: every number on a page traces to the project's `facts.json` (source, scope, period recorded at analysis time). Invented, rounded-up, or "roughly right" figures are forbidden. Counter-evidence is stated, not trimmed.

## III. Page Role Vocabulary

| Role | Communication Job | Evidence Obligation | Composition Tendency |
|---|---|---|---|
| Cover / 结论 | State the governing conclusion as the deck's only headline | One sentence ≤30 chars, carrying the key delta number | White title card on canvas; deck id `@DATA2PPT 0XX` top-right; date/scope small |
| 冲突 | Make the change felt as a deviation, not a topic | Anomaly located on the series with exact period and delta; grey context vs highlighted anomaly | Main chart card + slim fact card; anomaly segment in accent color |
| 放大 | Give the change magnitude and blast radius | From/to values, affected users/orders count; each traced to facts.json | Big-number cards (mono, tabular); numbers dominate, prose minimal |
| 归因 | Rank what caused it, honestly | ≤3 causes ranked by contribution (pp or %); each with mechanism one-liner; state unknowns | Waterfall or horizontal bar card; contributions labeled on marks |
| 行动 | Convert analysis into decisions | Each action tied to an attribution line; expected effect quantified when data allows | Numbered action cards; each action ≤1 line, owner/deadline slots |
| 附录 | Give auditors the full picture | Full cleaned table(s) behind the deck's claims | Dense native table card, quiet styling, clearly secondary |

## IV. Evidence & Data Expression

- **Argument Trace**: facts.json is the single numeric source of truth for planning and authoring. Each fact row records: metric, value(s), period, scope, source cell/column. Charts re-derive geometry from facts, never from memory.
- **Charts**: grey base + accent for the attended series/segment only (`#1F4D3F` normal emphasis, `#C0392B` anomaly/negative). No gridlines, no legends (annotate directly on marks), no dual axes, no 3D/shadow/gradient decoration. Keep left+bottom axis only; label values directly on or beside marks.
- **Chart Type Routing**: one number → hero number page (no chart); 2 numbers → text + delta; 3–5 categories → horizontal bar, descending; time trend → line; attribution decomposition → waterfall; composition → stacked bar (pie forbidden above 3 slices); correlation (few points) → scatter; (many points) → heatmap.
- **Native Editability**: charts and tables compile to native PPTX objects (`--native-charts-and-tables`); they must remain data-editable in PowerPoint. Chart geometry passes the project's verify-charts calibration against facts.json before export.
- **Tables**: appendix only, or when the row-level detail is itself the beat. Native table, zebra-free, thin `#D8E5DE` rules.

## V. Visual System Defaults

- **Canvas tokens**: canvas `#EFEFED` warm grey; card `#FFFFFF`, radius 8px, 1px `#E3E3E0` border, shadow `0 1px 4px rgba(0,0,0,.06)`; primary ink `#1D1D1F`; muted ink `#8A8A86`; primary green `#1F4D3F`; sage `#7FA99B` (secondary lines, dashed annotation frames); light green fill `#EAF1ED`; card divider `#D8E5DE`; alert red `#C0392B` (anomaly/negative only — color marks attention, nothing else).
- **Composition — 卡片矩阵 (card matrix)**: each page is 2–4 white cards on the canvas with consistent 24–32px gutters; one main card carries the beat's chart or hero number, 1–3 slim cards carry facts, evidence, or annotations. Dashed sage frames (`1.5px dashed #7FA99B`, `#F7FAF8` fill) mark 证据/结论 annotation boxes. Header row: `P0X · 页面角色` left (bold, small sub-label), `@DATA2PPT 0XX` right (mono, green).
- **Density**: information-rich but card-disciplined — every text block lives inside a card; nothing floats on the canvas except the header row. Cards never overlap.
- **Typography**: sans-serif CJK (system PingFang/Noto Sans SC); titles 28–34px bold; body 14–16px; captions/labels 11–12px muted. Numbers: monospace (SF Mono/JetBrains Mono), tabular, large for hero figures (48–72px) with tight tracking; unit suffixes small. Accent color on numbers only when the number is the attention target.
- **Decoration**: flat. No gradients, shadows beyond the card lift, icon flourishes, or page furniture beyond the header row. Small pill tags (`#EAF1ED` bg, green text, 3px radius) for kickers like 证据/归因/行动.

## VI. Image & Icon Direction

- **Preferred Image Rendering**: none by default. This style is data-first; generated imagery is out of voice. If a cover needs warmth, prefer typographic treatment over stock photos.
- **Image Usage**: only user-supplied screenshots or diagrams that are themselves evidence; place inside a card with caption + source.
- **Icon Treatment**: minimal, single visual language (outline, e.g. tabler-outline from the project icon library), used as quiet 16–20px identifiers for card categories (冲突/归因/行动), never as decoration rows. No emoji.

## VII. Review Focus
<!-- visual-review-trigger: explicit-user-only -->

- Every page title is a ≤30-char conclusion sentence; no descriptive titles survive.
- Every chart: grey base + single accent focus, no gridlines/legend/dual-axis/decoration; values annotated on marks.
- Every number traces to facts.json; waterfall attribution ≤3 causes.
- Card matrix: 2–4 cards per page, consistent gutters, no floating text, no card overlap.
- Tokens respected: exact hex values, mono numerals, dashed-frame annotations, `@DATA2PPT 0XX` header id.
- Alert red appears only on anomaly/negative targets; sage dashed frames only on annotation boxes.

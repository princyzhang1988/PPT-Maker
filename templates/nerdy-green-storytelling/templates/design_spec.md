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
- **Decision Discipline** (after OpenAI, *product-business-analysis*): the deck exists to inform a decision, stated up front (question, decision, audience, action, scope, comparison). Every comparison names its baseline, denominator, and normalization — a number without its comparison point does not ship. When evidence conflicts, present the conflict and the better-supported reading; never smooth it over. Incomplete evidence yields a provisionally worded title plus a visible caveat, never false confidence. The action page hands off four things: what to do, why the evidence supports it, which caveats/dependencies matter, and what follow-up analysis would raise confidence.

## III. Page Role Vocabulary

| Role | Communication Job | Evidence Obligation | Composition Tendency |
|---|---|---|---|
| Cover / 结论 | State the governing conclusion as the deck's only headline | One sentence ≤30 chars, carrying the key delta number | White title card on canvas; deck id `@DATA2PPT 0XX` top-right; date/scope small |
| 冲突 | Make the change felt as a deviation, not a topic | Anomaly located on the series with exact period and delta; grey context vs highlighted anomaly | Main chart card + slim fact card; anomaly segment in accent color |
| 放大 | Give the change magnitude and blast radius | From/to values, affected users/orders count; each traced to facts.json | Big-number cards (mono, tabular); numbers dominate, prose minimal |
| 归因 | Rank what caused it, honestly | ≤3 causes ranked by contribution (pp or %); each with mechanism one-liner; state unknowns | Waterfall or horizontal bar card; contributions labeled on marks |
| 行动 | Convert analysis into decisions | Each action tied to an attribution line; expected effect quantified when data allows | Numbered action cards; each action ≤1 line, owner/deadline slots |
| 附录 | Give auditors the full picture | Full cleaned table(s) behind the deck's claims | Dense native table card, quiet styling, clearly secondary |
| 数据核查 | 证明"变化是真的"再开始叙事：链路核查、稳定性（CV 阈值）、异常值处理 | facts.json `quality_check` 字段；CV 数值与阈值对照；剔除的异常值披露 | 单张窄卡放在冲突页前或并入口径卡；不稳定信号用 #55816D |
| 假设验证 | 列出归因假设清单及每条的验证方法与结论，支撑"≤3 个原因"的证据链 | 每个假设一行：假设 → 验证方法 → 支持/排除；排除项也要展示 | 表格式卡片；支持项深绿标记，排除项灰显 |

## IV. Evidence & Data Expression

- **Argument Trace**: facts.json is the single numeric source of truth for planning and authoring. Each fact row records: metric, value(s), period, scope, source cell/column. Charts re-derive geometry from facts, never from memory.
- **Charts**: grey base + attention mark for the attended series/segment only — decline/anomaly uses `#55816D` (mid green), positive uses `#A9C3B6` (pale), structure/totals use `#1F4D3F`. No gridlines, no legends (annotate directly on marks), no dual axes, no 3D/shadow/gradient decoration. Keep left+bottom axis only; label values directly on or beside marks.
- **Chart Type Routing**: one number → hero number page (no chart); 2 numbers → text + delta; 3–5 categories → horizontal bar, descending; time trend → line; attribution decomposition → waterfall; composition → stacked bar (pie forbidden above 3 slices); correlation (few points) → scatter; (many points) → heatmap.
- **Native Editability**: charts and tables compile to native PPTX objects (`--native-charts-and-tables`); they must remain data-editable in PowerPoint. Chart geometry passes the project's verify-charts calibration against facts.json before export.
- **Tables**: appendix only, or when the row-level detail is itself the beat. Native table, zebra-free, thin `#D8E5DE` rules.

## V. Visual System Defaults

- **Canvas tokens**: canvas `#F7F7F4` near-white warm grey (the reference series keeps canvas and cards in one light family — hierarchy comes from hairline borders and inset panels, never from a dark field under white cards); card `#FFFFFF`, radius 8px, 1px `#E3E3E0` border, no shadow (flat, per reference); inset panel `#F2F2EF` (quiet secondary zone inside a page); primary ink `#1D1D1F`; muted ink `#8A8A86`; primary green `#1F4D3F` (titles, totals, structure); decline green `#55816D` (attention: anomaly marks, negative factors, down-numbers — the series is deliberately monochrome green, no red); sage `#7FA99B` (secondary lines, dashed annotation frames); gain green `#A9C3B6` (positive factors); light green fill `#EAF1ED`; card divider `#D8E5DE`. Direction within the green ramp is carried by lightness (deep = structure/total, mid = decline, pale = gain) plus explicit +/- labels — never by hue contrast.
- **Composition — 卡片矩阵 (card matrix)**: each page is 2–4 white cards on the canvas with consistent 24–32px gutters; one main card carries the beat's chart or hero number, 1–3 slim cards carry facts, evidence, or annotations; a full-width composition (cover title card spanning the content area edge-to-edge) is preferred whenever a single beat owns the page — floating mid-size cards on empty canvas are avoided. Dashed sage frames (`1.5px dashed #7FA99B`, `#F7FAF8` fill) mark 证据/结论 annotation boxes. Header row: `P0X · 页面角色` left (bold, small sub-label), `@DATA2PPT 0XX` right (mono, green).
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
- Alert/decline marks appear only on anomaly/negative targets, in `#55816D`; sage dashed frames only on annotation boxes. No red anywhere in the deck — the series is monochrome green.
- Every page title is a ≤30-char conclusion sentence; no descriptive titles survive (restated from §II for review convenience).

## VIII. Flowchart Style Rules (archify classic mapping)

Topology prototyped interactively with the archify skill (`workflow` type, `classic` preset); the approved look is compiled to fully native PowerPoint objects through the project SVG pipeline. Reference prototype: `flowchart/flowchart_classic.html` in the workspace root project.

- **Canvas & frame**: one full-width white card (`1px #E3E3E0` border, 8px radius) under the page headline; the diagram lives entirely inside it. Swimlanes are horizontal bands drawn as `1px dashed #D8E5DE` rounded rects (6,4) with no fill; each lane label sits at the band's top-left — `0X / 泳道名`, 11px, `#8A8A86`.
- **Nodes**: rounded rects (`rx 8`, native `roundRect`), 150×56–60px; stroke 1.5px in a role color, 2px when the node is the page's focus; title 14px bold `#1D1D1F` centered + sublabel 11px `#8A8A86`. Role colors (green ramp, no red) pair a border with a fill tint so types stay legible without hue variety: main-path/positive white fill + `#1F4D3F` border; risk/exception (未解决、投诉类) fill `#E7EFEA` + `#55816D` border; supporting/analysis (数据、原因) white fill + `#7FA99B` border; external/entry white fill + `#C7D3CC` border; the final action/outcome node fills `#EAF1ED` with `#1F4D3F` border and text. Semantic shape upgrades when the meaning demands it: decision → `flowChartDecision`, start/end → `flowChartTerminator`, document/report → `flowChartDocument` (all through `preset_shape_svg.py`, never hand-drawn paths).
- **Legend (mandatory)**: with hue variety collapsed into one green ramp, the legend is the only key to node/edge semantics and must never be dropped. One row of small swatch chips (24×14 rounded rects replicating each node style + 11px `#8A8A86` labels; line-style samples for 正常/异常/分析 flow) along the card's bottom edge.
- **Edges**: straight relationships are `<line>`; a stock elbow is a `bentConnector*` preset — never a hand path. Normal flow 1.5px solid `#1F4D3F`; the emphasized main path 2px; exception flow 1.5px dashed (5,3) `#55816D`; analysis/feedback flow 1.5px dashed (5,3) `#7FA99B`. Every edge carries a native triangle `tailEnd` via the §1.1 marker contract (marker fill matches its stroke; one marker def per color per page). Edge labels 11px `#8A8A86` beside/above the line; omit a label only when both endpoints fully imply it.
- **Layout discipline**: prefer an axis-aligned grid (all edges horizontal or vertical) so straight `<line>` connectors suffice; introduce a bentConnector only when a diagonal relationship is unavoidable. Target ≤12 nodes, ≤4 lanes, one obvious main path; keep ~60–120px between connected nodes so labels fit. Wrap the whole diagram in one root group (lanes, edges, and nodes as nested groups) so connector lines never create root-group overlap; bounds = the card rect.
- **Occlusion guard (checked in the 2026-09-06 demo)**: a lane label and the first node of its lane must never share x-range while the node's top edge sits at or above the label's descender line — reserve ≥10px vertical clearance between a label's baseline zone and any node rect (in the demo: label baseline 186, node top 196). The quality gate checks text against group bounds but not intra-group z-order collisions, so after export always render the page (headless browser or PowerPoint) and eyeball label/node crossings — PowerPoint's font metrics occlude more than the browser preview does.
- **Numbers on nodes**: every metric shown on a node traces to the project's `facts.json`, same as any other page content.

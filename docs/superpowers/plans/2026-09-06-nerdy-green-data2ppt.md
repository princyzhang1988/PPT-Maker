# nerdy 绿数据叙事 PPT 流水线（data2ppt）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于 ppt-master 搭建可复用流水线：用户给表格数据 → 大纲一次确认 → 输出 nerdy 绿风格、原生可编辑的 16:9 PPTX。

**Architecture:** 三件套——ppt-master 完整克隆（能力本体，不改动）、项目级风格工作区 `templates/nerdy-green-storytelling/`（视觉 tokens + Storytelling 方法论，作为显式 workspace root 传入 ppt-master Stage 1）、`data2ppt.md` 使用约定（收窄交互节奏与质量红线）。所有生成走 ppt-master Generate PPTX 路线，图表经 `--native-charts-and-tables` 导出为原生可编辑对象。

**Tech Stack:** ppt-master (MIT, Python)、pandas（数据探查）、git。

**设计文档:** `docs/superpowers/specs/2026-09-06-nerdy-green-data2ppt-design.md`

**环境备注:** 网络需走代理 `export https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897 all_proxy=socks5://127.0.0.1:7897`。所有 Python 命令使用项目虚拟环境 `.venv/bin/python`。

---

### Task 1: 获取 ppt-master 并安装依赖

**Files:**
- Create: `ppt-master/`（外部仓库克隆，加入 .gitignore，不入本项目 git）
- Modify: `.gitignore`
- Create: `.venv/`（虚拟环境，加入 .gitignore）

- [ ] **Step 1: 克隆 ppt-master**

```bash
cd /Users/princyzhang/PPT-Maker
export https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897 all_proxy=socks5://127.0.0.1:7897
git clone --depth 1 https://github.com/hugohe3/ppt-master ppt-master
```

Expected: `done.`，`ls ppt-master/skills/ppt-master/SKILL.md` 存在。

- [ ] **Step 2: 创建虚拟环境并安装依赖**

```bash
python3 -m venv .venv
.venv/bin/pip install -r ppt-master/requirements.txt
```

Expected: pip 安装成功退出码 0。若个别依赖在 macOS/arm64 编译失败，读 `ppt-master/skills/ppt-master/requirements.txt` 逐段排查，可跳过纯可选依赖（如 TTS backend、curl_cffi），核心依赖（python-pptx、lxml、Pillow、pandas 等）必须装上。

- [ ] **Step 3: 验证核心脚本可运行**

```bash
.venv/bin/python ppt-master/skills/ppt-master/scripts/project_manager.py --help | head -5
.venv/bin/python ppt-master/skills/ppt-master/scripts/svg_quality_checker.py --help | head -5
.venv/bin/python ppt-master/skills/ppt-master/scripts/svg_to_pptx.py --help | head -5
```

Expected: 三个命令均打印 usage，退出码 0。

- [ ] **Step 4: 更新 .gitignore 并提交**

`.gitignore` 追加两行：

```
ppt-master/
.venv/
```

```bash
git add .gitignore
git commit -m "chore: 忽略 ppt-master 克隆与虚拟环境"
```

---

### Task 2: 创建风格工作区目录骨架

**Files:**
- Create: `templates/nerdy-green-storytelling/templates/`（目录）
- Create: `templates/nerdy-green-storytelling/images/.gitkeep`
- Create: `templates/nerdy-green-storytelling/icons/imported/.gitkeep`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p templates/nerdy-green-storytelling/templates
mkdir -p templates/nerdy-green-storytelling/images
mkdir -p templates/nerdy-green-storytelling/icons/imported
touch templates/nerdy-green-storytelling/images/.gitkeep
touch templates/nerdy-green-storytelling/icons/imported/.gitkeep
```

该布局镜像 ppt-master 内置库样式包（如 `templates/styles/narrative-keynote/`：`templates/design_spec.md` + 可选 `images/` + `icons/imported/` + `exports/`）。风格以**显式 workspace root**（`templates/nerdy-green-storytelling`）传入 Generate 流程 Step 3 的 `explicit_workspace_roots`，不注册进 ppt-master 库索引、不改动 ppt-master 仓库内部。

- [ ] **Step 2: 提交**

```bash
git add templates/
git commit -m "chore: 风格工作区目录骨架 nerdy-green-storytelling"
```

---

### Task 3: 撰写风格 spec（核心创作）

**Files:**
- Create: `templates/nerdy-green-storytelling/templates/design_spec.md`

- [ ] **Step 1: 写入完整风格 spec**

格式对照内置样式 `ppt-master/skills/ppt-master/templates/styles/narrative-keynote/templates/design_spec.md`（frontmatter: style_id/kind/summary/keywords；正文 I–VII 节）。写入以下完整内容：

```markdown
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
```

- [ ] **Step 2: 结构自检**

```bash
.venv/bin/python - <<'EOF'
import re
text = open('templates/nerdy-green-storytelling/templates/design_spec.md').read()
assert text.startswith('---'), 'missing frontmatter'
fm = text.split('---')[1]
assert 'style_id: nerdy-green-storytelling' in fm
assert 'kind: style' in fm
for sec in ['## I.', '## II.', '## III.', '## IV.', '## V.', '## VI.', '## VII.']:
    assert sec in text, f'missing {sec}'
print('spec structure OK')
EOF
```

Expected: `spec structure OK`。

- [ ] **Step 3: 提交**

```bash
git add templates/nerdy-green-storytelling/templates/design_spec.md
git commit -m "feat: nerdy-green-storytelling 风格 spec（tokens+Storytelling 方法论）"
```

---

### Task 4: 撰写 data2ppt.md 使用约定

**Files:**
- Create: `data2ppt.md`（项目根目录）

- [ ] **Step 1: 写入完整使用约定**

```markdown
# data2ppt — 表格数据 → nerdy 绿叙事 PPT 使用约定

把表格数据交给本项目的 AI 助手并说"生成 PPT"，即按本约定走 ppt-master 的
Generate PPTX 路线。本文件是流程收窄说明书，不是新代码；ppt-master 本体保持原样。

## 固定路径与环境

- `SKILL_DIR` = `/Users/princyzhang/PPT-Maker/ppt-master/skills/ppt-master`
- Python = `/Users/princyzhang/PPT-Maker/.venv/bin/python`
- 风格工作区（显式 root）= `/Users/princyzhang/PPT-Maker/templates/nerdy-green-storytelling`
- 画布：16:9，viewBox `1280×720`
- 页数默认 5–6 页（封面/冲突/放大/归因/行动 + 可选附录），大纲确认时可调

## 交互流程（严格按序）

1. **接收输入**：Excel/CSV 文件、对话内贴的表格、或表格+背景描述。用 pandas
   读入并规范化（列类型、时间粒度、指标识别）。
2. **问方向（唯一前置提问）**：问用户"有没有已经想好的论点/论据方向？"
   - 有 → 按论点做 MECE 金字塔拆解，定向探查支持与反驳证据；
   - 无 → 自动探查：趋势/异常/归因/对比，取最强信号推导结论。
3. **写 facts.json** 到 `<project>/sources/`：每条事实含
   `{metric, value(s), period, scope, source}`，是全流程唯一数值真源。
4. **大纲确认（唯一阻塞点）**：按金字塔呈现页清单
   （每页：编号、角色、一句话标题、图表类型与数据来源），等用户确认。
   每页标题必须 ≤30 字结论句；写不出这句话的页/图砍掉。
5. **自动执行到交付，中途不再提问**：
   - `project_manager.py init <name> --format presentation_core_43 不适用时用默认 16:9`
     （16:9 用 `1280×720` viewBox，spec_lock 记录）
   - `project_manager.py import-sources <project> <数据文件> facts.json`
   - Stage 1 按"明确委托"代决策：free_design 不适用，必须传入风格工作区 root
     （`explicit_workspace_roots=[<风格工作区>]`），沟通契约 = reader-led 决策摘要
   - Executor 逐页生成 SVG（P01–P05 早检门 → 连续生成 → 终检门 0 错误）
   - 含数据图表 → 强制 `verify-charts` 对照 facts.json
   - `svg_to_pptx.py <project> --native-charts-and-tables`
   - 交付 `exports/*.pptx`，报告 POSTFLIGHT 结果与 warnings

## 质量红线

- 每个数字可追溯 facts.json；禁止生成时编造/脑补数值
- 每页 page job = 它的一句话结论（写进 design_spec §IX）
- 归因 ≤3 个原因；饼图 >3 分类禁用；无网格线/图例/双轴/3D
- 颜色只用于标记关注点（墨绿=强调，砖红=异常/负向，其余灰）
- 图表/表格必须原生可编辑（--native-charts-and-tables），禁止截图嵌页

## 失败恢复

- 单页失败：按 ppt-master failure-recovery 修该页所属层，不重跑规划
- 上下文丢失：`继续生成 projects/<project_name>` 走 resume-execute
- 风格/质量争议：对照 templates/nerdy-green-storytelling/templates/design_spec.md
```

- [ ] **Step 2: 提交**

```bash
git add data2ppt.md
git commit -m "docs: data2ppt 使用约定（交互节奏+质量红线+ppt-master 命令映射）"
```

---

### Task 5: 准备端到端验收数据

**Files:**
- Create: `examples/gmv_weekly.csv`
- Create: `examples/gmv_attribution.csv`

- [ ] **Step 1: 写入 GMV 样例数据**（来自设计文档 §6 的 Storytelling 样例）

`examples/gmv_weekly.csv`：

```csv
week,gmv_wan
W19,1310
W20,1330
W21,1290
W22,1320
W23,1280
W24,1300
W25,1310
W26,1213
```

`examples/gmv_attribution.csv`：

```csv
factor,delta_wan,note
上周基线,1280,
渠道A转化下降,-49,转化率 3.2%→1.1%（落地页改版导致）
渠道B减投,-18,
渠道C增长,8,
其他,-8,
本周,1213,
```

- [ ] **Step 2: 提交**

```bash
git add examples/
git commit -m "test: GMV 端到端验收样例数据"
```

---

### Task 6: 端到端验收运行

**Files:**
- Create: `projects/<验收项目名>/`（ppt-master 项目，gitignore）
- Modify: `.gitignore`（追加 `projects/`）

- [ ] **Step 1: 按使用约定走完整流程（本任务由 AI 助手亲自执行，模拟真实使用）**

执行 Task 4 的交互流程第 1–5 步：读入 `examples/gmv_weekly.csv` + `gmv_attribution.csv` → 问方向（自答：无方向，按方法论自动叙事）→ 写 facts.json → 产出大纲（P01 封面"本周 GMV 环比下跌 5.2%，为近 8 周最大跌幅" / P02 冲突·8 周折线 / P03 放大·大数字 / P04 归因·瀑布 / P05 行动）→ 经用户确认 → 生成 SVG → 质量门 → 导出。

关键命令（`P=<项目路径>`，`SKILL_DIR=/Users/princyzhang/PPT-Maker/ppt-master/skills/ppt-master`，`PY=/Users/princyzhang/PPT-Maker/.venv/bin/python`）：

```bash
$PY $SKILL_DIR/scripts/project_manager.py init gmv_acceptance
$PY $SKILL_DIR/scripts/project_manager.py import-sources projects/gmv_acceptance_* examples/gmv_weekly.csv examples/gmv_attribution.csv
# Stage 1/2: 大纲经用户确认后写入 design_spec.md + spec_lock.md（free-design 但锁定 nerdy-green tokens）
# Executor: 逐页生成 svg_output/P01..P05.svg → 早检门 → 终检门
$PY $SKILL_DIR/scripts/svg_quality_checker.py $P --canonical-authoring --stage final --json
$PY $SKILL_DIR/scripts/svg_to_pptx.py $P --native-charts-and-tables
```

Expected: 终检 0 错误；导出退出码 0，POSTFLIGHT `status: passed`。

- [ ] **Step 2: 原生可编辑性验证**

```bash
unzip -l projects/gmv_acceptance_*/exports/*.pptx | grep -E 'charts/chart|chart\.xml' | head -3
```

Expected: 存在 `ppt/charts/chart*.xml` 条目（原生图表对象，非截图）。文字可编辑性由 PPTX 打开检查确认。

- [ ] **Step 3: 视觉验收**

将 `svg_final/*.svg` 渲染为 PNG，逐页核对验收清单第 2/5/6 项（tokens、一句话标题、Storytelling 规则）；由用户在 PowerPoint 打开最终 PPTX 核对第 3 项。

- [ ] **Step 4: 验收清单核对并记录结果**

对照设计文档 §6 的 7 项清单逐项记录 通过/不通过 + 证据路径，写入
`docs/superpowers/specs/2026-09-06-nerdy-green-data2ppt-acceptance.md`。不通过项回到对应 Task 修复后重跑本 Task。

- [ ] **Step 5: 提交验收记录与 .gitignore**

```bash
echo "projects/" >> .gitignore
git add .gitignore docs/superpowers/specs/2026-09-06-nerdy-green-data2ppt-acceptance.md
git commit -m "test: data2ppt 端到端验收记录"
```

---

## Self-Review 记录

- **Spec 覆盖**：§2 三件套 → Task 1/3/4；§3 流程与红线 → Task 4；§4 tokens/版式 A/图表规则 → Task 3；§5 管线 → Task 4 命令映射 + Task 6 执行；§6 验收 7 项 → Task 6。无缺口。
- **占位符扫描**：无 TBD/TODO；Task 3/4 含完整文件内容；命令均带期望输出。
- **一致性**：`--native-charts-and-tables`、facts.json、显式 workspace root、16:9 `1280×720`、5–6 页默认值在 Task 3/4/6 间一致；`design_spec.md` 路径与 frontmatter 字段对照 narrative-keynote 内置样例核实过。
- **注**：Task 3 Step 1 的 spec 正文是初稿权威版本；实施时如与 ppt-master 校验器要求冲突（如必需字段缺失），以内置样式 schema 为准做最小增补，并在提交信息中注明。

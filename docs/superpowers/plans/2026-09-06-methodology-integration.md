# 数据分析方法论接入 data2ppt 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把用户的数据分析方法论提炼为 `methodology/analysis-methodology.md` 规则库，接入 data2ppt 的分析层与文档链，并用 GMV 虚构样例完成端到端验证。

**Architecture:** 纯文档改动。规则库按时序组织（§A 可信检查→§B 三比→§C 七步骨架→§D 三不→§E 归因页角色→§F 优先矩阵→§G 行动三分类→§H 探查顺序与 6 秒测试）；data2ppt.md 承载流程路由，风格工作区承载页面角色扩展，SKILL.md（本机 + 仓库副本）承载强制加载。

**Tech Stack:** Markdown、git。

**设计文档:** `docs/superpowers/specs/2026-09-06-methodology-integration-design.md`

---

### Task 1: 创建方法论规则库

**Files:**
- Create: `methodology/analysis-methodology.md`

- [ ] **Step 1: 写入规则库全文**

```markdown
# 数据分析方法论规则库（data2ppt 分析层）

> 提炼自用户的数据分析方法论文档（培训大纲 v3.0、数据化运营-数据分析/落地执行）。
> 只含分析时可执行的规则；培训内容原文留在 Obsidian 源文档，不入库。

## §A 数据可信前置检查（异动归因类必跑，其他类型可选）

1. **异动真实性核查**：确认变化是真业务信号而非数据问题——检查采集/ETL/上报
   链路变更；有第二数据源时交叉验证。核查结论写入 facts.json：
   `"quality_check": {"stability": "...", "outliers": "...", "link_check": "..."}`
2. **稳定性阈值（变异系数 CV）**：CV = std/mean。CV<15% 高稳定；15–30% 中等；
   ≥30% 低稳定——低稳定指标的变化**不得写成确定性结论**，大纲阶段标"暂定"。
3. **异常值检测**：正态用 3σ，非正态用 IQR；被剔除/标注的异常值必须在口径注披露。
4. 样本量不足或周期过短 → 结论措辞降级（"初步迹象"），并注明需要的数据。

## §B 三比分析法（自动探查的对比维度框架）

- **自己比**：同比（消季节，需≥2年数据）/ 环比（短期趋势）/ 定基比（长期趋势）
- **标杆比**：业务目标、盈亏平衡点、历史最优
- **市场比**：竞品、行业均值
- 规则：每个对比结论标注属于哪一比；某比不可得时在口径注说明原因（如"无目标
  值/竞品数据"），不得默认只做环比。

## §C 七步成诗法（分析骨架）

界定问题 → 分解问题 → 优先排序 → 关键分析 → 归纳建议 → 工作计划 → 效果检视。
- **分析按七步走，呈现按金字塔**：设计spec §IX 每页可标注对应七步阶段（P0X 行内
  `七步: 界定/分解/...`）。
- 第 3 步"优先排序"产出 §F 矩阵；第 6/7 步映射到行动页的"工作计划"与"后续验证"
  区块。

## §D 三不原则（质量红线）

1. **不用事实解释事实**：页面放结论与关键证据，不复述分析过程。
2. **不用偶然代表必然**：单点波动不下趋势结论；未验证根因必须标"假设/暂定"。
3. **不用角度限制观点**：行动建议必须可执行，不得以视角不同回避给建议。

## §E 归因报告模板 → 页面角色（归因类 deck）

完整版六段（用户要求"给分析师看"时）：异动概述 → **数据核查** → 下钻分析 →
**假设验证**（假设清单+验证方法+结论）→ 归因结论 → 建议行动。
决策者版：仍压缩为 冲突→放大→归因→行动 四段，但数据核查结论必须进入口径注。
页面角色"数据核查""假设验证"的规范见风格工作区 §III。

## §F 优先排序矩阵（行动页排序）

排序 = 提升空间 × 操作难度；提升空间大 + 难度低 = 第一优先。
大纲确认时展示排序表（每项行动两维打分或定性评级）；行动页附一行排序理由。

## §G 行动三分类与落地方式（行动页分组标签）

- 动作方向标签：**拓展类**（新增资源/渠道/量）/ **优化类**（现有动作提效）/
  **剔除类**（停掉无效负向动作）
- 落地方式标签：分类·排序 / 模式·策略 / 机制·预警
- 规则：每个建议带一个方向标签；≥3 条建议时按方向分组呈现。

## §H 探查顺序与 6 秒测试

- 自动探查执行顺序：**先看结构 → 再看漏斗 → 再看画像**。
- 6 秒测试（交付目检新增项）：逐页自问"6 秒内能否答出这页说了什么"；
  答不出 = 回去删，直到通过。
```

- [ ] **Step 2: 结构自检**

```bash
grep -c "^## §" methodology/analysis-methodology.md   # Expected: 8
```

- [ ] **Step 3: Commit**

```bash
git add methodology/ && git commit -m "feat: 数据分析方法论规则库（§A-§H）"
```

---

### Task 2: 接入 data2ppt.md

**Files:**
- Modify: `data2ppt.md`

- [ ] **Step 1: 交互流程第 2 步前插入方法论路由**

在"## 交互流程（严格按序）"的步骤 2 之前插入：

```markdown
2. **方法论路由**：读 `methodology/analysis-methodology.md` 并按类型应用——
   异动归因类先跑 §A 数据可信前置检查（quality_check 写入 facts.json）；
   对比维度按 §B 三比组织（不可得的比要说明原因）；探查顺序按 §H
   （结构→漏斗→画像）；分析骨架按 §C 七步成诗法；行动页按 §F 矩阵排序、
   §G 三分类打标签；全篇遵守 §D 三不原则。
```

原步骤 2-5 顺延为 3-6。

- [ ] **Step 2: 质量红线新增三不原则**

在"## 质量红线"列表追加一行：

```markdown
- 三不原则：不用事实解释事实、不用偶然代表必然、不用角度限制观点（未验证根因标"暂定"）
```

- [ ] **Step 3: 大纲确认项补充**

大纲确认步骤（原步骤 4）追加一句：

```markdown
行动建议按 §F 优先矩阵排序（提升空间×操作难度）并带 §G 拓展/优化/剔除分类标签。
```

- [ ] **Step 4: Commit**

```bash
git add data2ppt.md && git commit -m "docs: data2ppt 接入方法论路由与三不原则"
```

---

### Task 3: 风格工作区新增两个页面角色

**Files:**
- Modify: `templates/nerdy-green-storytelling/templates/design_spec.md`（§III 页面角色词表表格末尾追加两行）

- [ ] **Step 1: 追加角色行**

```markdown
| 数据核查 | 证明"变化是真的"再开始叙事：链路核查、稳定性（CV 阈值）、异常值处理 | facts.json `quality_check` 字段；CV 数值与阈值对照；剔除的异常值披露 | 单张窄卡放在冲突页前或并入口径卡；不稳定信号用 #55816D |
| 假设验证 | 列出归因假设清单及每条的验证方法与结论，支撑"≤3 个原因"的证据链 | 每个假设一行：假设 → 验证方法 → 支持/排除；排除项也要展示 | 表格式卡片；支持项深绿标记，排除项灰显 |
```

- [ ] **Step 2: Commit**

```bash
git add templates/ && git commit -m "feat: 风格工作区新增数据核查/假设验证页面角色"
```

---

### Task 4: SKILL.md 强制加载（本机 + 仓库副本）

**Files:**
- Modify: `/Users/princyzhang/.agents/skills/data2ppt/SKILL.md`
- Modify: `skill/data2ppt-SKILL.md`

- [ ] **Step 1: 强制加载清单插入（两个文件同改）**

在"## 强制加载顺序"第 2 条后插入：

```markdown
3. 读 `<项目根>/methodology/analysis-methodology.md`（分析方法论规则库 §A–§H）。
```

（原 3、4 条顺延为 4、5。）本机版第 2 条之后插入相同内容，路径写作
`/Users/princyzhang/PPT-Maker/methodology/analysis-methodology.md`。

- [ ] **Step 2: Commit + Push**

```bash
git add skill/ && git commit -m "docs: SKILL 强制加载方法论规则库"
```

---

### Task 5: 端到端验证（GMV 虚构样例）

**Files:**
- Modify: `ppt-master/projects/gmv_acceptance_ppt169_20260906/sources/facts.json`（追加 quality_check）
- Modify: `ppt-master/projects/gmv_acceptance_ppt169_20260906/svg_output/05_actions.svg`（行动分类标签）
- Modify: `ppt-master/projects/gmv_acceptance_ppt169_20260906/svg_output/03_magnitude.svg`（三比口径注）

- [ ] **Step 1: facts.json 追加 quality_check（按 §A 规则对 GMV 序列实算）**

```json
"quality_check": {
  "stability": "8 周序列 CV≈2.7%（剔除 W26 后 std/mean），高稳定（CV<15%），W26 下跌可视为真实业务信号",
  "outliers": "3σ 检验：W26=1213 偏离均值 -2.3σ，未超 3σ 但为序列最低；按业务口径保留并标注",
  "link_check": "无第二数据源可交叉验证，已声明口径冲突待对齐"
}
```

（CV 实算值以 pandas 实跑为准，允许 ±0.2pp 误差。）

- [ ] **Step 2: 05_actions.svg 三个行动卡标题行追加分类标签 pill**

行动 1 追加 `优化类`、行动 2 追加 `优化类`、行动 3 追加 `机制·预警`（pill 样式：
`#EAF1ED` 底 `#1F4D3F` 字，右对齐于卡片右上角）；03_magnitude.svg 口径卡追加一行
`三比：仅自己比可得（环比）；标杆比（无目标值）与市场比（无竞品数据）不可得`。

- [ ] **Step 3: 重跑质量门 + 导出 + 渲染目检（目检含 §H 6 秒测试）**

```bash
$PYTHON $SKILL_DIR/scripts/stamp_native_fallbacks.py $P/svg_output --write
$PYTHON $SKILL_DIR/scripts/svg_quality_checker.py $P --canonical-authoring --stage final --json
$PYTHON $SKILL_DIR/scripts/svg_to_pptx.py $P --native-charts-and-tables
```

Expected: 0 错误；POSTFLIGHT passed；交付路径从 `[Done] Saved:` 现取。

- [ ] **Step 4: 验收记录 + Commit + Push**

```bash
git add -A && git commit -m "test: 方法论接入端到端验证（quality_check/三比/行动分类/6秒测试）" && git push
```

---

## Self-Review 记录

- **Spec 覆盖**：§A→Task 1/5；§B→Task 1/2/5；§C→Task 1/2；§D→Task 1/2；§E→Task 1/3；§F→Task 1/2/5；§G→Task 1/2/5；§H→Task 1/2/5。无缺口。
- **占位符扫描**：无 TBD；Task 1 规则库全文、Task 2-4 补丁文本、Task 5 改动点均已写明。
- **一致性**：CV 阈值、七步阶段名、三分类标签在 Task 1/2/5 间一致；quality_check 字段名与 spec §2 §A 一致。

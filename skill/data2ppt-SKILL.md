---
name: data2ppt
description: >-
  把表格数据（Excel/CSV/对话内贴的表格）生成一套 nerdy 绿风格、图表原生可编辑的
  16:9 决策摘要 PPTX。当用户要求做 PPT、生成幻灯片、把数据做成汇报、画数据叙事
  PPT、或提到 data2ppt 时使用。流程：决策框架与方向确认 → 数据探查建 facts.json →
  大纲一次确认 → 自动生成 SVG → 质量门与图表校验 → 原生图表导出。
---

# data2ppt — 表格数据 → nerdy 绿决策摘要 PPT

基于 ppt-master（Generate PPTX 路线）的收窄工作流。本 skill 是路由器与纪律清单；
详细规则在被加载的文件里。

## 硬性路径（每次先验证存在，缺失则停下报告）

```
SKILL_DIR  = <项目根目录>/ppt-master/skills/ppt-master
PYTHON     = <项目根目录>/.venv/bin/python
STYLE_WS   = <项目根目录>/templates/nerdy-green-storytelling
```

## 强制加载顺序

1. 本文件。
2. 读 `<项目根目录>/data2ppt.md`（交互流程与质量红线的完整版）。
3. 读 `<项目根目录>/methodology/analysis-methodology.md`（分析方法论规则库 §A–§H）。
4. 读 `${STYLE_WS}/templates/design_spec.md`（视觉 tokens = §V，流程图样式 = §VIII）。
5. 生成流程图页前，另读 ppt-master 的 `references/native-shape-authoring.md` 与
   `references/executor-chart.md`；纯图表页读 `references/native-data-interface.md`。

## 工作流（两个阻塞确认点，其余自动）

**Phase A — 理解与方向**（⛔ 阻塞点 1）
1. 接收输入：Excel/CSV 用 pandas 读；对话内表格解析成结构化数据；先做数据核查
   （行列合计、口径一致性），冲突如实记录，不抹平。
   数值探查优先用脚本实跑：`.venv/bin/python analyze.py <数据> --metric <列> --time <列>
   [--dims <维度>] [--compare <期1>,<期2>]`，输出 facts 草稿后 AI 复核补全（规则 §A/§B/§H）。
2. 确认决策框架：这次分析服务什么决策、给谁看、要什么行动、对比口径是什么；
   再问用户有没有已想好的论点/论据方向。
   - 有方向 → MECE 金字塔拆解，定向探查支持与反驳证据；
   - 无方向 → 列假设 → 逐个转为聚焦数据问题 → 自动探查（趋势/异常/归因/对比）。

**Phase B — 大纲**（⛔ 阻塞点 2，唯一的内容确认）
3. 写 `<project>/sources/facts.json`：每条事实 `{metric, values, period, scope,
   source, baseline/denominator}`；数据冲突写进 caveats；证据不足的结论标"暂定"。
4. 输出大纲：每页 = 编号、角色（封面/冲突/放大/归因/行动/附录/流程）、≤30 字
   结论式标题、图表类型、数据来源、所用决策透镜。等用户确认或修改。

**Phase C — 自动执行**（确认后到交付不再提问）
5. 初始化与规划工件：
   ```bash
   $PYTHON $SKILL_DIR/scripts/project_manager.py init <name> --format ppt169
   $PYTHON $SKILL_DIR/scripts/project_manager.py scaffold-spec <project>   # 填满所有 [fill]
   $PYTHON $SKILL_DIR/scripts/project_manager.py scaffold-lock <project>
   $PYTHON $SKILL_DIR/scripts/project_manager.py validate <project>       # 必须 OK
   $PYTHON $SKILL_DIR/scripts/text_measure.py calibrate <project> --outline
   ```
   spec_lock 注意：`mode`/`visual_style` 只能填目录枚举或恰为 `custom`；`custom`
   必须带 `mode_behavior` / `visual_style_behavior` 字段。
6. 逐页手写 SVG 到 `<project>/svg_output/`（风格 tokens 一律取自 §V；近白画布
   `#F7F7F4`，全绿无红）。含值驱动图表的页：画
   `chart-plot-area: object=<key> | x_min,y_min,x_max,y_max` 标记；原生图表对象
   （`data-pptx-replace-with="chart"` + 内联 JSON）与可见 fallback 同一编辑单元写完，
   随即打戳：
   ```bash
   $PYTHON $SKILL_DIR/scripts/stamp_native_fallbacks.py <project>/svg_output --write
   ```
   页面有任何可见修改后必须重打。
7. 质量门（页数 ≤6 免早检门，直接终检）：
   ```bash
   $PYTHON $SKILL_DIR/scripts/svg_quality_checker.py <project> --canonical-authoring --stage final --json
   ```
   0 错误才放行；修复走"一次合并修复 pass"，不逐条查。
8. 含图表 → verify-charts：用 `svg_position_calculator.py calc bar|line` 对照
   plot-area 逐点核算，修完重跑终检。已知坑：bar 系列 `point_colors` 不接受
   null（必须全色）；百分比标签用 小数值 + `number_format: "0.0%"`（不支持
   `0.0"%"` 字面量格式）。
9. 导出：
   ```bash
   $PYTHON $SKILL_DIR/scripts/svg_to_pptx.py <project> --native-charts-and-tables
   ```
   **交付路径必须从输出 `[Done] Saved:` 行现取**（每次导出生成新时间戳文件，
   凭记忆报旧路径是已犯过的错误）。读 `[POSTFLIGHT]` 行，status=passed 才算成功。
10. 交付前渲染目检（强制，质量门对此盲区）：
    ```bash
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless \
      --disable-gpu --screenshot=/tmp/d2p_check.png --window-size=1280,720 \
      --hide-scrollbars "file://<svg_output>/<页>.svg"
    ```
    逐页看：文本遮挡（尤其泳道标签与首节点，须 ≥10px 垂直间隙）、边线穿字、
    图例完整。发现遮挡 → 改几何 → 重跑 6-10。
11. 交付报告：PPTX 路径 + POSTFLIGHT 结果 + warnings 披露 + 预览图路径
    （复制 PNG 到 `<project>/preview_png/`）。

## 质量红线（违反即返工）

- 每个数字可追溯 facts.json；禁止编造。对比必须带基线/分母/口径。
- 每页标题 = 该页 ≤30 字结论句；写不出这句话的页/图砍掉。
- 归因 ≤3 个原因；饼图 >3 分类禁用；无网格线/图例(图表内)/双轴/3D。
- 颜色只用绿色系：深绿 #1F4D3F=结构/正向强调，中绿 #55816D=下降/异常，
  浅绿 #A9C3B6=正向，全篇无红色。
- 图表/表格必须原生可编辑（--native-charts-and-tables），禁止截图嵌页。
- 流程图页按 §VIII：虚线泳道带 + 白卡节点（角色=描边色+底色 tint）+ 原生箭头
  直线 + **图例强制**；≤12 节点 ≤4 泳道，优先轴对齐布线。
- 行动页四要素：做什么、证据为何支持、风险依赖、后续验证。
- 单页失败只修该页所属层；上下文丢失用 resume-execute 续跑，不重跑规划。

## 沉淀

每次实际使用后，若发现新的坑或风格修正：更新 data2ppt.md / 风格工作区
design_spec.md（含本文件），git commit 并 push 到 GitHub
（origin = github.com/princyzhang1988/PPT-Maker，保持仓库与本地同步）。

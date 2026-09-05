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
   - `project_manager.py init <name>`（16:9 用 `1280×720` viewBox，spec_lock 记录）
   - `project_manager.py import-sources <project> <数据文件> facts.json`
   - Stage 1 按"明确委托"代决策：传入风格工作区 root
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

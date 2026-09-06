# data2ppt — 表格数据 → nerdy 绿叙事 PPT 使用约定

> 本文件已被封装为可调用技能：`~/.agents/skills/data2ppt/SKILL.md`。
> 对 AI 助手说"做 PPT / 生成决策摘要"即可触发；本文件是规则的完整版。

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
   读入并规范化（列类型、时间粒度、指标识别）；多来源冲突时比较口径/新鲜度/粒度，
   选定权威来源并在 facts.json 声明取舍（OpenAI product-business-analysis 的
   Source Discovery & Verification 规则）。
2. **方法论路由**：读 `methodology/analysis-methodology.md` 并按类型应用——
   异动归因类先跑 §A 数据可信前置检查（quality_check 写入 facts.json）；
   对比维度按 §B 三比组织（不可得的比要说明原因）；探查顺序按 §H
   （结构→漏斗→画像）；分析骨架按 §C 七步成诗法；行动页按 §F 矩阵排序、
   §G 三分类打标签；全篇遵守 §D 三不原则。
3. **问方向（唯一前置提问）**：先确认决策框架——这次分析服务于什么决策、
   谁来用、要什么行动、对比口径是什么；再问有没有已想好的论点/论据方向。
   - 有 → 按论点做 MECE 金字塔拆解，定向探查支持与反驳证据；
   - 无 → 列假设（什么原因可能解释数据），逐个转为聚焦的数据问题后自动探查：
     趋势/异常/归因/对比，取最强信号推导结论。
4. **写 facts.json** 到 `<project>/sources/`：每条事实含
   `{metric, value(s), period, scope, source, baseline/denominator}`，是全流程唯一
   数值真源；缺失关键数据源时停下说明，不用弱替代冒充。
5. **大纲确认（唯一阻塞点）**：按金字塔呈现页清单
   （每页：编号、角色、一句话标题、图表类型、数据来源、所用决策透镜
   ——规模/动量/广度/集中度/效率/可行动性等，选真能改变结论的 1-2 个），
   等用户确认。行动建议按 §F 优先矩阵排序（提升空间×操作难度）并带 §G 拓展/优化/剔除分类标签。
每页标题必须 ≤30 字结论句；写不出这句话的页/图砍掉。
   证据不足的结论在大纲阶段就标注"暂定"，并写明什么证据能提升置信度。
6. **自动执行到交付，中途不再提问**：
   - `project_manager.py init <name> --format ppt169`（16:9=1280×720，目录名必须带格式段，否则 scaffold/validate 拒绝）
   - `project_manager.py import-sources <project> <数据文件> facts.json`
   - Stage 1 按"明确委托"代决策：传入风格工作区 root
     （`explicit_workspace_roots=[<风格工作区>]`），沟通契约 = reader-led 决策摘要
   - Executor 逐页生成 SVG（P01–P05 早检门 → 连续生成 → 终检门 0 错误）
     - 值驱动图表：图内画 `chart-plot-area: object=<key> | x_min,y_min,x_max,y_max` 标记；
       原生图表对象（`data-pptx-replace-with="chart"` + 内联 JSON）与可见 fallback
       同一编辑单元写完，随即 `stamp_native_fallbacks.py <svg_output> --write` 打同步戳；
       页面有任何可见修改后重打
   - 含数据图表 → 强制 `verify-charts`（svg_position_calculator 对照 plot-area；
     瀑布图按分解段落逐段核算）→ 修完重跑终检
   - `svg_to_pptx.py <project> --native-charts-and-tables`
   - 交付 `exports/*.pptx`，报告 POSTFLIGHT 结果与 warnings

## 质量红线

- 每个数字可追溯 facts.json；禁止生成时编造/脑补数值
- 每个对比显式给出基线/分母/口径；证据冲突时呈现冲突而非抹平
- 行动页交付四要素：做什么、证据为何支持、风险与依赖、后续验证什么
- 每页 page job = 它的一句话结论（写进 design_spec §IX）
- 归因 ≤3 个原因；饼图 >3 分类禁用；无网格线/图例/双轴/3D
- 颜色只用绿色系标记关注点（深绿=结构/合计，中绿 #55816D=下降/异常，浅绿 #A9C3B6=正向），全篇无红色
- 图表/表格必须原生可编辑（--native-charts-and-tables），禁止截图嵌页
- 三不原则：不用事实解释事实、不用偶然代表必然、不用角度限制观点（未验证根因标"暂定"）

## 已踩过的坑（实跑沉淀）

- `init` 目录名必须带格式段（--format ppt169），否则 scaffold/validate 拒绝。
- bar 图表 `point_colors` 不接受 null；百分比标签 = 小数值 + `number_format: "0.0%"`。
- 图表可见 fallback 修改后必须重打 `stamp_native_fallbacks --write`。
- 流程图泳道标签与首节点保留 ≥10px 垂直间隙（质量门查不出组内遮挡）。
- 导出每次生成新时间戳文件——交付路径从 `[Done] Saved:` 输出现取。
- 交付前渲染目检强制：文本遮挡、边线穿字、图例完整。

## 失败恢复

- 单页失败：按 ppt-master failure-recovery 修该页所属层，不重跑规划
- 上下文丢失：`继续生成 projects/<project_name>` 走 resume-execute
- 风格/质量争议：对照 templates/nerdy-green-storytelling/templates/design_spec.md

## 沉淀与同步

- 每次实际使用后，若发现新的坑或风格修正：更新本文件 / 风格工作区 design_spec.md /
  SKILL.md，git commit 并 push 到 GitHub（origin = github.com/princyzhang1988/PPT-Maker，
  保持仓库与本地同步）。
- 推送前过一遍隐私检查：真实业务数据不得入库（projects/ 已 ignore；流程图拓扑等
  新增引用文件先脱敏再提交）。

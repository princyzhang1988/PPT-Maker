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

## 交互流程（严格按序：两个阻塞确认点，其余自动）

用户输入 = 数据 + 简单目标描述。流程：**探查（自动）→ 分析方式提案（⛔确认）
→ 执行分析（自动）→ 分析结果+大纲（⛔确认）→ 制作到交付（自动）**。

1. **接收输入与数据探查**（自动，不先提问）：Excel/CSV 文件、对话内贴的表格、
   或表格+背景描述。用 pandas 读入并规范化（列类型、时间粒度、指标识别），
   直接跑探查（多来源冲突时比较口径/新鲜度/粒度，选定权威来源并在 facts.json
   声明取舍）：
   ```bash
   .venv/bin/python analyze.py <data.csv> --metric <指标列> --time <时间列> \
       [--dims <维度列,...>] [--compare <期1>,<期2>] [--funnel <阶段列1>,...] \
       [--quadrant <X列>,<Y列>] [--rfm <用户列>,<日期列>,<金额列>] \
       [--retention <用户列>,<日期列>[,<分组列>]] [--out <project>/sources/facts_draft.json]
   ```
   产出 facts 草稿：§H.0 数据清洗（单位归一化、缺失/脏值/重复/同指标多单位冲突
   披露——冲突必须先统一口径再聚合）、§A 可信检查（quality_check）、
   §H 结构→漏斗→画像（漏斗相邻阶段量纲不一致时脚本拒绝算转化率）、§B 三比、趋势。
2. **【阻塞确认点 1】分析方式提案**：汇总探查发现（数据形状、目标理解、
   可信结论），按 methodology §I 六法菜单提出分析方式提案，每项声明：
   方法（对比/分组/漏斗/象限/留存/RFM）→ 回答什么业务问题 → 数据要求是否
   满足 → 预期产出与呈现形式；对比类按 §B 标注属于哪一比。目标描述太模糊时，
   决策框架补全问题（服务什么决策/给谁看/要什么行动/对比口径）在本确认点
   一次问清。用户确认或增删分析方式后才进入下一步。
3. **执行分析**（自动）：对确认的方式逐项脚本实跑；有既定论点方向则按 MECE
   金字塔定向探查支持与反驳证据，无方向则列假设逐个转为聚焦数据问题探查，
   取最强信号推导结论。AI 复核补充业务口径与 caveats 后写入 facts.json
   （唯一数值真源；缺失关键数据源时停下说明，不用弱替代冒充）。
4. **【阻塞确认点 2】分析结果 + 呈现大纲**：提交两部分等确认——
   a) 分析结果：每条结论带证据与口径，反证呈现不抹平；证据不足的结论标
      “暂定”并写明什么证据能提升置信度；
   b) 页面级大纲（按金字塔呈现）：每页 编号、角色、一句话标题（≤30 字
      结论句，写不出这句话的页/图砍掉）、图表类型、数据来源、所用决策透镜
      （规模/动量/广度/集中度/效率/可行动性，选真能改变结论的 1-2 个）；
      行动建议按 §F 优先矩阵排序（提升空间×操作难度）并带 §G 三分类标签。
   确认后到交付不再提问。
5. **制作图表与 PPT**（自动）：
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

## 已有 PPT 的更新路由（二次修改场景）

生成过的 deck 需要修改时，先判断变更类型，走对应路线；**facts.json 永远是唯一
数值真源，改页面不改 facts 是禁止操作**。

| 变更类型 | 路线 |
|---|---|
| **文字/措辞微调**（标题措辞、标签、来源注） | 直接改对应 `svg_output/<页>.svg` → 重过质量门（图表页动了 fallback 需重打戳）→ 重导出 → 渲染目检。分钟级，不重跑分析。 |
| **配色/版式微调**（某页布局、颜色、字号） | 同上；若涉及风格 tokens 级改动（如换主色），先更新风格工作区 spec 再全局 sed，防止页面间漂移。 |
| **数据变更**（新一周数据、数字修正） | 先更新 `sources/` 数据文件 → `analyze.py` 重跑 → 更新 facts.json（重过 §A 可信检查）→ 逐页核对标题结论是否仍成立：结论变了的页重画，结论没变的页只更新数字 → 质量门 → 导出。交付时报告"哪些页因数据变了结论/数字"。 |
| **页数/结构变化**（加页、删页、换叙事顺序） | 回到阻塞确认点 2（分析结果+呈现大纲），重新确认后执行；不跳过确认直接改页。 |
| **换画布/换风格** | 等同重新生成：新 init 项目，走完整流程。 |

通用规则：
- 导出永远生成新时间戳文件，旧文件保留供对比；交付时报告最新路径与新旧差异。
- 二次修改同样走质量门与渲染目检，"只是改个字"不豁免。

## 已踩过的坑（实跑沉淀）

- `init` 目录名必须带格式段（--format ppt169），否则 scaffold/validate 拒绝。
- bar 图表 `point_colors` 不接受 null；百分比标签 = 小数值 + `number_format: "0.0%"`。
- 图表可见 fallback 修改后必须重打 `stamp_native_fallbacks --write`。
- 数值列单位嵌在列名里（`gmv_wan`/`delta_wan`）是常态——analyze.py 会自动识别并归一化，
  但 **facts.json 里必须保留原始单位标注**，deck 口径注随原始单位呈现，不得混用。
- 漏斗阶段必须同量纲（人数对人数、金额对金额）；脚本对量纲不一致的相邻阶段拒绝
  计算转化率，deck 遇到这种 note 时先统一口径再上漏斗图。
- 流程图泳道标签与首节点保留 ≥10px 垂直间隙（质量门查不出组内遮挡）。
- 导出每次生成新时间戳文件——交付路径从 `[Done] Saved:` 输出现取。
- 交付前渲染目检强制：文本遮挡、边线穿字、图例完整。
- push 到 GitHub 直连不通（443 超时），需先走本地代理：
  `export https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897 all_proxy=socks5://127.0.0.1:7897`。

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

# 端到端实测报告：数据分析六大方法论 × data2ppt 全流程

日期：2026-09-13
实测对象：data2ppt 工作流（含当日刚接入的 §I.0 问题类型路由、八法菜单、--sigtest/--causal/RFM/留存/象限能力）
数据集：UCI Online Retail II（英国在线零售真实交易，1,067,371 行，2009-12-01 ~ 2011-12-09，公开数据集）
交付物：`ppt-master/projects/online_retail_e2e_ppt169_20260913/exports/online_retail_e2e_20260913_105135_native_charts_tables.pptx`（6 页，原生图表/表格，POSTFLIGHT passed）

## 1. 实测结论（TL;DR）

全流程跑通：**探查（7 项脚本实跑）→ 分析方式提案（§I.0 路由）→ 执行分析（facts.json）→ 结果+大纲确认 → 6 页 PPT 制作（质量门 6/6、POSTFLIGHT passed、judge 逐页验收通过）**。

实测直接揪出并修复了 analyze.py 的一个**真 bug**（贡献度分解对「单期缺席维度」产生 NaN delta 被 sum 静默跳过，总额扭曲 -99,755 vs 真值 -97,373），已修复并新增回归测试（tests/test_inference.py 9/9 通过）。

新机制全部按设计工作：推断检验的措辞纪律（p≥0.05 不说「无差异」）、因果命题自动降级（无对照组 → 探索性归因 + 暂定）、留存口径不适用时的诚实披露、不完整期截断。

## 2. 数据集选择

| 项 | 值 |
|---|---|
| 来源 | UCI Machine Learning Repository — Online Retail II（public/502） |
| 规模 | 1,067,371 行交易明细；5,942 名有账号客户；43 国 |
| 字段 | Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country |
| 选择理由 | 同时覆盖新八法的尽可能多分支：时间序列（趋势/同比）、维度（分组/贡献度）、用户级订单（RFM/留存）、重尾金额（sigtest 检验力）；无对照组——正好检验 §I.0 因果降级规则 |
| 清洗点（真实数据的典型脏） | Customer ID 缺失 22.8%；负收入（退货）19,498 行；零价格 6,202 行；2011-12 仅 9 天（不完整期） |

## 3. 流程实录

### 3.1 模拟用户输入（简单目标）

> 「这是英国电商两年的订单明细，帮我做一份经营复盘：收入表现怎么样、哪里出了问题、客户怎么运营。」

### 3.2 Phase A：数据探查（自动，不提问）

派生 `revenue = Quantity × Price`、`month` 后，analyze.py 七项实跑（命令与产物落 `sources/explore_*.json`）：

| # | 命令形态 | 关键结果 |
|---|---|---|
| 1 | `--metric revenue --time month`（月度趋势+三比） | CV=35.5%（低稳定→结论用同比口径）；2011-12 -70.3% 为不完整期伪信号 |
| 2 | 订单级 AOV 表（5.4 万单） | 供 sigtest |
| 3 | `--sigtest revenue --time month --compare 2010-04,2011-04` | Welch p=0.45（不可区分）、MWU p=0.0013、d=0.025（可忽略）→ 客单价无法解释下滑 |
| 4 | `--dims Country --compare 2010-04,2011-04`（贡献度） | UK 56.4% / EIRE 16.2% / 瑞典 15.6% / 德国 11.8%（修复后数字） |
| 5 | `--rfm Customer ID,InvoiceDate,revenue` | 重要价值 31.0% 客户 / 77.6% 营收；流失风险 30.3% / 2.7% |
| 6 | `--retention Customer ID,InvoiceDate` | D1/D7/D30 = 1.5%/2.5%/0.9% → 精确日购买留存对 B2B 无业务含义（如实披露，不采用） |
| 7 | `--causal revenue,month`（无分组） | 返回降级指引：「无对照组且无干预点 → 探索性归因（§I.0 规则 1）」✓ 降级规则实弹验证 |

补算：同比表（2011-01~11）、H1 聚合（-4.2%）、4 月客户/订单/AOV 拆解、695 名流失老客户（上年同月贡献 £301.6k）。

### 3.3 确认点 1：分析方式提案（§I.0 路由）

实测以用户委托代确认（正常流程此处阻塞等待）。提案材料：

| # | 问题类型 | 分析方式 | 数据 | 产出 |
|---|---|---|---|---|
| 1 | 描述性+探索性 | 月度收入趋势 + 同比（§B 自己比） | ✓ 25 个月 | 趋势折线 + 同比表 |
| 2 | 因果候选→**降级**（§I.0 规则 1） | 贡献度分解（探索性归因）标暂定 | 无对照组/干预点 | 国家贡献 + 口径注 |
| 3 | 推断性 | 显著性检验（§I-7）：4 月客单价差异 | ✓ n=1,892/1,744 | Welch t + MWU + Cohen's d |
| 4 | 描述性 | RFM 客户分层（§I-6） | ✓ 5,942 客户 | 八群表 + 营收占比 |
| 5 | 探索性 | 购买留存（§I-5） | ✓ 但口径不适用 | 如实披露并弃用 |
| — | 预测性（如"明年 11 月多少"） | **能力边界，不提案** | — | — |

### 3.4 确认点 2：分析结果 + 呈现大纲

facts.json 单一真源（`sources/facts.json`），六页大纲（每页结论句 ≤30 字）：

| 页 | 角色 | 标题（结论句） |
|---|---|---|
| P01 | 封面 | 1-4月连跌已修复，31%核心客户贡献78%营收 |
| P02 | 冲突 | 1-4月同比连跌四月，4月最深-16.5% |
| P03 | 放大 | 4月缺口£97.4千：客单价无恙，695名老客户未复购 |
| P04 | 归因 | 英国市场占跌幅 56.4%，四国即全部缺口（暂定·探索性归因） |
| P05 | 行动 | 守住31%核心客户，分层激活30%沉睡客户 |
| P06 | 附录 | 附录：RFM全表与口径说明 |

### 3.5 Phase C：制作

`project_manager init --format ppt169` → import-sources → scaffold-spec/lock（填满 [fill]，§IX 补 Relationships 行）→ validate OK → text_measure calibrate → 逐页手写 6 页 SVG（生成器脚本坐标全由 facts 计算）→ `stamp_native_fallbacks --write` → 质量门终检（**6/6 Fully passed, 0 warnings, 0 errors**，修复轨迹：表格 JSON 行间逗号、companion note 投影、text_color 主导色对齐、表头 align、表格 payload 完整化 bold/align/borders/row_heights）→ `verify-charts`（svg_position_calculator 逐点核算：折线 23 点与横条 4+5 条宽度全部一致）→ `svg_to_pptx --native-charts-and-tables`（**POSTFLIGHT passed, warning_categories=0**）→ headless Chrome 渲染 6 页 → judge 逐页验收。

### 3.6 Judge 验收两轮

- 第一轮：P01/P02/P05 pass；**P03/P04 fail**（缺口金额两处矛盾 £97.4k vs £99.8k——judge 抓出 truth=£97.4k）；**P06 fail**（表头带遮挡首行）。
- 修复过程中定位到金额矛盾的根因是 **analyze.py 真 bug**（见 §4），数字修正为修复后的口径。
- 第二轮：P03/P04/P06 全部 pass（P06 表体下移后首行完整、7 行对齐；P04 四条与 100% 自洽）。

## 4. 实测战果：发现并修复 analyze.py 真 bug

**缺陷**：`contribution_block` 中 `wide[p1] - wide[p0]` 对「只在单期出现的维度」产生 NaN delta，被 `sum()` 静默跳过——总额从真值 **-£97,373** 扭曲为 **-£99,755**（丹麦 2011 缺席 -£748、UAE 2010 缺席 +£16.5 等被丢弃，叠加分母失真使各国占比整体偏移）。

**修复**：主路径与 Bootstrap 重采样路径均 `fillna(0)`（单期缺席按 0 计，含口径注披露）；新增回归测试 `test_contribution_one_sided_dim`（构造单期维度，断言 total=直接两期差）。**该 bug 由真实数据的「新市场只在单期出现」触发，虚构验收样例从未覆盖此形态——E2E 实测的价值直接兑现。**

## 5. 工件清单（过程材料）

| 材料 | 路径 |
|---|---|
| 交付 PPTX | `ppt-master/projects/online_retail_e2e_ppt169_20260913/exports/online_retail_e2e_20260913_105135_native_charts_tables.pptx` |
| facts.json（唯一数值真源） | `…/sources/facts.json` |
| 七项探查原始输出 | `…/sources/explore_{trend,sigtest,contribution,rfm,retention,causal_downgrade}.json` |
| 月度收入表 | `…/sources/monthly_revenue.csv` |
| 六页 SVG 源 | `…/svg_output/01_cover.svg … 06_appendix_table.svg` |
| 渲染目检 PNG | `…/preview_png/*.png`（6 张） |
| 质量门报告 | `…/validation/svg_quality_report.json`、`…/validation/*_native_charts_tables.report.json` |
| 原始数据集 | /tmp/e2e_test/online_retail_II.xlsx（UCI 公开，不入库） |
| bug 修复 | analyze.py contribution_block + tests/test_inference.py（9/9 通过） |

## 6. 遗留与建议

1. P03 结论行单位「£97.4千」与页面他处「k」不统一（judge 提示，无碍验收）。
2. 留存分析对低频购买场景的口径适配（月度 cohort 复购率）可作为 analyze.py 下一步增强。
3. 贡献度行级 Bootstrap 在重尾分布下 CI 偏宽——可考虑按订单聚合后再重采样（下轮评估）。


## 7. 复购质疑后的重做分析（v2，2026-09-13）

用户质疑「主因 695 名老客户未复购」是否对比了复购情况——补做三个验证证实该结论超证（37% 错峰、缺席基线 60.8%→66.1%、分解漏无账号段未闭合），随后按用户确认的四个口径重做分析并重建 deck：

1. **1-4 月窗口闭合分解**（-£279,016，闭合校验 ✓）：留存客户 1,100 家 -£387.6k（最大净拖累，户均 -£352）、流失 1,127 家 -£576.2k、新客 1,072 家 +£663.4k（超额对冲）、无账号 +£21.3k。
2. **90 天滚动口径**（快照 2011-12-09）：活跃 2,927 / 流失 3,015；4 月末 90 天活跃 2,006→1,935（-3.5%）；H1「流失」1,127 家中 303 家快照仍活跃、824 家流失；召回优先 564 家（2010 收入 ≥£1k，Top5 合计 £205.1k）。
3. **无账号客户拆解**：H1 +£21,335；订单 -32.4% 而收入升——单均金额大幅上升的大额批发单；占 2011 收入 13.9%，UK 绝对主体。
4. **假设验证表**（deck 新增 P04，§E 假设验证页角色）：流失=部分排除；4 月深跌=大部分排除（日历）；客单价=排除；国家集中=暂定。

deck v2 交付：`exports/online_retail_e2e_20260913_152542_native_charts_tables.pptx`（P03 闭合分解瀑布、P04 假设验证表、P05 召回优先证据、P06 七条口径卡；质量门 6/6、POSTFLIGHT passed、judge 两轮后 6/6 pass）。

**流程沉淀**：本轮验证了新的两步制交互（第 1 步分析过程对齐 → 第 2 步对外报告）——用户对「未复购=主因」的质疑在第 1 步被消化，避免了一次带病交付。


## 8. 第二套数据源实测：Olist GMV 异动归因（互联网用户增长场景，2026-09-13）

按用户要求更换数据源再测一轮：**Olist Brazilian E-Commerce**（巴西电商，99,441 订单 / 96,096 用户，2016-09~2018-10，Kaggle olistbr / GitHub 镜像 ductransponster）——互联网用户增长场景的 GMV 异动归因。

### 流程（两步制首次完整执行）

- **第 1 步交付（分析过程）**：探查（4 个不完整/伪月剔除、CV=46.7%、复购率 3.4%、新客 GMV 占比 96.8~100%）→ §I.0 路由（异动归因→§A 前置；无对照组降级；RFM 明示不适用——复购 3.4% 使分层失去意义）→ 假设验证六条。用户对齐四口径：叙事 C 并列、GMV 披露口径、截单暂定、暂定带标记。
- **第 2 步交付（deck）**：`ppt-master/projects/olist_gmv_anomaly_ppt169_20260913/exports/olist_gmv_anomaly_20260913_205313_native_charts_tables.pptx`（质量门 6/6、POSTFLIGHT passed、judge 6/6 pass——含一条溯源建议已补：+15~30% 派生口径钉入 facts.json）。

### 结论（结论先行 + 论据）

1. GMV 引擎 = 新客获取：r(GMV, 新客数)=0.9945，新客 GMV 占比 96.8~100%，复购用户仅 3.4%。
2. 异动 A（2017-12 -26.5%）：黑五透支-回归，非业务恶化（vs 10 月轨道 +12.7%/+22.8%；量跌价稳 p=0.302；下半月腰斩→圣诞截单暂定；履约改善）。大部分排除「恶化」。
3. 异动 B（2018 平台期）：新客获取失速（7,025→6,271，GMV 同步平台化）；留存无法接力；渠道层根因止步（无渠道字段——能力边界）。

### 新增验证点

两步制首次完整运行：第 1 步消化了口径对齐（含「RFM 不适用」的诚实排除），第 2 步 deck 结论全部不超过已对齐证据强度。数据集差异测试（零售 vs 平台电商/用户增长）均通过，工作流具备可复用性。

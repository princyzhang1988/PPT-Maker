# 设计文档：nerdy 绿数据叙事 PPT 生成流水线（data2ppt）

日期：2026-09-06
状态：已获用户批准的设计，待实施规划

## 1. 目标

构建一个**可复用的生成流水线**：用户给出表格数据（Excel/CSV 文件、对话里贴的表格、表格+背景描述、或纯数据），系统按照"nerdy 绿"美学风格（提炼自 `nerdy绿_小红书图片/` 的 11 张参考图）与《Storytelling with Data》方法论（`分析结果的呈现与叙事 - Storytelling with Data.md`），生成 **16:9 横版、原生可编辑的 .pptx**。

**实现路线（已选定）**：基于 [ppt-master](https://github.com/hugohe3/ppt-master)（MIT）定制。不另造管线，所有定制以"数据/文档"形式存在，ppt-master 本体保持原样、可随时升级。

已否决的替代路线：
- 抽取编译器自建轻量 skill（流程更轻但需维护抽取代码、脱离上游生态）
- 完全自研 python-pptx 直出（AI 直接产 DrawingML/python-pptx 布局不可靠，是 ppt-master 设计文档明确否决的路线）

## 2. 总体架构（三件套）

```
/Users/princyzhang/PPT-Maker/
├── ppt-master/              ① 完整克隆的 ppt-master 仓库
│   └── skills/ppt-master/     （能力本体：SVG→PPTX 编译器/质量门/模板系统）
├── templates/nerdy-green-storytelling/   ② 风格工作区（本轮核心创作）
│   └── templates/design_spec.style.nerdy-green-storytelling.md
└── data2ppt.md              ③ 薄封装：数据→PPT 使用约定（后续可升级为正式 skill）
```

### ① ppt-master 本体
- 克隆完整仓库到项目目录；`pip install -r requirements.txt` 安装依赖。
- 复用其现成能力：Generate PPTX 路线、SVG 质量检查器（早检门/终检门）、`verify-charts` 图表坐标校验、`svg_to_pptx.py --native-charts-and-tables` 原生图表/表格导出、failure-recovery 恢复机制。

### ② 风格工作区 nerdy-green-storytelling
按 ppt-master 的 Create Template（Style 类）规范制作，同时承载两层内容（Style 类模板的职责即"沟通方法 + 视觉默认值"）：
- **视觉层**：从参考图提炼的设计 tokens（见 §4）
- **叙事层**：Storytelling 方法论规则化（见 §3.3、§4 图表规则）

验证方式：`project_manager.py validate`。

### ③ data2ppt 使用约定
一份薄文档，约定输入形态、交互节奏（哪些阶段自动代决策、哪个点阻塞确认）、质量红线。不是新代码，是把 ppt-master 流程按本场景收窄的说明书。

## 3. 数据 → 叙事大纲流程（金字塔原理版）

### 3.1 交互流程

```
1. 用户给出：表格数据（xlsx/csv/直接贴）+ 可选背景描述
2. 先问一句：有没有已想好的论点/论据方向？
3a. 有方向 → 按论点做针对性数据探查与制表（MECE 拆解论据分支，
    定向计算支持/反驳它的事实；支持与反驳都呈现）
3b. 无方向 → 自动探查：趋势/异常/归因/对比
4. 产出 facts.json（每条事实带数据出处，杜绝编造）
5. 大纲确认 ←—— 唯一的阻塞确认点（金字塔结构呈现）
6. 自动跑完：SVG 生成 → 质量门 → 导出 PPTX
7. 交付 exports/<项目名>_<时间戳>.pptx
```

### 3.2 自动分析维度（无方向时）
- **趋势**：时间序列环比/同比、最近周期变化幅度（如"下跌 5.2%"）
- **异常**：均值/趋势线的显著偏离点
- **归因**：可分解指标的贡献度排序（≤3 个原因）
- **对比**：分类维度 Top/Bottom 排名

### 3.3 金字塔原理拆解 + 一句话规则（硬规则）
- 大纲按金字塔呈现：一层结论、二层论据页、三层证据图表
- **每一页、每一个图表都必须能被一句话说明**——页面标题即这句话（≤30 字结论式标题）；写不出这句话的页/图直接砍掉
- 该规则写进风格工作区，对应 ppt-master §IX 页面的 page job

### 3.4 与 ppt-master 流程的对接
- 走 Generate PPTX 路线 + 安装的 nerdy-green-storytelling 风格工作区
- Stage 1（沟通契约）按"明确委托"自动代决策，默认 reader-led 决策摘要
- 风格已由工作区锁定，Stage 2 收敛为单次大纲确认（§3.1 第 5 步）

### 3.5 页面骨架（四段叙事）
冲突 → 放大 → 归因 → 行动。页数默认 5–8 页（封面/冲突/放大/归因/行动 + 可选附录数据表），大纲确认时可调。

## 4. nerdy 绿视觉系统

### 4.1 设计 tokens

| Token | 取值 |
|---|---|
| 画布底色 | 浅暖灰 `#EFEFED` |
| 卡片 | 白底、圆角 8px、极浅投影、1px 浅边框 |
| 主色 | 墨绿 `#1F4D3F`（标题/强调） |
| 辅助色 | 灰绿 `#7FA99B`（次要线、虚线框）、浅绿填充 `#EAF1ED` |
| 警示色 | 砖红 `#C0392B`（仅用于异常/下跌标记） |
| 数字 | 等宽字体、大字号、负字距 |
| 页眉 | `P0X · 页面角色` + 右侧 `@DATA2PPT 00X` 编号 |
| 标注 | 墨绿虚线框 + 小标签（证据/结论框） |

### 4.2 版式骨架（已选定：A · 卡片矩阵）
一页多张白卡分工（主图卡 + 事实卡 + 证据卡），密集信息、Dashboard 式，适合决策摘要。已通过浏览器 mockup 对比 A（卡片矩阵）/ B（单卡聚焦）/ C（墨绿侧栏）后由用户选定。mockup 存于 `.superpowers/brainstorm/` 会话目录（visual-style.html）。

### 4.3 图表规则（Storytelling 落地）
- 图表生成方式：AI 生成 SVG → ppt-master 编译为**原生可编辑图表/表格**（`--native-charts-and-tables`）
- 灰色打底 + 关注段墨绿/砖红加粗；无网格线；数值直接标注在图上（不用图例）
- 图型速查：单数字→大字页；3-5 分类对比→横向柱状图（降序）；时间趋势→折线；归因→瀑布图；构成→堆叠柱状（饼图 >3 分类禁用）
- 删除清单：网格线、多余边框、装饰 3D/阴影/渐变一律不用

## 5. 端到端生成管线（ppt-master 机制，自动执行）

| 环节 | 机制 |
|---|---|
| 项目初始化 | `project_manager.py init` + 分析结果写入 `sources/`（facts.json + 规范化数据表） |
| Stage 1 | 明确委托代决策，安装风格工作区 |
| SVG 生成 | Executor 按风格 spec 逐页手写 SVG；P01–P05 早检门校准方法，之后连续画完 |
| 图表校验 | 数据图表页强制走 `verify-charts`：SVG 几何坐标逐点核对 facts.json |
| 终检门 | `svg_quality_checker --stage final` 0 错误放行 |
| 导出 | `svg_to_pptx.py --native-charts-and-tables` |

### 质量红线
- 每个数字必须能追溯到 facts.json，禁止编造/脑补数值
- 每页 page job = 它的一句话结论
- 归因页 ≤3 个原因；饼图禁用 >3 分类
- 失败恢复走 ppt-master failure-recovery：单页失败只修该页；上下文丢失可 resume-execute 续跑

## 6. 验收标准

端到端验收样例：使用《Storytelling with Data》文档内现成的 8 周 GMV 序列（1310→1213）+ 归因分解（渠道A -49 / 渠道B -18 / 渠道C +8 …）跑一次真实生成。

| # | 验收项 | 标准 |
|---|---|---|
| 1 | 交互节奏 | 只被问一次方向 + 一次大纲确认，之后无人打扰直到交付 |
| 2 | 视觉风格 | 渲染页面与 mockup A 的 tokens 一致 |
| 3 | 原生可编辑 | PowerPoint 中图表为可编辑对象（可改数据/颜色），文字全部可选中 |
| 4 | 数字正确 | 图表数值与 facts.json 一致（verify-charts 通过） |
| 5 | 一句话规则 | 每页标题即该页结论；瀑布图归因 ≤3 项 |
| 6 | Storytelling 落地 | 无网格线、灰色打底 + 关注段高亮、数值直接标注 |
| 7 | 可复用性 | 换一份新表格数据可走通同一流程 |

风格工作区验证：`project_manager.py validate`。

## 7. 范围外（YAGNI）
- 不做竖版小红书卡片画布（如未来需要，风格工作区可扩展第二画布）
- 不做多风格并存/风格选择器（只有一套 nerdy-green-storytelling）
- 不做 matplotlib 嵌图路线（已选定全原生 SVG 路线）
- data2ppt.md 暂不升级为独立 skill，待流程跑顺后再固化

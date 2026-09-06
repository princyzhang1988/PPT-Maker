# 验收记录：data2ppt 端到端验收（GMV 样例）

日期：2026-09-06
对应设计：`docs/superpowers/specs/2026-09-06-nerdy-green-data2ppt-design.md` §6
对应计划：`docs/superpowers/plans/2026-09-06-nerdy-green-data2ppt.md` Task 6

## 运行环境产物

- 项目：`ppt-master/projects/gmv_acceptance_ppt169_20260906/`
- 数据真源：`sources/facts.json`（含口径注：weekly CSV 与归因 CSV 的"上周"基线不一致，环比结论以归因 CSV 为准——源数据即如此，已在 facts.json caveats 声明）
- 终检报告：`validation/svg_quality_report.json`（final，0 错误 0 警告）
- 导出：`exports/gmv_acceptance_20260906_081800_native_charts_tables.pptx`
- 导出审计：`validation/gmv_acceptance_20260906_081800_native_charts_tables.report.json`
  `[POSTFLIGHT] status=passed quality_gate=passed slides=5 warning_categories=0`

## verify-charts 回执

```
verify-charts: 02_conflict_trend.svg | object=gmv-trend | type=line | mode=direct-calc | scale=1180-1360 (declared, no ticks) | calc=ran | svg=updated（折线坐标按计算器输出校正 ≤0.4px）
verify-charts: 04_attribution_waterfall.svg | object=gmv-attribution | type=waterfall | mode=decomposable-calc | scale=1180-1320 (declared, no ticks) | calc=ran | svg=updated（修正作图时绘图区高度 330→320px 的系统性偏差，条形槽位对齐计算器）
```

## 验收清单

| # | 验收项 | 结果 | 证据 |
|---|---|---|---|
| 1 | 交互节奏 | ✅（带注） | 流程仅两个交互点：问方向、大纲确认。本次为用户外出授权的无人值守验收，两点均按约定代答（方向=无/自动叙事；大纲=金字塔 5 页）。正常使用时这两点仍阻塞等用户 |
| 2 | 视觉风格 | ✅ | 5 页 PNG 渲染（qlmanage）与 mockup A tokens 一致：#EFEFED 画布、白卡圆角+描边、墨绿 #1F4D3F、砖红 #C0392B 仅用于异常/负向、等宽数字、灰绿虚线标注框、`@DATA2PPT 00X` 页眉 |
| 3 | 原生可编辑 | ✅ | PPTX 内 `ppt/charts/chart201.xml`（c:lineChart，8 周 8 值）+ `ppt/charts/chartEx401.xml`（cx:chartSpace 瀑布图，1280/-49/-18/8/-8/1213），各带 `ppt/embeddings/Microsoft_Excel_Sheet*.xlsx` 内嵌工作簿——图表数据在 PowerPoint 中可直接编辑；全部文字为 DrawingML 文本框 |
| 4 | 数字正确 | ✅ | 全部数值可追溯 facts.json；图表坐标经 svg_position_calculator 校验（ waterfall 修正了 7.4px 系统性缩放偏差——验证门真实发挥作用） |
| 5 | 一句话规则 | ✅ | 5 页标题均为 ≤30 字结论句（21/17/17/18/19 字）；瀑布归因 2 个负向原因 + 1 个正向反证，≤3 |
| 6 | Storytelling 落地 | ✅ | 无网格线、无图例、数值直接标注在图上、灰线打底 + 关注点着色、非零基线已在图上显式声明（"纵轴自 1180 万起"） |
| 7 | 可复用性 | ✅（带注） | 同一流程由 `data2ppt.md` 约定驱动；换一份新 CSV 重跑同命令序列即可。完整的多数据形态实测留待日常使用累积 |

## 实跑中学到并回写 data2ppt.md 的操作要点

1. `project_manager.py init` 目录名必须带注册格式段：`init <name> --format ppt169`，否则 scaffold/validate 报"Cannot derive the canvas format"。
2. spec_lock 的 `mode` / `visual_style` 为枚举或恰为 `custom`；`custom` 时必须提供 `mode_behavior` / `visual_style_behavior` 字段。
3. 原生图表的 plot-area 标记（`chart-plot-area: object=<key> | …`）是 verify-charts 硬性输入；`stamp_native_fallbacks.py --write` 必须在每次可见修改后重跑。

## 遗留观察（不阻塞验收）

- qlmanage 渲染为预览用途；最终视觉以 PowerPoint 打开导出 PPTX 为准（图表颜色/字体在 PowerPoint 中的呈现建议用户回来后人工复核一次）。
- `visual_style: custom` 未挂接 ppt-master 目录引用文件，风格语义完全由风格工作区 design_spec.md 承载——符合设计（显式 workspace root 路线）。

---

## Revision Round 2（用户反馈：2026-09-06）

用户三条反馈及处置：

1. **封面白卡与背景突兀** → 回看参考图（img_02 等）确认：nerdy 模板的画布是**近白色**，卡片用细描边+浅灰内嵌面板做"轻边界"，不是白卡浮在灰底上。处置：画布 #EFEFED → 近白 #F7F7F4；封面改为**全宽标题卡**（参考模板页眉卡做法）+ 底部"本篇结构"四段导览条（浅灰 #F2F2EF 内嵌面板）；风格 spec §V 同步改写（卡片去阴影、新增 inset panel token、全宽构图优先规则）。
2. **红色替换为绿色** → 全篇去红，绿色单色系：深绿 #1F4D3F（结构/合计）、中绿 #55816D（下降/异常标记）、浅绿 #A9C3B6（正向）、方向由明度+正负号承载。5 页 SVG、原生图表 payload（chart201 point_colors/data_labels、chartEx colors401 color-style part）全部换色；终检 0 错误。
3. **融入 openai/role-specific-plugins 的 product-business-analysis 方法** → data2ppt.md 与风格 spec §II 新增：决策框架先行（决策/受众/行动/对比口径）、来源发现与冲突裁决、假设→聚焦数据问题、facts.json 增加基线/分母、大纲页标注决策透镜、行动页四要素（做什么/证据/风险/后续验证）、暂定结论显式标注。

Revision 后产物：`exports/gmv_acceptance_20260906_084101_native_charts_tables.pptx`
（`[POSTFLIGHT] status=passed quality_gate=passed slides=5 warning_categories=0`；终检 5 页 0 错误 0 警告；图表几何未变，颜色系更新已验证进入原生 chart part。）

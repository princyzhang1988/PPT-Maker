# charts/ — 独立快速图表

对话中临时出图的 track：matplotlib 脚本生成 nerdy green 风格、透明背景 PNG，
直接贴进 IM / 文档 / 邮件。与 deck 管线（ppt-master 原生可编辑图表）并行，
**不**产出 PPTX——要进 deck 的图必须走 data2ppt 流程重画为原生图表。

## 与 deck 质量红线的关系

- 共享 design_spec §V 视觉 tokens（`chart_style.py`）：全绿无红、无网格线、
  数值直接标注、结论式标题、mono 数字。
- 本 track **允许双轴**（两个指标量级差异大时，轴色与线色对应即可）；
  deck 内双轴仍是红线。其余红线（饼图 >3 分类禁用、归因 ≤3 原因等）两边一致。

## 用法

新图从 `example_dual_axis_line.py` 复制起步：只写数据、标题和少量布局参数，
tokens / rcParams / 标题区 / 脚注 / 轴线 / 折线+末点强调 / 逐点标数全部来自
`chart_style.py`。运行：

```bash
python3 charts/<图名>.py    # PNG 落在脚本同目录
```

字体用 PingFang SC（macOS 自带）；跨平台跑把 `chart_style.py` 里的
`font.family` 换成 Noto Sans SC。

## 入库边界（隐私规则，见 data2ppt.md 沉淀机制）

`.gitignore` 对本目录做**白名单制**：只有 `README.md`、`chart_style.py`、
`example_dual_axis_line.py` 入库。含真实业务数据的脚本与 PNG 留在本地，
不 commit、不 push。

要沉淀新的通用图式（双轴、堆叠柱、里程碑等）时：把真实数据换成虚构样例
做一份 example 入库，真实版脚本留在本地。

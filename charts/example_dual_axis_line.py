"""示例：双轴折线图模板（虚构数据，可直接复制起步）。

两个指标量级差异大（60% 档 vs 10% 档）时的标准画法：
左轴 = 指标A（深绿），右轴 = 指标B（鼠尾草），轴线与刻度同色以便对照。
双轴仅用于本目录的独立图表；进 deck 的图禁用双轴（design_spec §IV）。

用法：复制本文件改名，替换数据与标题，python3 运行即出 PNG。
"""

from pathlib import Path

import matplotlib.ticker as mticker

from chart_style import (
    INK,
    MUTED,
    PRIMARY_GREEN,
    SAGE,
    add_source_note,
    add_title,
    annotate_values,
    apply_style,
    new_figure,
    plot_line,
    style_spines,
)

OUTPUT_DIR = Path(__file__).resolve().parent

apply_style()

# ↓↓↓ 换成真实数据（虚构样例；两线量级错开，标数才不会互相压字）
periods = ["第1周", "第2周", "第3周", "第4周", "第5周", "第6周"]
metric_a = [62.0, 64.5, 68.0, 71.2, 74.8, 78.0]  # 左轴：量级大
metric_b = [3.2, 4.4, 5.1, 6.3, 7.4, 8.5]  # 右轴：量级小

fig = new_figure((11, 6.2))
add_title(
    fig,
    "指标A升至 78%，指标B升至 8.5%（示例数据）",
    "统计区间：示例 · 按周（共 6 期）",
)

ax = fig.add_axes([0.075, 0.175, 0.835, 0.655])
ax.patch.set_alpha(0)

# 左轴：量级大的指标（深绿，实心点）
plot_line(ax, periods, metric_a, color=PRIMARY_GREEN)
ax.set_ylim(55, 85)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{y:.0f}%"))
ax.yaxis.set_major_locator(mticker.MultipleLocator(5))
ax.set_ylabel("指标A（左轴）", fontsize=11, color=PRIMARY_GREEN, labelpad=8)
ax.tick_params(axis="y", labelsize=10, colors=PRIMARY_GREEN, length=0, pad=8)

# 右轴：量级小的指标（鼠尾草，空心点）
ax2 = ax.twinx()
ax2.patch.set_alpha(0)
plot_line(ax2, periods, metric_b, color=SAGE, face=None)
ax2.set_ylim(0, 25)
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{y:.0f}%"))
ax2.yaxis.set_major_locator(mticker.MultipleLocator(5))
ax2.set_ylabel("指标B（右轴）", fontsize=11, color=SAGE, labelpad=10)
ax2.tick_params(axis="y", labelsize=10, colors=SAGE, length=0, pad=8)

# 逐点标数：两条线贴近时用 offsets 上下避让（传 list 可逐点指定）
annotate_values(ax, metric_a, offsets=13, color=PRIMARY_GREEN, fontsize=12)
annotate_values(ax2, metric_b, offsets=-22, color=SAGE, fontsize=12)

# 轴线：主轴左+下，副轴右
style_spines(ax)
style_spines(ax2, left=False, bottom=False, right=True, right_color=SAGE)

ax.set_xlabel("周期", fontsize=11, color=MUTED, labelpad=8)
ax.tick_params(axis="x", labelsize=10, colors=INK, length=0, pad=8)

add_source_note(fig, "数据来源：示例（虚构数据）· 左右轴刻度不同，仅用于趋势对照")

output_path = OUTPUT_DIR / "example_dual_axis_line.png"
fig.savefig(output_path, dpi=200, transparent=True, bbox_inches="tight")
print(output_path)

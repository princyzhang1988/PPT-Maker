"""charts/ 公共样式模块 — nerdy green tokens 与图表骨架。

tokens 与规则全部取自 templates/nerdy-green-storytelling/templates/design_spec.md
§V（视觉系统）/ §VIII（流程图）：全绿单色系无红、扁平无阴影、无网格线、数值直接标注。

本目录的定位与入库边界见 charts/README.md：chart_style.py 只含样式与通用骨架，
不含任何业务数据；各图表脚本只写数据与少量布局参数，其余视觉细节从这里取。

提供：
- 颜色 tokens（INK/MUTED/PRIMARY_GREEN/DECLINE_GREEN/SAGE/GAIN_GREEN/...）
- apply_style()：rcParams（PingFang SC、无 Unicode 减号问题、200 dpi）
- new_figure / add_title / add_source_note：透明画布 + 左上标题区 + 左下脚注
- style_spines：只保留需要的轴线（主轴左+下，双轴副轴右）
- plot_line：带圆点标记的折线 + 末点实心强调
- annotate_values：逐点等宽字体数值标注（offsets 可逐点指定避让）
- PCT：整数百分比刻度 formatter
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# §V canvas tokens
INK = "#1D1D1F"  # 主文字
MUTED = "#8A8A86"  # 次要文字
PRIMARY_GREEN = "#1F4D3F"  # 主绿：结构/总量/正向强调
DECLINE_GREEN = "#55816D"  # 中绿：下降/异常/风险（全篇无红，靠明度区分方向）
SAGE = "#7FA99B"  # 鼠尾草：次级线/虚线标注框
GAIN_GREEN = "#A9C3B6"  # 浅绿：正向增益
LIGHT_GREEN = "#EAF1ED"  # 淡绿填充
DIVIDER = "#D8E5DE"  # 分割线/轴线
SOFT_GREEN = "#C7D3CC"  # 深底上的浅色文字、外部/入口节点描边（§VIII）

PCT = mticker.FuncFormatter(lambda v, _: f"{v:.0f}%")


def apply_style() -> None:
    """所有图表脚本在绘图前调用一次。"""
    plt.rcParams.update(
        {
            "font.family": "PingFang SC",
            "axes.unicode_minus": False,
            "figure.dpi": 200,
        }
    )


def new_figure(figsize: tuple[float, float]):
    """透明背景画布（PNG 以 transparent=True 落盘）。"""
    fig = plt.figure(figsize=figsize)
    fig.patch.set_alpha(0)
    return fig


def add_title(
    fig,
    title: str,
    subtitle: str,
    *,
    title_y: float = 0.945,
    subtitle_y: float = 0.895,
    title_size: int = 21,
) -> None:
    """左上角结论式大标题 + 次要口径副标题。"""
    fig.text(
        0.02,
        title_y,
        title,
        fontsize=title_size,
        fontweight="bold",
        color=PRIMARY_GREEN,
        ha="left",
        va="center",
    )
    fig.text(
        0.02,
        subtitle_y,
        subtitle,
        fontsize=11,
        color=MUTED,
        ha="left",
        va="center",
    )


def add_source_note(fig, text: str, *, y: float = 0.04) -> None:
    """左下角数据来源/口径脚注。"""
    fig.text(0.02, y, text, fontsize=9, color=MUTED, ha="left", va="center")


def style_spines(ax, *, left: bool = True, bottom: bool = True,
                 right: bool = False, right_color: str = DIVIDER) -> None:
    """无网格线；按需保留左/下/右轴线（右轴用于 twinx 副轴，颜色与刻度同色）。"""
    ax.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["left"].set_visible(left)
    if left:
        ax.spines["left"].set_color(DIVIDER)
    ax.spines["bottom"].set_visible(bottom)
    if bottom:
        ax.spines["bottom"].set_color(DIVIDER)
    ax.spines["right"].set_visible(right)
    if right:
        ax.spines["right"].set_color(right_color)


def plot_line(
    ax,
    labels,
    values,
    *,
    color: str = PRIMARY_GREEN,
    face: str | None = LIGHT_GREEN,
    linewidth: float = 2.0,
    markersize: float = 5.5,
    markeredgewidth: float = 1.6,
    emphasize_last: bool = True,
    last_markersize: float = 10,
    zorder: int = 3,
) -> None:
    """圆点折线；末点用实心大标记强调（face=None 为空心点）。

    注意 matplotlib 的 markerfacecolor=None 是"用默认色"而非空心，
    这里统一翻译为字面量 "none"。
    """
    ax.plot(
        labels,
        values,
        color=color,
        linewidth=linewidth,
        marker="o",
        markersize=markersize,
        markerfacecolor=face if face is not None else "none",
        markeredgewidth=markeredgewidth,
        markeredgecolor=color,
        zorder=zorder,
    )
    if emphasize_last:
        ax.plot(
            labels[-1],
            values[-1],
            marker="o",
            markersize=last_markersize,
            color=color,
            zorder=zorder + 1,
        )


def annotate_values(
    ax,
    values,
    *,
    offsets=13,
    color: str = INK,
    fmt: str = "{:.1f}%",
    fontsize: int = 11,
    fontweight: str = "bold",
) -> None:
    """逐点数值标注，等宽字体；offsets 传 list 时逐点指定上下避让。"""
    if not isinstance(offsets, (list, tuple)):
        offsets = [offsets] * len(values)
    for index, value in enumerate(values):
        ax.annotate(
            fmt.format(value),
            (index, value),
            textcoords="offset points",
            xytext=(0, offsets[index]),
            ha="center",
            fontsize=fontsize,
            fontfamily="monospace",
            fontweight=fontweight,
            color=color,
        )

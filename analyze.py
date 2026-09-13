#!/usr/bin/env python3
"""analyze.py — data2ppt 自动探查脚本（方法论规则库 §A/§B/§H/§I 的可执行版）

输入一份 CSV/XLSX 和可选参数，产出 facts.json 草稿：
- §H.0 数据清洗（探查前必跑）：单位识别与归一化（列名后缀 _wan/_yi/万/亿 等）、
  缺失率、脏值（coerce 为 NaN）、重复行、同指标多单位冲突检测
- §H 结构优先：行列概览、缺失值、字段类型、分类维度排名/贡献度分解
- §H 漏斗：--funnel 指定阶段列序列，算各阶段值、相邻转化率/流失率、整体转化
- §H 画像：--dims 指定维度，算构成占比、累计占比（集中度）
- §A 数据可信前置检查：CV 稳定性阈值、3σ/IQR 异常值（link_check 留人工）
- 趋势：时间序列的最新变化幅度、最大涨跌
- §B 三比：自己比（同比/环比/定基）实算；标杆比/市场比标注不可得原因
- §I 六法实跑（「分析方式提案」确认点的可执行项）：
  - 象限：--quadrant X,Y 配合 --dims，两指标切四象限（中位数分界，|r|>0.8 退化告警）
  - 留存：--retention 用户,日期[,分组]，按首次活跃日分 cohort，算次日/7日/30日留存
  - RFM：--rfm 用户,日期,金额，R/F/M 中位数切分八群，输出各群人数与营收占比

用法：
  .venv/bin/python analyze.py <data.csv> [--metric 指标列] [--time 时间列] \
      [--dims 维度列1,维度列2] [--compare 期1,期2] [--funnel 阶段列1,阶段列2,...] \
      [--quadrant X列,Y列] [--cuts X界,Y界] [--rfm 用户列,日期列,金额列] \
      [--retention 用户列,日期列[,分组列]] [--out facts_draft.json]

只跑 --rfm / --retention 时可以不提供 --metric（跳过指标级清洗与 §A 检查）。
输出 JSON 到 --out（默认打印 stdout）。**草稿仅供 AI 复核补充，不直接作为
facts.json 使用**——业务口径、caveats、决策框架仍由分析者补全。
数值列带单位后缀（如 gmv_wan）时，脚本自动归一化到绝对量基准后再计算，
并在 data_cleaning 中披露单位映射，防止单位不统一污染贡献度分解。
"""
import argparse
import json
import re
import sys

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep
from statsmodels.stats.weightstats import CompareMeans, DescrStatsW

# ---------------------------------------------------------------------------
# §H.0 数据清洗 / 标准化（探查前必跑）
# ---------------------------------------------------------------------------

# (列名后缀, 归一化倍率, 单位标签)；倍率 None 表示"百分比类，不缩放，仅标记"
UNIT_TABLE = [
    ("亿", 1e8, "亿"),
    ("_yi", 1e8, "亿"),
    ("万", 1e4, "万"),
    ("_wan", 1e4, "万"),
    ("_w", 1e4, "万"),
    ("_千", 1e3, "千"),
    ("_qian", 1e3, "千"),
    ("_yuan", 1.0, "元"),
    ("_元", 1.0, "元"),
    ("_fen", 0.01, "分"),
    ("_分", 0.01, "分"),
    ("_pct", None, "百分比"),
    ("_percent", None, "百分比"),
    ("_率", None, "百分比"),
]


def unit_of(col: str):
    """从列名后缀识别单位。返回 (base_name, factor, unit_label)。

    factor=None 表示百分比类列（不缩放）；factor=1.0 表示无单位后缀。
    """
    for suffix, factor, label in UNIT_TABLE:
        if len(col) > len(suffix) and col.endswith(suffix):
            return col[:-len(suffix)], factor, label
    return col, 1.0, "无单位后缀"


def clean_block(df: pd.DataFrame, metric_col: str) -> dict:
    """探查前清洗：单位归一化、缺失率、脏值、重复行、同指标多单位冲突。

    返回 dict 含一个内部键 "_series"：归一化后的指标列（后续计算统一用它），
    json 输出时该键被剔除。
    """
    base, factor, unit_label = unit_of(metric_col)
    s_raw = pd.to_numeric(df[metric_col], errors="coerce")
    # 百分比列（factor=None）不缩放；绝对量列统一乘倍率到基准单位
    s_norm = s_raw if factor is None else s_raw * factor

    # 缺失率：逐列统计缺失数与占比，>=5% 标 warning
    missing = {}
    missing_warns = []
    for c in df.columns:
        n = int(df[c].isna().sum())
        if n:
            rate = n / len(df) * 100
            missing[c] = {"count": n, "rate_pct": round(rate, 2)}
            if rate >= 5:
                missing_warns.append(f"列 '{c}' 缺失率 {rate:.1f}% ≥ 5%，结论需注明样本口径")

    # 脏值：metric 列被 coerce 为 NaN 的原始非空值数量
    coerced = int((df[metric_col].notna() & s_raw.isna()).sum())

    # 重复行
    dup = int(df.duplicated().sum())

    # 同指标多单位冲突：所有数值列按 base_name 聚合，若同一基名下存在不同单位后缀
    unit_map = {}
    for c in df.select_dtypes("number").columns:
        b, f, lbl = unit_of(c)
        if f is None:
            continue  # 百分比列不算绝对量冲突
        unit_map.setdefault(b, set()).add(lbl)
    unit_conflicts = [
        {"base": b, "columns": [c for c in df.columns if unit_of(c)[0] == b],
         "issue": f"同指标 '{b}' 存在多个单位后缀（{', '.join(sorted(s))}），"
                  f"必须先统一口径再聚合，否则直接求和会污染分解结果"}
        for b, s in unit_map.items() if len(s) > 1
    ]

    out = {
        "metric_unit": {
            "column": metric_col, "base_name": base, "unit": unit_label,
            "factor": factor if factor is not None else "percent(no-scale)",
            "normalized_to": "绝对量基准（元/件）" if factor not in (None, 1.0)
                             else ("百分比列，不缩放，仅标记" if factor is None else "无单位后缀，原值"),
        },
        "missing": missing,
        "dirty_values": {"column": metric_col, "coerced_to_nan": coerced}
                        if coerced else None,
        "duplicate_rows": dup,
        "unit_conflicts": unit_conflicts,
        "warnings": missing_warns + ([f"列 '{metric_col}' 含 {coerced} 个非数值脏值，已转 NaN 并在口径注披露"]
                                     if coerced else []),
        "_series": s_norm,
    }
    return out


# ---------------------------------------------------------------------------
# §A 数据可信前置检查
# ---------------------------------------------------------------------------


def stability_label(cv: float) -> str:
    if cv < 15:
        return f"高稳定（CV={cv:.1f}% < 15%），变化可视为真实业务信号"
    if cv < 30:
        return f"中等稳定（CV={cv:.1f}%），结论需结合业务背景谨慎表述"
    return f"低稳定（CV={cv:.1f}% ≥ 30%），指标噪声大——结论标'暂定'，不得写成确定性表述"


def outlier_check(series: pd.Series) -> dict:
    """3σ 与 IQR 双方法标记（方法论 §A.3），只标记不剔除。"""
    s = series.dropna()
    mean, std = s.mean(), s.std()
    z = (s - mean) / std if std > 0 else pd.Series(0, index=s.index)
    sigma_flags = s[abs(z) > 3].index.tolist()
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    iqr_flags = s[(s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)].index.tolist()
    return {
        "method": "3σ + IQR（1.5 倍）双方法标记，只标记不剔除",
        "sigma_flags": sigma_flags,
        "iqr_flags": iqr_flags,
        "note": "被剔除/标注的值必须在 deck 口径注中披露（§A.3）",
    }


# ---------------------------------------------------------------------------
# §B 三比 / 趋势
# ---------------------------------------------------------------------------


def trend_block(df: pd.DataFrame, time_col: str, metric_col: str) -> dict:
    d = df[[time_col, metric_col]].dropna().sort_values(time_col)
    if len(d) < 2:
        return {}
    vals = d[metric_col].tolist()
    latest, prev = vals[-1], vals[-2]
    deltas = d[metric_col].diff().dropna()
    out = {
        "latest_period": str(d[time_col].iloc[-1]),
        "latest_delta": round(latest - prev, 4),
        "latest_delta_pct": round((latest - prev) / abs(prev) * 100, 2) if prev else None,
    }
    if len(deltas):
        pos_min = int(np.asarray(deltas.values).argmin())
        pos_max = int(np.asarray(deltas.values).argmax())
        out["max_drop_period"] = str(d[time_col].iloc[pos_min + 1])
        out["max_drop"] = round(float(deltas.values[pos_min]), 4)
        out["max_rise_period"] = str(d[time_col].iloc[pos_max + 1])
        out["max_rise"] = round(float(deltas.values[pos_max]), 4)
    if len(vals) >= 3:
        first = vals[0]
        out["vs_period_start_pct"] = round((latest - first) / abs(first) * 100, 2) if first else None
    return out


# ---------------------------------------------------------------------------
# §H 结构：贡献度分解 / 分类排名
# ---------------------------------------------------------------------------


def contribution_block(df: pd.DataFrame, dims: list, time_col: str, metric_col: str, compare: list) -> dict:
    """两期对比时按维度分解贡献度（方法论：贡献度 = 本期-上期，按维度下钻）。

    每期原始行数 ≥8 时附 Bootstrap 95% CI（按行放回重采样 1000 次，种子 42 可复现）；
    行数不足则 contribution_ci95=None 并在 note 说明（样本太少区间无意义）；
    某维度在重采样中无有效样本（某期被完全淘汰）时该维度 CI 亦为 None。
    """
    d = df.copy()
    if compare:
        d = d[d[time_col].astype(str).isin(compare)]
        if d[time_col].astype(str).nunique() != 2:
            return {"error": f"--compare 两期在数据中不存在：{compare}"}
    periods = sorted(d[time_col].astype(str).unique())
    if len(periods) != 2:
        return {"error": f"贡献度分解需要恰有两个期间（{time_col} 现有 {periods}），用 --compare 指定"}
    p0, p1 = periods
    wide = d.pivot_table(index=dims, columns=time_col, values=metric_col, aggfunc="sum")
    wide["delta"] = wide[p1] - wide[p0]
    total = wide["delta"].sum()
    # §I-8 附属：贡献度 Bootstrap 95% CI（按原始行放回重采样；每期 <8 行无意义则跳过）
    rng = np.random.default_rng(42)
    raw0 = d[d[time_col].astype(str) == p0]
    raw1 = d[d[time_col].astype(str) == p1]
    boot_ok = len(raw0) >= 8 and len(raw1) >= 8
    ci_map = {}
    if boot_ok:
        for _ in range(1000):
            s0 = raw0.sample(len(raw0), replace=True, random_state=rng)
            s1 = raw1.sample(len(raw1), replace=True, random_state=rng)
            w = pd.concat([s0, s1]).pivot_table(index=dims, columns=time_col,
                                                values=metric_col, aggfunc="sum")
            if p0 not in w.columns or p1 not in w.columns:
                continue
            delta_b = w[p1] - w[p0]
            t = delta_b.sum()
            if not t:
                continue
            # 重采样可能漏掉某维度某期的全部行 → delta 为 NaN，须剔除防污染分位数
            pct_b = (delta_b / t * 100).dropna()
            for k, v in pct_b.items():
                ci_map.setdefault(k, []).append(float(v))
    wide["contribution_pct"] = (wide["delta"] / total * 100).round(1) if total else np.nan
    wide = wide.sort_values("delta")
    rows = []
    for dim_key, row in wide.iterrows():
        dim_vals = dim_key if isinstance(dim_key, tuple) else (dim_key,)
        # ci_map 的 key 与 pivot_table(index=dims) 索引同源（单维度标量/多维度元组），
        # 与 iterrows 的原始 key 同型，直接用原始 key 查表；归一化后的元组会查空单维度键。
        # ci_vals 为空（每期 <8 行未跑 Bootstrap，或该维度在某期重采样中被完全淘汰）→ CI=None
        ci_vals = ci_map.get(dim_key, []) if boot_ok else []
        rows.append({
            "dims": dict(zip(dims, [str(v) for v in dim_vals])),
            f"val_{p0}": round(float(row[p0]), 4), f"val_{p1}": round(float(row[p1]), 4),
            "delta": round(float(row["delta"]), 4),
            "contribution_pct": None if pd.isna(row["contribution_pct"]) else float(row["contribution_pct"]),
            "contribution_ci95": (
                [round(float(np.percentile(ci_vals, 2.5)), 1),
                 round(float(np.percentile(ci_vals, 97.5)), 1)]
                if ci_vals else None),
        })
    return {"periods": [p0, p1], "total_delta": round(float(total), 4), "by_dim": rows,
            "note": ("负贡献排在最前；贡献度只回答'哪里变了'，不回答'为什么'——归因需假设验证"
                     + ("；contribution_ci95 为 Bootstrap 95% 区间（按行放回重采样 1000 次）"
                        if boot_ok else "；每期行数 <8，Bootstrap CI 无意义未计算"))}


def category_rank_block(df: pd.DataFrame, dims: list, metric_col: str) -> dict:
    """结构视角：分类维度排名（无时间列或两期不足时的兜底）。"""
    rank = df.groupby(dims)[metric_col].sum().sort_values(ascending=False)
    return {"top": {str(k): round(float(v), 4) for k, v in rank.head(3).items()},
            "bottom": {str(k): round(float(v), 4) for k, v in rank.tail(3).items()},
            "note": "排名=结构视角（§H 先看结构）；贡献度分解需两期数据"}


# ---------------------------------------------------------------------------
# §H 漏斗：链路转化 / 流失（方法论 §H「再看漏斗」）
# ---------------------------------------------------------------------------


def funnel_block(df: pd.DataFrame, stages: list) -> dict:
    """漏斗分析：每列为一个阶段的量（人数/金额），算相邻转化率与流失率。

    只回答"哪里流失最多"，不回答"为什么"——归因需假设验证。
    """
    missing = [st for st in stages if st not in df.columns]
    if missing:
        return {"error": f"漏斗阶段列不存在：{missing}"}
    vals = []
    for st in stages:
        raw = pd.to_numeric(df[st], errors="coerce")
        _, factor, label = unit_of(st)
        v = raw.sum() if factor is None else raw.sum() * factor
        vals.append({"stage": st, "unit": label, "value": round(float(v), 4)})
    convs = []
    for i in range(1, len(vals)):
        prev_v = vals[i - 1]["value"]
        unit_i, unit_j = vals[i - 1]["unit"], vals[i]["unit"]
        same_unit = unit_i == unit_j
        row = {"from": stages[i - 1], "to": stages[i],
               "unit_from": unit_i, "unit_to": unit_j}
        if not same_unit:
            row.update({
                "conv_rate_pct": None, "drop_pct": None,
                "note": f"相邻阶段量纲不一致（{unit_i} vs {unit_j}），转化率无业务意义——"
                        f"先统一口径再算转化（§H 漏斗）",
            })
        elif prev_v:
            cur = vals[i]["value"]
            row.update({
                "conv_rate_pct": round(cur / prev_v * 100, 1),
                "drop_pct": round((1 - cur / prev_v) * 100, 1),
            })
        else:
            row.update({"conv_rate_pct": None, "drop_pct": None,
                        "note": "上一阶段为 0，转化率无法计算"})
        convs.append(row)
    overall = None
    overall_note = None
    if len(vals) >= 2 and vals[0]["value"]:
        if vals[0]["unit"] == vals[-1]["unit"]:
            overall = round(vals[-1]["value"] / vals[0]["value"] * 100, 1)
        else:
            overall_note = (f"首尾阶段量纲不一致（{vals[0]['unit']} vs {vals[-1]['unit']}），"
                            f"整体转化率不计算，需先统一口径")
    valid = [c for c in convs if c.get("conv_rate_pct") is not None]
    max_drop = max(valid, key=lambda c: c["drop_pct"]) if valid else None
    return {
        "stages": vals,
        "conversions": convs,
        "overall_conv_pct": overall,
        "overall_note": overall_note,
        "max_loss_edge": {"from": max_drop["from"], "to": max_drop["to"],
                          "drop_pct": max_drop["drop_pct"]} if max_drop else None,
        "note": "漏斗只回答'哪里流失最多'，不回答'为什么'——归因需假设验证（§H）",
    }


# ---------------------------------------------------------------------------
# §H 画像：构成占比 / 集中度（方法论 §H「再看画像」）
# ---------------------------------------------------------------------------


def profile_block(df: pd.DataFrame, dims: list, metric_col: str) -> dict:
    """画像分析：按维度看构成占比与累计占比（集中度）。

    top3 集中度（累计占比）≥ 60% 提示头部集中，分层运营时优先做头部；
    分布均匀（top1 < 30%）提示无主导层，需另找分层变量。
    """
    agg = df.groupby(dims)[metric_col].sum().sort_values(ascending=False)
    total = agg.sum()
    if not total:
        return {"error": "画像维度下指标合计为 0，无法计算占比"}
    share = (agg / total * 100).round(1)
    cum = share.cumsum().round(1)
    rows = []
    for k0, v in agg.items():
        k = k0 if isinstance(k0, tuple) else (k0,)
        rows.append({
            "dims": dict(zip(dims, [str(x) for x in k])),
            "value": round(float(v), 4),
            "share_pct": float(share[k0]),
            "cum_share_pct": float(cum[k0]),
        })
    top3 = rows[:3]
    top1_share = rows[0]["share_pct"] if rows else None
    top3_cum = top3[-1]["cum_share_pct"] if len(top3) == 3 else (top3[-1]["cum_share_pct"] if top3 else None)
    if top3_cum is not None and top3_cum >= 60:
        concentration = f"头部集中（Top3 累计占比 {top3_cum}% ≥ 60%），分层运营优先做头部"
    elif top1_share is not None and top1_share < 30:
        concentration = f"分布均匀（Top1 占比 {top1_share}% < 30%），无主导层，需另找分层变量"
    else:
        concentration = "集中度中等，建议结合业务规则进一步分层"
    return {
        "by_dim": rows,
        "top1_share_pct": top1_share,
        "top3_cum_share_pct": top3_cum,
        "concentration": concentration,
        "note": "画像=构成与集中度；分层需结合业务规则（§H 再看画像）",
    }


# ---------------------------------------------------------------------------
# §I 象限分析（保谁弃谁：两指标四象限）
# ---------------------------------------------------------------------------


def quadrant_block(df: pd.DataFrame, x_col: str, y_col: str, dims: list, cuts) -> dict:
    """象限分析：每个分析对象（--dims 聚合求和）取两指标切四象限。

    分界线默认取各自中位数——仅作起点，最终切线须结合业务阈值校准；
    两轴 |r|>0.8 视为四象限退化，告警换轴（§I-4）。
    """
    d = df.copy()
    for c in (x_col, y_col):
        if c not in d.columns:
            return {"error": f"象限分析列不存在：{c}"}
        d[c] = pd.to_numeric(d[c], errors="coerce")
    g = d.dropna(subset=[x_col, y_col]).groupby(dims)[[x_col, y_col]].sum()
    if len(g) < 4:
        return {"error": f"象限分析需要 ≥4 个分析对象（{dims} 现有 {len(g)} 个）"}
    xs, ys = g[x_col].astype(float), g[y_col].astype(float)
    corr = float(xs.corr(ys)) if xs.std() > 0 and ys.std() > 0 else None
    degenerate = corr is not None and abs(corr) > 0.8
    cut_x = cuts[0] if cuts and cuts[0] is not None else float(xs.median())
    cut_y = cuts[1] if cuts and cuts[1] is not None else float(ys.median())

    def quadrant_name(x: float, y: float) -> str:
        if x >= cut_x and y >= cut_y:
            return "高X高Y（放大）"
        if x < cut_x and y >= cut_y:
            return "低X高Y（维持/保收）"
        if x >= cut_x and y < cut_y:
            return "高X低Y（核查/观察）"
        return "低X低Y（收缩/退出）"

    total_y = float(ys.sum())
    rows = []
    for key, row in g.iterrows():
        k = key if isinstance(key, tuple) else (key,)
        x_val, y_val = float(row[x_col]), float(row[y_col])
        rows.append({
            "dims": dict(zip(dims, [str(v) for v in k])),
            "x": round(x_val, 4), "y": round(y_val, 4),
            "quadrant": quadrant_name(x_val, y_val),
            "y_share_pct": round(y_val / total_y * 100, 1) if total_y else None,
        })
    rows.sort(key=lambda r: (r["quadrant"], -(r["y"] or 0)))
    return {
        "x_metric": x_col, "y_metric": y_col,
        "cut_lines": {"x": round(cut_x, 4), "y": round(cut_y, 4),
                      "note": "默认中位数，仅作起点——最终切线须业务校准并写入口径注"},
        "corr_xy": None if corr is None else round(corr, 3),
        "degenerate_warning": "两轴强相关（|r|>0.8），四象限退化成一条线——换轴或弃用（§I-4）"
                              if degenerate else None,
        "by_object": rows,
        "note": "聚合方式为求和；比率类指标（增速/毛利率）请先按对象预算好再进象限；"
                "静态象限需跟踪跨期位置变化",
    }


# ---------------------------------------------------------------------------
# §I 留存分析（拉来的人留得住吗：cohort × 精确第 N 日回访）
# ---------------------------------------------------------------------------


def retention_block(df: pd.DataFrame, user_col: str, date_col: str, segment_col=None) -> dict:
    """留存分析：用户级活跃明细，按首次活跃日分 cohort，算 D1/D7/D30 精确回访留存。

    口径 = 精确第 N 日（日历日偏移）有活跃，非"N 日内仍活跃"滚动口径；
    未成熟 cohort（观察期不足 N 天）不计入并单独标注（§I-5）。
    """
    cols = [user_col, date_col] + ([segment_col] if segment_col else [])
    missing = [c for c in cols if c not in df.columns]
    if missing:
        return {"error": f"留存分析列不存在：{missing}"}
    d = df[cols].copy()
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[user_col, date_col])
    if d.empty:
        return {"error": "留存分析：用户/日期列无可解析数据"}
    d["day"] = d[date_col].dt.normalize()
    snapshot = d["day"].max()
    first = d.groupby(user_col)["day"].min().rename("cohort_day")
    d = d.join(first, on=user_col)
    d["offset_days"] = (d["day"] - d["cohort_day"]).dt.days

    def cohort_table(sub: pd.DataFrame) -> dict:
        users = sub[user_col].nunique()
        out = {"cohort_users": users}
        for n_day in (1, 7, 30):
            key = f"d{n_day}_retention_pct"
            matured = sub[sub["cohort_day"] <= snapshot - pd.Timedelta(days=n_day)]
            m_users = matured[user_col].nunique()
            if m_users == 0:
                out[key] = None
                out[f"{key}_note"] = "观察期不足，cohort 未成熟，不计入"
            else:
                retained = matured[matured["offset_days"] == n_day][user_col].nunique()
                out[key] = round(retained / m_users * 100, 1)
        return out

    result = {
        "snapshot_date": str(snapshot.date()),
        "definition": "Dn = 首次活跃后第 N 个日历日（精确命中）仍有活跃的用户占比；"
                      "未成熟 cohort 不计入",
        "overall": cohort_table(d),
    }
    if segment_col:
        by_segment = {}
        for seg, sub in d.dropna(subset=[segment_col]).groupby(segment_col):
            by_segment[str(seg)] = cohort_table(sub)
        result["by_segment"] = by_segment
    result["notes"] = [
        "必须按渠道/人群拆分看留存，整体均值会掩盖渠道质量差异（§I-5）",
        "警惕幸存者偏差：少数高频用户撑高整体曲线，不等于普遍粘性",
        "多 cohort 合并统计（按首活跃日过滤未成熟用户）；新增留存≠活跃留存，口径注须声明",
    ]
    return result


# ---------------------------------------------------------------------------
# §I RFM 分析（谁是高价值客户：R/F/M 中位数切分八群）
# ---------------------------------------------------------------------------

# 8 种 R/F/M 组合的默认分群名与建议动作（动作仅为起点，须业务确认并配责任人）
RFM_LABELS = {
    (1, 1, 1): "重要价值（维持：一对一维护+专属权益）",
    (0, 1, 1): "重要唤回（R 阈值期内定向触达召回）",
    (1, 0, 1): "重要深耕（提频：复购/搭配推荐）",
    (1, 1, 0): "潜力客户（提客单：组合/满额）",
    (1, 0, 0): "新客（首购转化与激活）",
    (0, 0, 1): "重要挽留（高价值趋流失，优先人工介入）",
    (0, 1, 0): "一般保持（低频平价，低成本触达）",
    (0, 0, 0): "流失风险（低成本召回或放弃）",
}


def rfm_block(df: pd.DataFrame, user_col: str, date_col: str, amount_col: str) -> dict:
    """RFM：用户级订单 → 最近购买 R（天）/频次 F/金额 M，中位数切分八群。

    阈值来自自家数据中位数（不得照抄行业经验线）；每群动作仅为默认建议，
    须配责任人与业务确认（§I-6）。
    """
    missing = [c for c in (user_col, date_col, amount_col) if c not in df.columns]
    if missing:
        return {"error": f"RFM 列不存在：{missing}"}
    d = df[[user_col, date_col, amount_col]].copy()
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d[amount_col] = pd.to_numeric(d[amount_col], errors="coerce")
    d = d.dropna()
    if d.empty:
        return {"error": "RFM：用户/日期/金额列无可解析数据"}
    _, _, amount_unit = unit_of(amount_col)
    snapshot = d[date_col].max()
    g = d.groupby(user_col).agg(
        last_date=(date_col, "max"), F=(date_col, "count"), M=(amount_col, "sum")
    )
    g["R_days"] = (snapshot - g["last_date"]).dt.days
    r_cut, f_cut, m_cut = float(g["R_days"].median()), float(g["F"].median()), float(g["M"].median())

    g["segment"] = [
        RFM_LABELS[(int(r <= r_cut), int(f >= f_cut), int(m >= m_cut))]
        for r, f, m in zip(g["R_days"], g["F"], g["M"])
    ]
    total_m = float(g["M"].sum())
    rows = []
    for seg, sub in g.groupby("segment"):
        rows.append({
            "segment": seg,
            "users": int(len(sub)),
            "user_share_pct": round(len(sub) / len(g) * 100, 1),
            "revenue_share_pct": round(float(sub["M"].sum()) / total_m * 100, 1) if total_m else None,
            "median_r_days": float(sub["R_days"].median()),
            "median_f": float(sub["F"].median()),
            "median_m": float(sub["M"].median()),
        })
    rows.sort(key=lambda r: -(r["revenue_share_pct"] or 0))
    out = {
        "snapshot_date": str(snapshot.date()),
        "amount_unit": amount_unit,
        "thresholds": {
            "r_good_days_le": round(r_cut, 1), "f_good_orders_ge": round(f_cut, 1),
            "m_good_amount_ge": round(m_cut, 2),
            "note": "阈值=自家数据中位数，不得照抄行业经验线（§I-6）",
        },
        "segments": rows,
        "notes": [
            "每群动作仅为默认建议，须配责任人与业务确认，方向标签联动 §G 三分类",
            "权重调整（加权 RFM）须经回归/AB 验证后才可使用",
        ],
    }
    if len(g) < 30:
        out["notes"].append(f"用户数 {len(g)} < 30，分群结论标'暂定'（样本量规则 §A.4）")
    return out


# ---------------------------------------------------------------------------
# §I 显著性检验（差异是噪声还是真信号：Leek&Peng「推断性」问题的可执行版）
# ---------------------------------------------------------------------------

SIGTEST_MIN_N = 30  # §A.4 精神：每组 n<30 不输出 p 值，只报效应量方向


def _cohen_d(a: pd.Series, b: pd.Series):
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return None  # 单观测组标准差未定义（ddof=1），效应量不可算，防 NaN 漏进 JSON
    pooled = (((na - 1) * a.std(ddof=1) ** 2 + (nb - 1) * b.std(ddof=1) ** 2)
              / (na + nb - 2)) ** 0.5
    return float((a.mean() - b.mean()) / pooled) if pooled else None


def _two_group_report(g1: pd.Series, g2: pd.Series, label1: str, label2: str) -> dict:
    """两组均值检验报告：n<30 只报效应量方向；n≥30 出 Welch t / Mann-Whitney U 与结论。"""
    if len(g1) == 0 or len(g2) == 0:
        return {"error": f"某组 coerce 后无有效数值（组1 {len(g1)} 行 / 组2 {len(g2)} 行）"}
    out = {"form": "两组均值检验",
           "group1": {"label": label1, "n": int(len(g1)), "mean": round(float(g1.mean()), 4)},
           "group2": {"label": label2, "n": int(len(g2)), "mean": round(float(g2.mean()), 4)}}
    d = _cohen_d(g1, g2)
    out["effect_cohens_d"] = round(d, 3) if d is not None else None
    if len(g1) < SIGTEST_MIN_N or len(g2) < SIGTEST_MIN_N:
        out.update({
            "sample_guard": f"每组 n≥{SIGTEST_MIN_N} 才输出 p 值（§A.4）——当前只报效应量方向",
            "effect_direction": "group1 > group2" if g1.mean() > g2.mean() else "group1 < group2",
            "conclusion": "样本不足，差异是否真实待更多数据——标'暂定'",
        })
        return out
    shapiro_ran = False
    normal = True
    for s in (g1, g2):
        if 3 <= len(s) <= 5000:
            shapiro_ran = True
            normal = normal and stats.shapiro(s).pvalue >= 0.05
    cm = CompareMeans(DescrStatsW(g1), DescrStatsW(g2))
    lo, hi = cm.tconfint_diff(usevar="unequal")
    t_stat, p_welch = stats.ttest_ind(g1, g2, equal_var=False)
    u_stat, p_mw = stats.mannwhitneyu(g1, g2, alternative="two-sided")
    out.update({
        "tests": {
            "welch_t": {"stat": round(float(t_stat), 4), "p": round(float(p_welch), 4),
                        "ci95_diff": [round(float(lo), 4), round(float(hi), 4)]},
            "mann_whitney_u": {"stat": round(float(u_stat), 4), "p": round(float(p_mw), 4)},
        },
        "normality": ("shapiro 双组 p≥0.05，以 Welch t 为主" if normal and shapiro_ran
                      else "至少一组偏离正态，以 Mann-Whitney U 为主" if shapiro_ran
                      else "n>5000 未做 Shapiro（大样本渐近下以 Welch t 为主）"),
        "conclusion": ("检出显著差异（p<0.05）" if (p_welch if normal else p_mw) < 0.05
                       else "未检出显著差异（p≥0.05）——不等于无差异，可能是检验力不足"),
    })
    return out


def sigtest_block(df: pd.DataFrame, parts: list, compare: list, time_col) -> dict:
    """--sigtest：2 参数=两组均值检验；3 参数=双比率 z 检验（每行一组）；
    1 参数=指标列，配 --time + --compare 切两期做两组均值检验。"""
    if len(parts) == 3:  # 成功列,总数列,组列
        succ, total, grp = parts
        missing = [c for c in (succ, total, grp) if c not in df.columns]
        if missing:
            return {"error": f"比率检验列不存在：{missing}"}
        d = df[[succ, total, grp]].copy()
        for c in (succ, total):
            d[c] = pd.to_numeric(d[c], errors="coerce")
        d = d.dropna()
        if len(d) < 2:
            return {"error": "比率检验需要 ≥2 行（每行一组）"}
        (g1, s1, n1), (g2, s2, n2) = [(str(r[grp]), float(r[succ]), float(r[total]))
                                      for _, r in d.head(2).iterrows()]
        if min(n1, n2) <= 0 or s1 > n1 or s2 > n2:
            return {"error": "比率检验数据非法：成功数应 ≤ 总数且总数 > 0"}
        z, p = proportions_ztest([s1, s2], [n1, n2])
        if not (np.isfinite(z) and np.isfinite(p)):
            return {"error": "比率检验退化（如两组成功数均为 0）——无法计算检验统计量，"
                             "请检查数据或积累样本后再检验"}
        p1, p2 = s1 / n1, s2 / n2
        lo, hi = confint_proportions_2indep(s1, n1, s2, n2, method="wald",
                                            compare="diff", alpha=0.05)
        out = {"form": "两比率 z 检验",
               "groups": [{"group": g1, "success": s1, "total": n1, "rate": round(p1, 4)},
                          {"group": g2, "success": s2, "total": n2, "rate": round(p2, 4)}],
               "z_stat": round(float(z), 4), "p": round(float(p), 4),
               "abs_rate_diff": round(abs(p1 - p2), 4),
               "ci95_diff": [round(float(lo), 4), round(float(hi), 4)],
               "conclusion": ("两比率差异显著（p<0.05）" if p < 0.05
                              else "未检出显著差异（p≥0.05）——不等于无差异")}
        if len(d) > 2:
            out["multiple_comparison_note"] = (f"共 {len(d)} 组只比了前两组——"
                                               f"两两全比需 Bonferroni 校正（阈值 α/{len(d)}）")
        return out

    if len(parts) == 2:
        value_col, group_col = parts
    elif len(parts) == 1:
        value_col, group_col = parts[0], None
    else:
        return {"error": "--sigtest 参数：指标列[,分组列] 或 成功列,总数列,组列"}
    if value_col not in df.columns:
        return {"error": f"指标列不存在：{value_col}"}
    d = df.copy()
    d[value_col] = pd.to_numeric(d[value_col], errors="coerce")

    if group_col:
        if group_col not in df.columns:
            return {"error": f"分组列不存在：{group_col}"}
        levels = d[group_col].dropna().unique().tolist()
        if len(levels) != 2:
            return {"error": f"分组列恰好需要两组（现有 {len(levels)} 组）——"
                             f"请二选一/合并，或全对比需 Bonferroni 校正（§I-7）"}
        g1 = d[d[group_col] == levels[0]][value_col].dropna()
        g2 = d[d[group_col] == levels[1]][value_col].dropna()
        return _two_group_report(g1, g2, str(levels[0]), str(levels[1]))

    # 无分组列：--time + --compare 两期切
    if not (compare and time_col):
        return {"error": "均值检验需要分组列，或 --time + --compare 指定两期"}
    d[time_col] = d[time_col].astype(str)
    d = d[d[time_col].isin(compare)]
    periods = sorted(d[time_col].unique())
    if len(periods) != 2:
        return {"error": f"--compare 需在数据中恰有两期：{compare}（现有 {periods}）"}
    g1 = d[d[time_col] == periods[0]][value_col].dropna()
    g2 = d[d[time_col] == periods[1]][value_col].dropna()
    return _two_group_report(g1, g2, periods[0], periods[1])


# ---------------------------------------------------------------------------
# §I 准实验归因（变化是否由干预导致：DiD / 中断对比；DoWhy 仅作参照不引依赖）
# ---------------------------------------------------------------------------

DOWHY_NOTE = "若能提供变量因果图（DAG），可安装 dowhy 做 GCM 异动归因——超出本脚本范围（§I-8）"


def _floatable(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def _period_key(t: str):
    """数值感知排序键：数字段按数值比较（2 < 10，W2 < W10），非数字段按词法。"""
    return tuple((0, float(p)) if p.isdigit() else (1, p)
                 for p in re.split(r"(\d+)", str(t).strip()))


def causal_block(df: pd.DataFrame, parts: list, compare: list, interrupt: str) -> dict:
    """--causal：3 参数=DiD（配 --compare）；2 参数=中断前后对比（配 --interrupt）。

    DiD 的 --compare 语义：期1=干预前最后一期，期2=干预后第一期；
    全面板回归 post = 时间排序 ≥ 期2 的所有期（两期过滤会得到饱和模型，CI/p 无意义）；
    期序为数值感知排序（全数值或同一前缀+纯序号时按数值，避免 W10 插进 W1 与 W2 之间），
    无法确定数值序时回退词法序并在 notes 提示确认期序。
    """
    downgrade = "无对照组且无干预点 → 路由降级为探索性归因（--dims 贡献度分解），结论标'暂定'（§I.0 规则 1）"
    if len(parts) == 3 and interrupt is None:
        value_col, time_col, group_col = parts
        missing = [c for c in (value_col, time_col, group_col) if c not in df.columns]
        if missing:
            return {"error": f"DiD 列不存在：{missing}"}
        if not compare or len(compare) != 2:
            return {"error": "DiD 需要 --compare 干预前最后一期,干预后第一期（如 W4,W5）",
                    "downgrade": downgrade}
        d = df.copy()
        d[value_col] = pd.to_numeric(d[value_col], errors="coerce")
        d = d.dropna(subset=[value_col, group_col])  # 组缺失行不得静默落入对照组（treat=0）
        d[time_col] = d[time_col].astype(str)
        periods = sorted(d[time_col].unique())
        stripped = [str(t).strip() for t in periods]
        ms = [re.fullmatch(r"(\D*)(\d+)", s) for s in stripped]
        # 期序：全数值或同一前缀+纯序号（W1..W12）时按数值序；否则词法序并提示确认
        numeric_sorted = (all(_floatable(s) for s in stripped)
                          or (all(ms) and len({m.group(1) for m in ms}) == 1))
        periods = sorted(periods, key=_period_key)
        period_order = "数值序" if numeric_sorted else "词法序（请确认期标签）"
        pre_anchor, post_anchor = compare[0], compare[1]
        if pre_anchor not in periods or post_anchor not in periods:
            return {"error": f"--compare 两期都必须存在于数据：{compare}（现有 {periods}）",
                    "downgrade": downgrade}
        if periods.index(pre_anchor) >= periods.index(post_anchor):
            return {"error": f"--compare 期1 必须早于期2（语义：末个干预前期,首个干预后期）：{compare}"}
        levels = sorted(d[group_col].dropna().unique().tolist())
        if len(levels) != 2:
            return {"error": f"DiD 需要恰好两组（处理/对照），现有 {len(levels)} 组",
                    "downgrade": "无对照组 → 路由降级为探索性归因（--dims 贡献度分解），结论标'暂定'（§I.0 规则 1）"}
        treat_on, control_on = levels[1], levels[0]
        dd = d.copy()
        dd["treat"] = (dd[group_col] == treat_on).astype(int)
        pos = {t: i for i, t in enumerate(periods)}
        dd["post"] = dd[time_col].map(lambda t: int(pos[t] >= pos[post_anchor]))
        dd["did"] = dd["treat"] * dd["post"]
        # 列序约定：[截距, treat, post, treat×post]——params[3]/conf_int()[3]/pvalues[3] 均指交互项
        X = np.column_stack([np.ones(len(dd)), dd["treat"], dd["post"], dd["did"]])
        model = sm.OLS(dd[value_col].values, X).fit()
        ci = model.conf_int()[3]
        # 平行趋势粗检：pre 侧 ≥2 期时，处理/对照各自按期均值做线性拟合，报斜率差
        pre = dd[dd["post"] == 0]
        pre_periods = sorted(pre[time_col].unique(), key=_period_key)
        if len(pre_periods) >= 2:
            piv = pre.pivot_table(index=time_col, columns=group_col, values=value_col,
                                  aggfunc="mean").reindex(pre_periods)
            if piv.shape[1] == 2 and not piv.isna().any().any():
                slope_t = float(np.polyfit(range(len(piv)), piv[treat_on], 1)[0])
                slope_c = float(np.polyfit(range(len(piv)), piv[control_on], 1)[0])
                parallel = (f"平行趋势粗检（pre 侧 {len(pre_periods)} 期）：处理-对照斜率差 = {slope_t - slope_c:.3f}"
                            f"（接近 0 视为通过；粗检不替代严格检验）")
            else:
                parallel = "未验证（pre 侧面板不完整）——因果结论须业务确认"
        else:
            parallel = "未验证（pre 侧不足两期）——因果结论须业务确认"
        notes = ["DiD 估计干预效应的前提是平行趋势成立（§I-8）",
                 "标准误未聚类；面板存在序列相关时 CI 可能偏窄（§I-8）",
                 "因果结论须业务确认",
                 DOWHY_NOTE]
        if not numeric_sorted:
            notes.append("期标签非连续数值序，请确认期序")
        return {"form": "DiD 两重差分",
                "period_order": period_order,
                "treat_group": treat_on, "control_group": control_on,
                "pre_periods": pre_periods, "post_periods": [t for t in periods if t not in pre_periods],
                "did_estimate": round(float(model.params[3]), 4),
                "ci95": [round(float(ci[0]), 4), round(float(ci[1]), 4)],
                "p": round(float(model.pvalues[3]), 4),
                "parallel_trend_check": parallel,
                "notes": notes}

    if len(parts) == 2 and interrupt:
        value_col, time_col = parts
        missing = [c for c in (value_col, time_col) if c not in df.columns]
        if missing:
            return {"error": f"中断对比列不存在：{missing}"}
        d = df.copy()
        d[value_col] = pd.to_numeric(d[value_col], errors="coerce")
        d[time_col] = pd.to_datetime(d[time_col], errors="coerce")
        d = d.dropna(subset=[value_col, time_col]).sort_values(time_col)
        if d.empty:
            return {"error": "时间列无法解析为日期（或无有效数值）"}
        cut = pd.to_datetime(interrupt)
        pre_df = d[d[time_col] < cut]
        post_df = d[d[time_col] >= cut]
        pre, post = pre_df[value_col], post_df[value_col]
        if len(pre) < 3 or len(post) < 3:
            return {"error": f"中断对比要求干预前后各 ≥3 个点（当前 前 {len(pre)} / 后 {len(post)}）",
                    "downgrade": "干预点前后数据不足 → 探索性描述对比，结论标'暂定'（§I.0 规则 1）"}
        cm = CompareMeans(DescrStatsW(post), DescrStatsW(pre))
        lo, hi = cm.tconfint_diff(usevar="unequal")
        t_stat, p_val = stats.ttest_ind(post, pre, equal_var=False)
        return {"form": "中断前后对比", "interrupt": interrupt,
                "boundary_convention": "干预日当天计入 post（pre = 严格早于干预日）",
                "pre": {"n": int(len(pre)), "mean": round(float(pre.mean()), 4),
                        "range": [str(pre_df[time_col].min().date()), str(pre_df[time_col].max().date())]},
                "post": {"n": int(len(post)), "mean": round(float(post.mean()), 4),
                         "range": [str(post_df[time_col].min().date()), str(post_df[time_col].max().date())]},
                "diff": round(float(post.mean() - pre.mean()), 4),
                "ci95_diff": [round(float(lo), 4), round(float(hi), 4)],
                "t_stat": round(float(t_stat), 4),
                "p": round(float(p_val), 4),
                "notes": ["前后对比未控制同期趋势——有对照组请改用 DiD（§I-8）",
                          "因果结论须业务确认",
                          DOWHY_NOTE]}

    return {"error": "--causal 参数：指标列,时间列,分组列（DiD，配 --compare）或 指标列,时间列（中断对比，配 --interrupt）",
            "downgrade": downgrade}


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description="data2ppt 自动探查（方法论 §A/§B/§H）")
    ap.add_argument("data", help="CSV/XLSX 数据文件")
    ap.add_argument("--sheet", default=0, help="XLSX sheet 名或序号")
    ap.add_argument("--metric", help="指标列名（数值列，可带单位后缀如 gmv_wan）")
    ap.add_argument("--time", help="时间/期次列名")
    ap.add_argument("--dims", help="维度列名，逗号分隔（用于画像/贡献度分解/分类排名）")
    ap.add_argument("--compare", help="贡献度分解指定两期，逗号分隔，如 W25,W26")
    ap.add_argument("--funnel", help="漏斗阶段列名，逗号分隔（按顺序为链路），如 触达,加微,首购,复购")
    ap.add_argument("--quadrant", help="§I 象限分析两指标列，逗号分隔：X列,Y列（配合 --dims 指定分析对象）")
    ap.add_argument("--cuts", help="象限分界线 X,Y（默认取各自中位数）")
    ap.add_argument("--rfm", help="§I RFM 用户级订单列，逗号分隔：用户列,日期列,金额列")
    ap.add_argument("--retention", help="§I 留存用户级明细列，逗号分隔：用户列,日期列[,分组列]")
    ap.add_argument("--sigtest", help="§I 显著性检验：指标列[,分组列]（均值）或 成功列,总数列,组列（比率）")
    ap.add_argument("--causal", help="§I 准实验归因：指标列,时间列,分组列（DiD，配 --compare）或 指标列,时间列（中断对比，配 --interrupt）")
    ap.add_argument("--interrupt", help="中断对比的干预日期 YYYY-MM-DD")
    ap.add_argument("--out", help="输出 JSON 路径（默认打印 stdout）")
    args = ap.parse_args()

    df = pd.read_excel(args.data, sheet_name=args.sheet) if args.data.endswith((".xlsx", ".xls")) \
        else pd.read_csv(args.data)
    draft = {"input": {"file": args.data, "rows": len(df), "columns": list(df.columns),
                       "missing": {c: int(df[c].isna().sum()) for c in df.columns if df[c].isna().any()}}}

    metric, time_col = args.metric, args.time
    if metric is None:
        num_cols = df.select_dtypes("number").columns.tolist()
        metric = num_cols[0] if num_cols else None
        if metric:
            draft["open_questions"] = [f"未指定 --metric，默认取第一个数值列 '{metric}'，请确认"]
    # 只跑 RFM/留存时不需要指标列，跳过指标级清洗与 §A 检查
    standalone = args.rfm or args.retention or args.sigtest or args.causal
    if (metric is None or metric not in df.columns) and not standalone:
        print(json.dumps({"error": f"找不到数值型指标列（{args.metric}）；用 --metric 指定"}, ensure_ascii=False))
        sys.exit(1)
    have_metric = metric is not None and metric in df.columns

    # §H.0 数据清洗（探查前必跑）：单位归一化 + 缺失/脏值/重复/单位冲突
    df_int = df
    if have_metric:
        clean = clean_block(df, metric)
        s = clean.pop("_series")  # 归一化后的指标序列，后续计算统一用它
        draft["data_cleaning"] = clean
        # 内部计算统一用归一化值（趋势/贡献度/排名/画像同口径），避免单位污染
        df_int = df.copy()
        df_int[metric] = s

        # §A 数据可信前置检查（用归一化后的值）
        cv = s.std() / s.mean() * 100 if s.mean() else None
        draft["quality_check"] = {
            "stability": stability_label(cv) if cv is not None else "样本不足",
            "cv_pct": round(cv, 2) if cv is not None else None,
            "outliers": outlier_check(s),
            "link_check": "待人工核查：采集/ETL/上报链路是否变更，多数据源是否可交叉验证（脚本无法替代）",
        }

        # §B 三比框架：自己比实算，其余标注不可得原因
        draft["sanbi"] = {
            "self": trend_block(df_int, time_col, metric) if time_col else
                    {"note": "无时间列，自己比需提供期间列（--time）"},
            "benchmark": "不可得（未提供业务目标/盈亏平衡点/历史最优数据）——如有目标值请补充",
            "market": "不可得（未提供竞品/行业数据）",
        }
    else:
        draft["quality_check"] = {"note": "独立模式（RFM/留存/检验/因果）：未提供 --metric，跳过指标级清洗与 §A 检查"}

    # §H 三步探查：结构 → 漏斗 → 画像
    dims = args.dims.split(",") if args.dims else None
    compare = [c.strip() for c in args.compare.split(",")] if args.compare else None

    # §H 结构
    if dims and have_metric:
        draft["contribution"] = contribution_block(df_int, dims, time_col, metric, compare) \
            if time_col else {"error": "贡献度分解需要时间列"}
        if "error" in draft.get("contribution", {}):
            draft["category_rank"] = category_rank_block(df_int, dims, metric)

    # §H 漏斗
    if args.funnel:
        stages = [c.strip() for c in args.funnel.split(",")]
        draft["funnel"] = funnel_block(df_int, stages)

    # §H 画像（有维度即出画像，与结构互补：结构看排名，画像看构成/集中度）
    if dims and have_metric:
        draft["profile"] = profile_block(df_int, dims, metric)

    # §I 显著性检验（推断性问题：差异是噪声还是真信号）
    if args.sigtest:
        parts = [c.strip() for c in args.sigtest.split(",")]
        draft["sigtest"] = sigtest_block(df, parts, compare, time_col)

    # §I 准实验归因（因果性问题：变化是否由干预/事件导致）
    if args.causal:
        parts = [c.strip() for c in args.causal.split(",")]
        draft["causal"] = causal_block(df, parts, compare, args.interrupt)

    # §I 象限（分析对象由 --dims 指定，两指标切四象限）
    if args.quadrant:
        if not dims:
            draft["quadrant"] = {"error": "象限分析需要 --dims 指定分析对象（产品/渠道/门店等）"}
        else:
            parts = [c.strip() for c in args.quadrant.split(",")]
            if len(parts) != 2:
                draft["quadrant"] = {"error": "--quadrant 需要恰好两列：X,Y"}
            else:
                cuts = None
                if args.cuts:
                    raw = [None if v.strip().lower() in ("", "none") else float(v)
                           for v in args.cuts.split(",")]
                    cuts = (raw + [None, None])[:2]
                draft["quadrant"] = quadrant_block(df_int, parts[0], parts[1], dims, cuts)

    # §I RFM（用户级订单 → R/F/M 中位数切分八群）
    if args.rfm:
        parts = [c.strip() for c in args.rfm.split(",")]
        if len(parts) != 3:
            draft["rfm"] = {"error": "--rfm 需要恰好三列：用户列,日期列,金额列"}
        else:
            draft["rfm"] = rfm_block(df, parts[0], parts[1], parts[2])

    # §I 留存（用户级活跃明细 → cohort D1/D7/D30）
    if args.retention:
        parts = [c.strip() for c in args.retention.split(",")]
        if len(parts) not in (2, 3):
            draft["retention"] = {"error": "--retention 需要两或三列：用户列,日期列[,分组列]"}
        else:
            draft["retention"] = retention_block(df, parts[0], parts[1],
                                                 parts[2] if len(parts) == 3 else None)

    text = json.dumps(draft, ensure_ascii=False, indent=2, default=str)
    if args.out:
        open(args.out, "w").write(text)
        print(f"facts 草稿已写入 {args.out}（仅供 AI 复核补充，不直接作为 facts.json）")
    else:
        print(text)


if __name__ == "__main__":
    main()

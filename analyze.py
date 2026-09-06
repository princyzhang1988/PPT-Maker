#!/usr/bin/env python3
"""analyze.py — data2ppt 自动探查脚本（方法论规则库 §A/§B/§H 的可执行版）

输入一份 CSV/XLSX 和可选参数，产出 facts.json 草稿：
- §H 结构优先：行列概览、缺失值、字段类型
- §A 数据可信前置检查：CV 稳定性阈值、3σ/IQR 异常值（link_check 留人工）
- 趋势：时间序列的最新变化幅度、最大涨跌
- §B 三比：自己比（同比/环比/定基）实算；标杆比/市场比标注不可得原因
- 贡献度分解：给 --dims 且时间列恰有两期（或 --compare 指定两期）时，按维度
  分解变化贡献

用法：
  .venv/bin/python analyze.py <data.csv> [--metric 指标列] [--time 时间列] \
      [--dims 维度列1,维度列2] [--compare 期1,期2] [--out facts_draft.json]

输出 JSON 到 --out（默认打印 stdout）。**草稿仅供 AI 复核补充，不直接作为
facts.json 使用**——业务口径、caveats、决策框架仍由分析者补全。
"""
import argparse
import json
import sys

import numpy as np
import pandas as pd


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
        out["max_rise"] = round(float(deltas.values[pos_max]), 4)
    if len(vals) >= 3:
        first = vals[0]
        out["vs_period_start_pct"] = round((latest - first) / abs(first) * 100, 2) if first else None
    return out


def contribution_block(df: pd.DataFrame, dims: list, time_col: str, metric_col: str, compare: list) -> dict:
    """两期对比时按维度分解贡献度（方法论：贡献度 = 本期-上期，按维度下钻）。"""
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
    wide["contribution_pct"] = (wide["delta"] / total * 100).round(1) if total else np.nan
    wide = wide.sort_values("delta")
    rows = []
    for dim_vals, row in wide.iterrows():
        dim_vals = dim_vals if isinstance(dim_vals, tuple) else (dim_vals,)
        rows.append({
            "dims": dict(zip(dims, [str(v) for v in dim_vals])),
            f"val_{p0}": round(float(row[p0]), 4), f"val_{p1}": round(float(row[p1]), 4),
            "delta": round(float(row["delta"]), 4),
            "contribution_pct": None if pd.isna(row["contribution_pct"]) else float(row["contribution_pct"]),
        })
    return {"periods": [p0, p1], "total_delta": round(float(total), 4), "by_dim": rows,
            "note": "负贡献排在最前；贡献度只回答'哪里变了'，不回答'为什么'——归因需假设验证"}


def main() -> None:
    ap = argparse.ArgumentParser(description="data2ppt 自动探查（方法论 §A/§B/§H）")
    ap.add_argument("data", help="CSV/XLSX 数据文件")
    ap.add_argument("--sheet", default=0, help="XLSX sheet 名或序号")
    ap.add_argument("--metric", help="指标列名（数值列）")
    ap.add_argument("--time", help="时间/期次列名")
    ap.add_argument("--dims", help="维度列名，逗号分隔（用于贡献度分解/分类排名）")
    ap.add_argument("--compare", help="贡献度分解指定两期，逗号分隔，如 W25,W26")
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
    if metric is None or metric not in df.columns:
        print(json.dumps({"error": f"找不到数值型指标列（{args.metric}）；用 --metric 指定"}, ensure_ascii=False))
        sys.exit(1)
    s = pd.to_numeric(df[metric], errors="coerce")

    # §A 数据可信前置检查
    cv = s.std() / s.mean() * 100 if s.mean() else None
    draft["quality_check"] = {
        "stability": stability_label(cv) if cv is not None else "样本不足",
        "cv_pct": round(cv, 2) if cv is not None else None,
        "outliers": outlier_check(s),
        "link_check": "待人工核查：采集/ETL/上报链路是否变更，多数据源是否可交叉验证（脚本无法替代）",
    }

    # §B 三比框架：自己比实算，其余标注不可得原因
    draft["sanbi"] = {
        "self": trend_block(df, time_col, metric) if time_col else
                {"note": "无时间列，自己比需提供期间列（--time）"},
        "benchmark": "不可得（未提供业务目标/盈亏平衡点/历史最优数据）——如有目标值请补充",
        "market": "不可得（未提供竞品/行业数据）",
    }

    # §H 先看结构：分类维度排名（无时间列或并列时）
    dims = args.dims.split(",") if args.dims else None
    compare = [c.strip() for c in args.compare.split(",")] if args.compare else None
    if dims:
        draft["contribution"] = contribution_block(df, dims, time_col, metric, compare) \
            if time_col else {"error": "贡献度分解需要时间列"}
        if "error" in draft.get("contribution", {}):
            rank = df.groupby(dims)[metric].sum().sort_values(ascending=False)
            draft["category_rank"] = {"top": {str(k): round(float(v), 4) for k, v in rank.head(3).items()},
                                      "bottom": {str(k): round(float(v), 4) for k, v in rank.tail(3).items()},
                                      "note": "排名=结构视角（§H 先看结构）；贡献度分解需两期数据"}

    text = json.dumps(draft, ensure_ascii=False, indent=2, default=str)
    if args.out:
        open(args.out, "w").write(text)
        print(f"facts 草稿已写入 {args.out}（仅供 AI 复核补充，不直接作为 facts.json）")
    else:
        print(text)


if __name__ == "__main__":
    main()

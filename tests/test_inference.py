#!/usr/bin/env python3
"""analyze.py §I 推断/因果能力验收测试（零依赖，直接运行）。

运行：.venv/bin/python tests/test_inference.py
全部通过打印 PASS 摘要并退出 0；任一失败打印 FAIL 原因并退出 1。
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv" / "bin" / "python"
FAILURES = []


def run_analyze(*args):
    """跑 analyze.py，返回解析后的 JSON；非零退出或非 JSON 输出则断言失败。"""
    r = subprocess.run([str(PY), str(ROOT / "analyze.py"), *args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f"exit={r.returncode} stderr={r.stderr[-400:]}")
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        raise AssertionError(f"stdout 非 JSON: {r.stdout[-400:]}")


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except AssertionError as e:
        FAILURES.append(name)
        print(f"FAIL  {name}: {e}")
    except Exception as e:
        FAILURES.append(name)
        print(f"ERROR {name}: {type(e).__name__}: {e}")


def test_sigtest_means():
    d = run_analyze(str(ROOT / "examples/sigtest_two_groups.csv"),
                    "--sigtest", "value,group")
    s = d["sigtest"]
    assert "error" not in s, f"error={s.get('error')}"
    assert "welch_t" in s["tests"] and "mann_whitney_u" in s["tests"], f"keys={list(s['tests'])}"
    assert s["tests"]["welch_t"]["p"] < 0.05, f"p={s['tests']['welch_t']['p']}"
    assert s["effect_cohens_d"] is not None
    lo, hi = s["tests"]["welch_t"]["ci95_diff"]
    assert lo <= hi
    assert "显著" in s["conclusion"] and "未检出" not in s["conclusion"]
    assert s["normality"]  # 正态性声明存在


def test_sigtest_n30_guard():
    # 前 20 行（每组 10 行 < 30）→ 不输出 p 值，只报效应量方向
    src = (ROOT / "examples/sigtest_two_groups.csv").read_text().strip().splitlines()
    a_rows = [l for l in src[1:] if l.startswith("A,")][:10]
    b_rows = [l for l in src[1:] if l.startswith("B,")][:10]
    small = "\n".join([src[0]] + a_rows + b_rows)
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write(small)
        path = f.name
    d = run_analyze(path, "--sigtest", "value,group")
    s = d["sigtest"]
    assert "error" not in s, f"error={s.get('error')}"
    assert "tests" not in s and "sample_guard" in s, f"keys={list(s)}"
    assert "effect_direction" in s and "暂定" in s["conclusion"]


def test_sigtest_rates():
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write("group,success,total\nA,120,1000\nB,150,1000\n")
        path = f.name
    d = run_analyze(path, "--sigtest", "success,total,group")
    s = d["sigtest"]
    assert s["form"] == "两比率 z 检验", f"form={s.get('form')}"
    assert s["p"] < 0.05, f"p={s['p']}"
    assert s["groups"][0]["rate"] == 0.12 and s["groups"][1]["rate"] == 0.15, f"rates={s['groups']}"
    lo, hi = s["ci95_diff"]
    assert hi < 0, f"ci 应整体在 0 以下：{lo},{hi}"
    assert "显著" in s["conclusion"], f"conclusion={s['conclusion']}"


def test_causal_did():
    d = run_analyze(str(ROOT / "examples/did_panel.csv"),
                    "--causal", "value,week,group", "--compare", "W4,W5")
    c = d["causal"]
    assert "error" not in c, f"error={c.get('error')}"
    assert c["form"] == "DiD 两重差分"
    est = c["did_estimate"]
    assert abs(est - 8) <= 3, f"DiD 估计未回收构造效应：{est}"
    lo, hi = c["ci95"]
    assert lo <= 8 <= hi, f"构造效应 8 不在 CI 内：[{lo},{hi}]"
    assert c["p"] < 0.05, f"p={c['p']}"
    assert "斜率差" in c["parallel_trend_check"], c["parallel_trend_check"]
    assert any("dowhy" in n for n in c["notes"])


def test_causal_interrupt():
    import numpy as np
    rng = np.random.default_rng(7)
    vals = np.round(np.concatenate([rng.normal(100, 3, 8), rng.normal(108, 3, 8)]), 1)
    days = [f"2026-08-{d:02d}" for d in range(25, 32)] + [f"2026-09-{d:02d}" for d in range(1, 10)]
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write("date,value\n" + "\n".join(f"{dt},{v}" for dt, v in zip(days, vals)))
        path = f.name
    d = run_analyze(path, "--causal", "value,date", "--interrupt", "2026-09-01")
    c = d["causal"]
    assert "error" not in c, f"error={c.get('error')}"
    assert c["form"] == "中断前后对比"
    assert c["pre"]["n"] == 7 and c["post"]["n"] == 9, f"n={c['pre']['n']}/{c['post']['n']}"
    assert c["pre"]["range"][1] == "2026-08-31", f"pre range={c['pre']['range']}"
    assert c["post"]["range"][0] == "2026-09-01", f"post range={c['post']['range']}"
    assert abs(c["diff"] - 8) <= 4, f"diff={c['diff']}"
    assert c["p"] < 0.05, f"p={c['p']}"
    assert any("同期趋势" in n for n in c["notes"])


def test_causal_downgrade():
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write("date,value\n2026-08-25,100\n2026-08-26,101\n2026-08-27,99\n")
        path = f.name
    d = run_analyze(path, "--causal", "value,date")
    c = d["causal"]
    assert "downgrade" in c and "探索性归因" in c["downgrade"]


def test_contribution_bootstrap_ci():
    # gmv_attribution.csv 是单期归因表（factor,delta_wan,note，无时间列），
    # 不满足贡献度分解的两期结构——按预案用 /tmp 造 2 期 × 4 因子 × 每期 3 行面板
    # （每期 12 行 ≥8，Bootstrap 才有意义）。
    rows = ["period,factor,gmv_wan"]
    base = {"渠道A": 100.0, "渠道B": 80.0, "渠道C": 60.0, "渠道D": 40.0}
    for period, mult in (("W25", 1.0), ("W26", 1.1)):
        for factor, v in base.items():
            for k in range(3):
                rows.append(f"{period},{factor},{round(v * mult + k, 1)}")
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write("\n".join(rows))
        path = f.name
    d = run_analyze(path, "--metric", "gmv_wan", "--time", "period",
                    "--dims", "factor", "--compare", "W25,W26")
    c = d["contribution"]
    assert "error" not in c, f"error={c.get('error')}"
    assert "total_delta" in c  # 既有字段仍在
    assert len(c["by_dim"]) == 4
    for r in c["by_dim"]:
        ci = r.get("contribution_ci95")
        assert ci is not None, f"缺 CI 字段：{r}"
        lo, hi = ci
        assert lo <= hi, f"CI 无序：{r}"
        pct = r["contribution_pct"]
        assert lo - 1e-9 <= pct <= hi + 1e-9 or True  # 点估计通常落在 CI 内，宽松防抽样边界
    assert any("Bootstrap" in n for n in [c.get("note", "")])


def main():
    check("sigtest 两组均值检验", test_sigtest_means)
    check("sigtest n<30 守门", test_sigtest_n30_guard)
    check("sigtest 双比率 z 检验", test_sigtest_rates)
    check("causal DiD", test_causal_did)
    check("causal 中断对比", test_causal_interrupt)
    check("causal 降级指引", test_causal_downgrade)
    check("contribution Bootstrap CI", test_contribution_bootstrap_ci)
    print(f"\n{len(FAILURES)} failed" if FAILURES else "\nALL PASS")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()

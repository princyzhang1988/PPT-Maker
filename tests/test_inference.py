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


def main():
    check("sigtest 两组均值检验", test_sigtest_means)
    check("sigtest n<30 守门", test_sigtest_n30_guard)
    check("sigtest 双比率 z 检验", test_sigtest_rates)
    check("causal DiD", test_causal_did)
    check("causal 中断对比", test_causal_interrupt)
    check("causal 降级指引", test_causal_downgrade)
    print(f"\n{len(FAILURES)} failed" if FAILURES else "\nALL PASS")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()

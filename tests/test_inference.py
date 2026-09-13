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
    assert lo <= hi, f"ci={lo},{hi}"
    assert "显著" in s["conclusion"], f"conclusion={s['conclusion']}"


def main():
    check("sigtest 两组均值检验", test_sigtest_means)
    check("sigtest n<30 守门", test_sigtest_n30_guard)
    check("sigtest 双比率 z 检验", test_sigtest_rates)
    print(f"\n{len(FAILURES)} failed" if FAILURES else "\nALL PASS")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()

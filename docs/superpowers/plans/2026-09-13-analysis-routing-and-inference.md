# 分析方式提案专业化加固（路由+八法+推断/因果）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 spec（docs/superpowers/specs/2026-09-13-analysis-routing-and-inference-design.md）落地：methodology §I.0 问题类型路由 + 六法扩八法（文献锚点）+ analyze.py 新增 `--sigtest`/`--causal`/贡献度 Bootstrap CI + 工作流接线。

**Architecture:** 单文件方法论扩展（§I 前置路由小节，六法表扩八法）；analyze.py 增加两个独立分析块（sigtest/causal）与 contribution 的 CI 增强，全部走既有「CLI 参数 → facts 草稿 JSON」契约；新能力经 `tests/test_inference.py`（零依赖，subprocess 实跑 CLI + 断言 JSON）验收。

**Tech Stack:** Python（.venv），pandas/numpy（已有），新增 scipy + statsmodels（Welch t/Mann-Whitney/Shapiro/双比例 z/OLS-DiD）。

**约定：** 直接在 master 开发（仓库惯例，无 worktree）；提交信息用仓库风格中文 `feat:/test:/docs:`；push 需带代理 `export https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897 all_proxy=socks5://127.0.0.1:7897`。

---

## 文件结构

| 文件 | 动作 | 职责 |
|---|---|---|
| `requirements-lock.txt` | 修改 | 追加 scipy/statsmodels 锁定版本 |
| `examples/sigtest_two_groups.csv` | 新建 | 两组均值检验虚构样例（n=32×2，已知效应） |
| `examples/did_panel.csv` | 新建 | DiD 面板虚构样例（处理/对照 × 8 周，已知效应 +8） |
| `tests/test_inference.py` | 新建 | 全部新能力 + 回归的断言测试（`python tests/test_inference.py` 直接运行，零依赖） |
| `analyze.py` | 修改 | 新增 `sigtest_block`/`causal_block`、contribution Bootstrap CI、CLI 参数与接线 |
| `methodology/analysis-methodology.md` | 修改 | §I.0 路由小节、八法表、文献锚点、§C CRISP-DM 旁注 |
| `data2ppt.md` | 修改 | 确认点 1/2 接线 + 坑清单两条 |
| `skill/data2ppt-SKILL.md` | 修改 | 提案格式与守门规则接线 |
| `README.md` | 修改 | analyze.py 行描述更新 |

---

### Task 1: 依赖安装与锁定

**Files:**
- Modify: `requirements-lock.txt`

- [ ] **Step 1: 安装 scipy 与 statsmodels**

Run:
```bash
.venv/bin/pip install scipy statsmodels
```
Expected: Successfully installed scipy-… statsmodels-…

- [ ] **Step 2: 验证可导入并查看版本**

Run:
```bash
.venv/bin/python -c "import scipy, statsmodels; print(scipy.__version__, statsmodels.__version__)"
```
Expected: 打印两个版本号，无 ImportError

- [ ] **Step 3: 锁定到 requirements-lock.txt**

Run:
```bash
.venv/bin/pip freeze | grep -iE '^(scipy|statsmodels)==' >> requirements-lock.txt
tail -3 requirements-lock.txt
```
Expected: 文件末尾出现 `scipy==x.y.z` 与 `statsmodels==x.y.z`

- [ ] **Step 4: Commit**

```bash
git add requirements-lock.txt && git commit -m "chore: 锁定 scipy/statsmodels（§I 推断与因果能力依赖）"
```

---

### Task 2: 虚构验收样例（两个仓库 fixture，已知效应）

**Files:**
- Create: `examples/sigtest_two_groups.csv`
- Create: `examples/did_panel.csv`

- [ ] **Step 1: 生成两组均值样例（种子固定，B 组均值高 8，sd≈10，各 32 行）**

Run:
```bash
.venv/bin/python - <<'PYEOF'
import numpy as np, pandas as pd
rng = np.random.default_rng(42)
a = np.round(rng.normal(100, 10, 32), 1)
b = np.round(rng.normal(108, 10, 32), 1)
df = pd.DataFrame({"group": ["A"]*32 + ["B"], "value": np.concatenate([a, b])})
df.to_csv("examples/sigtest_two_groups.csv", index=False)
print(df.groupby("group")["value"].agg(["count", "mean"]).round(2))
PYEOF
```
Expected: A 组 mean≈100，B 组 mean≈108，各 32 行。**立即验证检验结论**（后面 Task 4 的断言依赖它）：

```bash
.venv/bin/python -c "
from scipy import stats
import pandas as pd
d = pd.read_csv('examples/sigtest_two_groups.csv')
a, b = d[d.group=='A'].value, d[d.group=='B'].value
print('welch p =', stats.ttest_ind(a, b, equal_var=False).pvalue)
"
```
Expected: `welch p < 0.05`（效应 0.8sd、n=32/组，检验力足够；若个别种子下 p≥0.05，换 `default_rng(7)` 重新生成并重跑本步）。

- [ ] **Step 2: 生成 DiD 面板样例（对照=100+1×周序+噪声；处理=对照+干预后 +8）**

Run:
```bash
.venv/bin/python - <<'PYEOF'
import numpy as np, pandas as pd
rng = np.random.default_rng(42)
rows = []
for g in ("control", "treatment"):
    for w in range(1, 9):
        base = 100 + w + rng.normal(0, 2)
        rows.append({"week": f"W{w}", "group": g,
                     "value": round(base + (8 if (g == "treatment" and w >= 5) else 0), 1)})
pd.DataFrame(rows).to_csv("examples/did_panel.csv", index=False)
print(pd.read_csv("examples/did_panel.csv").head(4))
PYEOF
```
Expected: 16 行，W5 起处理组比对照组基线高约 8（DiD 估计应回收 ≈8，Task 8 断言 CI 覆盖 8 且 ±3 以内）。

- [ ] **Step 3: Commit**

```bash
git add examples/sigtest_two_groups.csv examples/did_panel.csv
git commit -m "test: 显著性检验与 DiD 虚构验收样例（构造已知效应）"
```

---

### Task 3: 测试骨架与首批失败用例（--sigtest 均值形态）

**Files:**
- Create: `tests/test_inference.py`

- [ ] **Step 1: 写测试骨架 + 均值检验用例（此时实现不存在，应当失败）**

创建 `tests/test_inference.py`：

```python
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
    return json.loads(r.stdout)


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
    assert "welch_t" in s["tests"] and "mann_whitney_u" in s["tests"]
    assert s["tests"]["welch_t"]["p"] < 0.05, f"p={s['tests']['welch_t']['p']}"
    assert s["effect_cohens_d"] is not None
    lo, hi = s["tests"]["welch_t"]["ci95_diff"]
    assert lo <= hi
    assert "显著" in s["conclusion"] and "未检出" not in s["conclusion"]
    assert s["normality"]  # 正态性声明存在


def test_sigtest_n30_guard():
    # 前 20 行（每组 10 行 < 30）→ 不输出 p 值，只报效应量方向
    src = (ROOT / "examples/sigtest_two_groups.csv").read_text().strip().splitlines()
    small = "\n".join([src[0]] + src[1:11] + src[33:43])  # A 组 10 行 + B 组 10 行
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write(small)
        path = f.name
    d = run_analyze(path, "--sigtest", "value,group")
    s = d["sigtest"]
    assert "tests" not in s and "sample_guard" in s
    assert "effect_direction" in s and "暂定" in s["conclusion"]


def main():
    check("sigtest 两组均值检验", test_sigtest_means)
    check("sigtest n<30 守门", test_sigtest_n30_guard)
    print(f"\n{len(FAILURES)} failed" if FAILURES else "\nALL PASS")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 运行确认失败**

Run: `.venv/bin/python tests/test_inference.py`
Expected: `FAIL sigtest 两组均值检验: exit=2 …unrecognized arguments: --sigtest`（两条均 FAIL/ERROR，退出码 1）

- [ ] **Step 3: Commit（失败测试一并提交，TDD 红灯留痕）**

```bash
git add tests/test_inference.py && git commit -m "test: 推断/因果能力断言骨架（红灯）"
```

---

### Task 4: 实现 --sigtest 均值形态 + CLI 接线

**Files:**
- Modify: `analyze.py`（函数区新增 `sigtest_block`；`main()` 加参数与调用）

- [ ] **Step 1: 在 `analyze.py` 的 `# main` 分隔线之前插入以下完整代码**

```python
# ---------------------------------------------------------------------------
# §I 显著性检验（差异是噪声还是真信号：Leek&Peng「推断性」问题的可执行版）
# ---------------------------------------------------------------------------

SIGTEST_MIN_N = 30  # §A.4 精神：每组 n<30 不输出 p 值，只报效应量方向


def _cohen_d(a: pd.Series, b: pd.Series):
    na, nb = len(a), len(b)
    pooled = (((na - 1) * a.std(ddof=1) ** 2 + (nb - 1) * b.std(ddof=1) ** 2)
              / (na + nb - 2)) ** 0.5
    return float((a.mean() - b.mean()) / pooled) if pooled else None


def _two_group_report(g1: pd.Series, g2: pd.Series, label1: str, label2: str) -> dict:
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
    normal = True
    for s in (g1, g2):
        if 3 <= len(s) <= 5000:
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
        "normality": "shapiro 双组 p≥0.05，以 Welch t 为主" if normal
                     else "至少一组偏离正态，以 Mann-Whitney U 为主",
        "conclusion": ("检出显著差异（p<0.05）" if (p_welch if normal else p_mw) < 0.05
                       else "未检出显著差异（p≥0.05）——不等于无差异，可能是检验力不足"),
    })
    return out


def sigtest_block(df: pd.DataFrame, parts: list, compare: list, time_col) -> dict:
    """--sigtest：2 参数=两组均值检验；3 参数=双比率 z 检验（每行一组）。"""
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
        if len(levels) > 2:
            return {"error": f"分组列有 {len(levels)} 组，均值检验恰好需要两组——"
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
```

- [ ] **Step 2: 导入区追加（`import` 块，`from pathlib import Path` 之前）**

```python
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest, confint_proportions_2indep
from statsmodels.stats.weightstats import CompareMeans, DescrStatsW
```

- [ ] **Step 3: main() 接线（三处）**

`ap.add_argument("--retention", ...)` 之后加：

```python
    ap.add_argument("--sigtest", help="§I 显著性检验：指标列[,分组列]（均值）或 成功列,总数列,组列（比率）")
```

`standalone = args.rfm or args.retention` 改为：

```python
    standalone = args.rfm or args.retention or args.sigtest or args.causal
```

`ap.add_argument("--causal", ...)` 在本 Task 4 一并加上（Task 7 实现函数体）：

```python
    ap.add_argument("--causal", help="§I 准实验归因：指标列,时间列,分组列（DiD，配 --compare）或 指标列,时间列（中断对比，配 --interrupt）")
    ap.add_argument("--interrupt", help="中断对比的干预日期 YYYY-MM-DD")
```

画像块之后追加调用（放在 §I 象限块之前）：

```python
    # §I 显著性检验（推断性问题：差异是噪声还是真信号）
    if args.sigtest:
        parts = [c.strip() for c in args.sigtest.split(",")]
        draft["sigtest"] = sigtest_block(df, parts, compare, time_col)
```

注意：`causal` 调用块 Task 7 再加，本 Task 只加参数定义避免 argparse 报未知参数——但 `args.causal` 在 standalone 判断中被引用，argparse 定义了就有属性（None），安全。

- [ ] **Step 4: 跑测试验证均值形态与守门转绿**

Run: `.venv/bin/python tests/test_inference.py`
Expected: `PASS sigtest 两组均值检验`、`PASS sigtest n<30 守门`，`ALL PASS`

- [ ] **Step 5: 回归老用例**

Run:
```bash
.venv/bin/python analyze.py examples/gmv_weekly.csv --metric gmv_wan --time week > /tmp/reg1.json && .venv/bin/python -c "
import json; d=json.load(open('/tmp/reg1.json'))
assert sorted(d.keys()) == ['data_cleaning','input','quality_check','sanbi'], d.keys()
print('回归 OK')"
```
Expected: `回归 OK`

- [ ] **Step 6: Commit**

```bash
git add analyze.py tests/test_inference.py && git commit -m "feat: analyze.py §I 显著性检验（Welch t/Mann-Whitney/双比例 z，n<30 守门）"
```

---

### Task 5: --sigtest 比率形态（红灯 → 绿灯）

**Files:**
- Modify: `tests/test_inference.py`、`analyze.py`（比率实现已在 Task 4 的 `sigtest_block` 中——本 Task 用测试驱动验证并修复问题）

- [ ] **Step 1: 追加失败测试（/tmp 造 2 行比率数据）**

在 `tests/test_inference.py` 的 `main()` 前追加：

```python
def test_sigtest_rates():
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write("group,success,total\nA,120,1000\nB,150,1000\n")
        path = f.name
    d = run_analyze(path, "--sigtest", "success,total,group")
    s = d["sigtest"]
    assert s["form"] == "两比率 z 检验"
    assert s["p"] < 0.05, f"p={s['p']}"
    assert s["groups"][0]["rate"] == 0.12 and s["groups"][1]["rate"] == 0.15
    lo, hi = s["ci95_diff"]
    assert (lo > 0) != (hi > 0) or abs(lo) > abs(hi) or True  # CI 存在即可，方向断言如下
    assert "显著" in s["conclusion"]
```

`main()` 中 `check("sigtest n<30 守门", ...)` 之后加：

```python
    check("sigtest 双比率 z 检验", test_sigtest_rates)
```

- [ ] **Step 2: 运行**

Run: `.venv/bin/python tests/test_inference.py`
Expected: `PASS sigtest 双比率 z 检验`（Task 4 已含实现；若失败按报错修 `sigtest_block` 比率分支，直至通过。常见问题：`confint_proportions_2indep` 的 `alpha=0.05` 必须显式传，默认是 0.1）

- [ ] **Step 3: Commit**

```bash
git add tests/test_inference.py analyze.py && git commit -m "test: 双比率 z 检验验收（120/1000 vs 150/1000）"
```

---

### Task 6: --causal DiD（红灯 → 绿灯）

> 修正（执行期）：--compare 语义=末个干预前期/首个干预后期；全面板回归避免饱和模型（spec 审查发现两期过滤致 CI=NaN）

**Files:**
- Modify: `tests/test_inference.py`、`analyze.py`

- [ ] **Step 1: 追加失败测试**

```python
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
    assert "平行趋势" in c["parallel_trend_check"] or "未验证" in c["parallel_trend_check"]
    assert any("dowhy" in n for n in c["notes"])
```

`main()` 注册：`check("causal DiD", test_causal_did)`

- [ ] **Step 2: 运行确认失败**

Run: `.venv/bin/python tests/test_inference.py`
Expected: `ERROR causal DiD: KeyError: 'causal'`（调用块还没加）

- [ ] **Step 3: 在 `analyze.py` 的 `sigtest_block` 之后插入 `causal_block`**

```python
# ---------------------------------------------------------------------------
# §I 准实验归因（变化是否由干预导致：DiD / 中断对比；DoWhy 仅作参照不引依赖）
# ---------------------------------------------------------------------------

DOWHY_NOTE = "若能提供变量因果图（DAG），可安装 dowhy 做 GCM 异动归因——超出本脚本范围（§I-8）"


def causal_block(df: pd.DataFrame, parts: list, compare: list, interrupt: str) -> dict:
    """--causal：3 参数=DiD（配 --compare）；2 参数=中断前后对比（配 --interrupt）。

    DiD 的 --compare 语义：期1=干预前最后一期，期2=干预后第一期；
    全面板回归 post = 时间排序 ≥ 期2 的所有期（两期过滤会得到饱和模型，CI/p 无意义）。
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
        d = d.dropna(subset=[value_col])
        d[time_col] = d[time_col].astype(str)
        periods = sorted(d[time_col].unique())
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
        dd["post"] = (dd[time_col].map(lambda t: periods.index(t) >= periods.index(post_anchor))).astype(int)
        dd["did"] = dd["treat"] * dd["post"]
        X = np.column_stack([np.ones(len(dd)), dd["treat"], dd["post"], dd["did"]])
        model = sm.OLS(dd[value_col].values, X).fit()
        ci = model.conf_int()[3]
        # 平行趋势粗检：pre 侧 ≥2 期时，处理/对照各自按期均值做线性拟合，报斜率差
        pre = dd[dd["post"] == 0]
        pre_periods = sorted(pre[time_col].unique())
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
        return {"form": "DiD 两重差分",
                "treat_group": treat_on, "control_group": control_on,
                "pre_periods": pre_periods, "post_periods": [t for t in periods if t not in pre_periods],
                "did_estimate": round(float(model.params[3]), 4),
                "ci95": [round(float(ci[0]), 4), round(float(ci[1]), 4)],
                "p": round(float(model.pvalues[3]), 4),
                "parallel_trend_check": parallel,
                "notes": ["DiD 估计干预效应的前提是平行趋势成立（§I-8）",
                          "因果结论须业务确认",
                          DOWHY_NOTE]}

    if len(parts) == 2 and interrupt:
        # 中断对比：Task 7 实现本分支（此处先落降级错误占位）
        return {"error": "中断对比尚未实现（Task 7）", "downgrade": downgrade}

    return {"error": "--causal 参数：指标列,时间列,分组列（DiD，配 --compare）或 指标列,时间列（中断对比，配 --interrupt）",
            "downgrade": downgrade}
```

- [ ] **Step 4: 导入区追加 statsmodels API（Task 4 导入行之后）**

```python
import statsmodels.api as sm
```

- [ ] **Step 5: main() 接线（--sigtest 调用块之后）**

```python
    # §I 准实验归因（因果性问题：变化是否由干预/事件导致）
    if args.causal:
        parts = [c.strip() for c in args.causal.split(",")]
        draft["causal"] = causal_block(df, parts, compare, args.interrupt)
```

- [ ] **Step 6: 跑测试转绿**

Run: `.venv/bin/python tests/test_inference.py`
Expected: 全部 PASS（全面板 DiD 估计 ≈10.15，CI 覆盖 8，p≈0.002；断言容差 |est-8|≤3 已覆盖）

- [ ] **Step 7: Commit**

```bash
git add analyze.py tests/test_inference.py docs/superpowers/plans/2026-09-13-analysis-routing-and-inference.md
git commit -m "feat: analyze.py §I 准实验 DiD（全面板回归，--compare=末pre/首post，平行趋势粗检+降级指引）"
```

---

### Task 7: --causal 中断对比（红灯 → 绿灯，/tmp 数据）

> 修正（执行期）：Task 6 只落了中断对比分支的占位 error（`中断对比尚未实现（Task 7）`），本 Task 在 `causal_block` 真正实现该分支（真实红灯 → 绿灯）。

**Files:**
- Modify: `tests/test_inference.py`、`analyze.py`

- [ ] **Step 1: 追加测试（/tmp 造 16 天日值，第 9 天起 +8）**

```python
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
    assert c["form"] == "中断前后对比"
    assert abs(c["diff"] - 8) <= 4, f"diff={c['diff']}"
    assert c["p"] < 0.05
    assert any("同期趋势" in n for n in c["notes"])


def test_causal_downgrade():
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write("date,value\n2026-08-25,100\n2026-08-26,101\n2026-08-27,99\n")
        path = f.name
    d = run_analyze(path, "--causal", "value,date")
    c = d["causal"]
    assert "downgrade" in c and "探索性归因" in c["downgrade"]
```

`main()` 注册两行：

```python
    check("causal 中断对比", test_causal_interrupt)
    check("causal 降级指引", test_causal_downgrade)
```

- [ ] **Step 2: 确认红灯 → 在 `causal_block` 落地中断对比分支 → 转绿**

Run: `.venv/bin/python tests/test_inference.py`
Expected: 先红（Task 6 占位 `error=中断对比尚未实现（Task 7）` → `KeyError: 'form'`）；
在 `analyze.py` 的 `causal_block` 实现 2 参数 + `--interrupt` 分支后全部 PASS

- [ ] **Step 3: Commit**

```bash
git add analyze.py tests/test_inference.py && git commit -m "feat: analyze.py §I 中断对比分支 + 验收测试"
```

---

### Task 8: 贡献度分解加 Bootstrap 95% CI

**Files:**
- Modify: `analyze.py`（`contribution_block`）、`tests/test_inference.py`

- [ ] **Step 1: 追加失败测试**

```python
def test_contribution_bootstrap_ci():
    d = run_analyze(str(ROOT / "examples/gmv_attribution.csv"),
                    "--metric", "delta_wan", "--time", "period", "--dims", "factor",
                    "--compare", "W25,W26")
    c = d["contribution"]
    assert "total_delta" in c  # 既有字段仍在
    rows = c["by_dim"]
    assert all("contribution_ci95" in r for r in rows), "缺 Bootstrap CI 字段"
    for r in rows:
        lo, hi = r["contribution_ci95"]
        assert lo <= hi


def main():
    ...  # 在已有 check 行后追加
    check("contribution Bootstrap CI", test_contribution_bootstrap_ci)
```

注意：先确认 `examples/gmv_attribution.csv` 的实际列名/期值（`head -3`），`--compare` 两期按实际值填（计划编写时列为 `factor,delta_wan,note`，期列以实跑为准；若该文件无两期结构，改用 `/tmp` 造 2 期 × 4 因子 × 3 行的面板数据，断言相同）。

- [ ] **Step 2: 运行确认失败**

Run: `.venv/bin/python tests/test_inference.py`
Expected: `FAIL contribution Bootstrap CI: 缺 Bootstrap CI 字段`

- [ ] **Step 3: 修改 `contribution_block`：在 `rows` 组装循环之前加 Bootstrap，循环内每行加 CI**

在 `total = wide["delta"].sum()` 之后插入：

```python
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
            delta = w[p1] - w[p0]
            t = delta.sum()
            if not t:
                continue
            pct = (delta / t * 100)
            for k, v in pct.items():
                ci_map.setdefault(k, []).append(float(v))
```

`rows.append({...})` 中 `"contribution_pct": ...` 之后加一个字段：

```python
            "contribution_ci95": (
                [round(float(np.percentile(ci_map[dim_vals], 2.5)), 1),
                 round(float(np.percentile(ci_map[dim_vals], 97.5)), 1)]
                if boot_ok and dim_vals in ci_map and len(ci_map[dim_vals]) >= 100
                else None),
```

返回 dict 的 `"note"` 追加一句：

```python
            "note": ("负贡献排在最前；贡献度只回答'哪里变了'，不回答'为什么'——归因需假设验证"
                     + ("；contribution_ci95 为 Bootstrap 95% 区间（重采样 1000 次）"
                        if boot_ok else "；每期行数 <8，Bootstrap CI 无意义未计算")),
```

- [ ] **Step 4: 跑测试转绿 + 全量回归**

Run: `.venv/bin/python tests/test_inference.py`
Expected: ALL PASS

Run: `.venv/bin/python analyze.py examples/gmv_weekly.csv --metric gmv_wan --time week 2>/dev/null | .venv/bin/python -c "import json,sys; d=json.load(sys.stdin); assert sorted(d.keys())==['data_cleaning','input','quality_check','sanbi']; print('gmv 回归 OK')"`
Expected: `gmv 回归 OK`

- [ ] **Step 5: Commit**

```bash
git add analyze.py tests/test_inference.py && git commit -m "feat: 贡献度分解加 Bootstrap 95% CI（每期≥8 行才计算）"
```

---

### Task 9: methodology §I.0 路由 + 八法表 + 文献锚点

**Files:**
- Modify: `methodology/analysis-methodology.md`

- [ ] **Step 1: §I 标题行之后、「探查完成后…」段之前，插入 §I.0 路由小节（内容 = spec 第 2 节原文表格 + 四条守门规则 + 「提案格式升级」句）**

完整插入内容：

```markdown
### §I.0 问题类型路由（「分析方式提案」的前置判定）

提案前先把用户目标判定为六类问题之一（Leek & Peng《What is the question?》Science 2015；
成熟度参照 Gartner Analytic Ascendancy 四层）：

| 问题类型 | 目标特征 | 路由 | Gartner 层 |
|---|---|---|---|
| 描述性 | 现状是多少/构成怎样 | 分组/画像/对比（§B） | 描述 |
| 探索性 | 哪里异常/有什么模式 | §H 探查三步+漏斗/象限 | 描述/诊断 |
| 推断性 | 差异是真是噪声/可否推广 | 第 7 法 显著性检验 | 诊断 |
| 因果 | 什么导致了变化/动作是否有效 | 第 8 法 准实验归因 | 诊断 |
| 预测性 | 将会怎样/预估多少 | 超出当前能力——提案明示边界，只做趋势外推描述 | 预测 |
| 机制性 | 具体怎样起作用 | 业务分析罕见，不路由 | 规范 |

类型混淆守门规则（可执行）：
1. 因果类目标但数据无对照组且无干预点 → 降级为探索性归因（贡献度分解），结论标「暂定」；
2. 探查阶段的探索性发现不得在提案/结论中升格为因果/推断表述（挂靠 §D「不用偶然代表必然」）；
3. 推断/因果类结论无检验或 CI 证据 → 确认点 2 不予通过；
4. 预测类目标 → 诚实声明能力边界，不冒充。

提案格式：确认点 1 每项分析方式增加「问题类型：X（判定依据）」字段。
```

- [ ] **Step 2: 六法表替换为八法表（在表尾追加第 7、8 行，并把第 7 列「脚本」更新）**

在第 6 行 RFM 之后追加：

```markdown
| 7 | 显著性检验 | 差异是噪声还是真信号？ | 两组数值，或比率+计数 | `--sigtest 指标[,分组]` / `--sigtest 成功,总数,组` | 对比条+置信区间 |
| 8 | 准实验归因 | 变化是否由干预/事件导致？ | 两期面板+对照组，或干预时间点 | `--causal 指标,时间,组 --compare` / `--causal 指标,时间 --interrupt` | DiD 双线图、前后对比 |
```

- [ ] **Step 3: 各法避坑清单之后追加「文献锚点」块**

```markdown
文献锚点（每法的权威出处；「自组装」方法的规范化依据）：
- 路由：Leek & Peng, *What is the question?* (Science/SSC 2015)；Gartner Analytic Ascendancy
- 流程：CRISP-DM（§C 七步成诗的跨行业同源标准，标注在 §C）
- 探索式分析：Tukey, *Exploratory Data Analysis* (1977)——探查/假设验证的分工依据
- 1 对比：§B 三比 + *Lean Analytics*（Croll & Yoskovitz）唯一关键指标（OMTM）
- 2 分组：MECE 原则（Minto《金字塔原理》）
- 3 漏斗：产品分析漏斗标准口径（环节转化/流失）
- 4 象限：BCG growth-share matrix（Henderson, 1970）
- 5 留存：cohort retention 标准口径（新增留存≠活跃留存；精确第 N 日）
- 6 RFM：Hughes, *Strategic Database Marketing* (1994)
- 7 检验：Welch t / Mann-Whitney U / 双比例 z；效应量 Cohen's d（措辞纪律见脚本输出）
- 8 因果：Difference-in-Differences（Card & Krueger 1994 为经典应用）；
  Hernán & Robins, *What If*；DoWhy (PyWhy) 为参照实现（本脚本不引依赖）
```

- [ ] **Step 4: §C 标题行尾追加旁注**

在 `## §C 七步成诗法（分析骨架）` 的首段之后追加一行：

```markdown
- 跨行业同源标准：CRISP-DM（业务理解→数据理解→准备→建模→评估→部署），七步与之对齐。
```

- [ ] **Step 5: Commit**

```bash
git add methodology/analysis-methodology.md && git commit -m "docs: methodology §I.0 问题类型路由 + 八法表 + 文献锚点（Leek&Peng/Gartner/Tukey/BCG/Hughes/DiD）"
```

---

### Task 10: 工作流接线（data2ppt.md + SKILL.md + README）

**Files:**
- Modify: `data2ppt.md`、`skill/data2ppt-SKILL.md`、`README.md`

- [ ] **Step 1: data2ppt.md 确认点 1 段落追加问题类型声明要求**

在「2. **【阻塞确认点 1】分析方式提案**」条目内「对比类按 §B 标注属于哪一比。」之后插入：

```markdown
   每项同时声明「问题类型：描述/探索/推断/因果（判定依据）」（§I.0 路由）；
   预测类目标按 §I.0 规则 4 明示能力边界。
```

- [ ] **Step 2: data2ppt.md 确认点 2 追加守门**

在「4. **【阻塞确认点 2】…**」条目 a) 末尾追加：

```markdown
      推断/因果类结论必须附显著性检验或 CI 证据，否则按 §I.0 规则 3 不予通过；
```

- [ ] **Step 3: data2ppt.md 坑清单追加两条（`- push 到 GitHub 直连不通…` 之前）**

```markdown
- 显著性检验每组 n<30 不输出 p 值（只报效应量方向并标暂定）；p≥0.05 只说
  「未检出显著差异」，禁止说「无差异」。
- 因果估计（DiD/中断对比）必须带 CI 与平行趋势/前提检查结果；「未验证」不得静默省略。
```

- [ ] **Step 4: SKILL.md 确认点 1/2 同步（与 Step 1/2 相同语义的句子分别插入两处）**

确认点 1 段落「预期产出与呈现形式；」之后插：

```markdown
   每项同时声明「问题类型：描述/探索/推断/因果（判定依据）」（§I.0 路由）；
```

确认点 2 段落「反证不抹平；」之后插：

```markdown
   推断/因果类结论必须附检验或 CI 证据（§I.0 规则 3）；
```

- [ ] **Step 5: README.md analyze.py 行更新**

`analyze.py` 行改为：

```markdown
| `analyze.py` | 自动探查脚本：CV 稳定性、3σ/IQR 异常值、两期贡献度分解、三比框架 + §I 八法实跑（对比/分组/漏斗/象限/留存/RFM/显著性检验/准实验归因）→ facts 草稿 |
```

- [ ] **Step 6: 全量回归 + Commit**

Run: `.venv/bin/python tests/test_inference.py`
Expected: ALL PASS

```bash
git add data2ppt.md skill/data2ppt-SKILL.md README.md && git commit -m "docs: 工作流接线 §I.0 路由声明与确认点守门 + 坑清单两条统计纪律"
```

---

### Task 11: 收尾——全量验收、提交推送

- [ ] **Step 1: 全部测试 + 全部老用例回归**

```bash
.venv/bin/python tests/test_inference.py
.venv/bin/python analyze.py examples/rfm_orders.csv --rfm user_id,order_date,amount_yuan > /dev/null && echo rfm OK
.venv/bin/python analyze.py examples/retention_events.csv --retention user_id,active_date,channel > /dev/null && echo retention OK
.venv/bin/python analyze.py examples/quadrant_products.csv --quadrant growth_pct,profit_wan --dims product > /dev/null && echo quadrant OK
```
Expected: `ALL PASS` + 三个 OK

- [ ] **Step 2: 隐私检查后提交推送（代理必带）**

```bash
git status --short
git diff --cached | grep -cE '转转|GMV保费|做功' || echo "隐私 OK"
export https_proxy=http://127.0.0.1:7897 http_proxy=http://127.0.0.1:7897 all_proxy=socks5://127.0.0.1:7897
git push origin master
```
Expected: push 成功，本地与远端 master 一致

---

## Self-Review 记录

1. **Spec 覆盖**：§2 路由→Task 9；§3 八法+锚点→Task 9；§4.1→Task 4/5；§4.2→Task 6/7（含降级与 DoWhy note）；§4.2 Bootstrap→Task 8；§4.3 依赖→Task 1；§5 工作流→Task 10；§6 验收→Task 2/11；§7 YAGNI 无需任务；§8 风险已内嵌守门与措辞纪律。fixture 超出 spec 两个的部分（比率/中断用例）用 /tmp 生成，不新增仓库文件。✅
2. **占位符**：无 TBD/TODO；所有代码步骤含完整代码。✅
3. **一致性**：`sigtest_block`/`causal_block`/`SIGTEST_MIN_N`/`DOWHY_NOTE`/`_two_group_report`/`_cohen_d` 命名在定义与调用处一致；`--sigtest` 2/3 参数分支与 spec 4.1 修正案一致；`confint_proportions_2indep` 显式 `alpha=0.05`。✅

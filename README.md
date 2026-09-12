# PPT-Maker

表格数据 → nerdy 绿风格、图表**原生可编辑**的 16:9 决策摘要 PPT。基于
[ppt-master](https://github.com/hugohe3/ppt-master)（MIT）定制：保留其 SVG→DrawingML
编译器与质量门，收窄为一条"数据 → 叙事大纲一次确认 → 自动出片"的工作流。

## 仓库结构

| 路径 | 说明 |
|---|---|
| `data2ppt.md` | 工作流约定：交互节奏、质量红线、ppt-master 命令映射、实跑坑清单 |
| `templates/nerdy-green-storytelling/` | 风格工作区（设计 tokens、Storytelling 方法论、流程图样式规范） |
| `skill/data2ppt-SKILL.md` | 可调用技能定义（复制到 `~/.agents/skills/data2ppt/SKILL.md` 使用） |
| `analyze.py` | 自动探查脚本：CV 稳定性、3σ/IQR 异常值、两期贡献度分解、三比框架 + §I 六法实跑（对比/分组/漏斗/象限/留存/RFM）→ facts 草稿 |
| `methodology/` | 数据分析方法论规则库 §A–§I：可信前置检查、三比、探查顺序、六法选择菜单与避坑规则 |
| `charts/` | 独立快速图表（matplotlib → 透明 PNG）：白名单只入库 `chart_style.py` 公共样式与 `example_dual_axis_line.py` 模板，真实数据脚本留在本地（见 charts/README.md） |
| `examples/` | 端到端验收样例数据（GMV 虚构样例） |
| `flowchart/flowchart_base.json` | 流程图拓扑源（archify workflow 格式，已脱敏） |
| `docs/superpowers/` | 设计文档、实施计划、验收记录 |
| `ppt-master/`、`projects/`、`.venv/` | 本地生成，不入库（见 .gitignore） |

## 快速开始

```bash
git clone https://github.com/hugohe3/ppt-master   # 依赖本体
python3 -m venv .venv && .venv/bin/pip install -r ppt-master/requirements.txt -r requirements-lock.txt
.venv/bin/pip install pandas openpyxl   # analyze.py 依赖
cp skill/data2ppt-SKILL.md ~/.agents/skills/data2ppt/SKILL.md   # 按需改其中的本机路径
```

之后对 AI 助手说"做 PPT，数据是……"即可。流程与红线见 `data2ppt.md`。

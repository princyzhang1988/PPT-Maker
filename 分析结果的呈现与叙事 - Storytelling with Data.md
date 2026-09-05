---
title: 分析结果的呈现与叙事
subtitle: 基于 Cole Knaflic《Storytelling with Data》
type: 方法论
tags:
  - 数据可视化
  - 叙事
  - 分析方法论
  - storytelling
created: 2026-06-07
---

# 分析结果的呈现与叙事

> **你画的不是图，你画的是结论。**
> 
> —— Cole Knaflic, *Storytelling with Data*

---

## 一、核心问题

大多数数据分析师卡住的不是"能不能画出来"，而是**"怎么画得更清楚、更美观、更适合表达结论"**。

分析过程的终点不是找到答案，而是**让决策者看懂并行动**。本方法论聚焦这"最后一公里"。

---

## 二、画图前：先写结论再画图

### 一句话结论原则

画任何图之前，先写一句不超过 30 字的话：

> ❌ "GMV 趋势图"  
> ✅ "本周 GMV 下跌 5.2%，主因渠道 A 转化率骤降"

这句话直接作为图的标题。如果写不出，说明还没想清楚要证明什么。

### 三问定位

| 问题 | 不要 | 要 |
|------|------|------|
| 给谁看？ | "给团队"太模糊 | "给总监，他需要决定是否调预算" |
| 要做什么决策？ | 画一堆指标等人看 | 只画支撑决策的证据 |
| 什么数据支撑？ | 所有关联指标塞一张图 | 选最强的 2-3 个证据 |

---

## 三、画图时：删减优先于添加

### 删除清单

每张图做完逐条自查：

- [ ] **网格线** → 删掉。不是坐标纸，是讲故事。
- [ ] **图例**（如果能直接标注在线旁）→ 删掉，减少眼球跳转
- [ ] **双 Y 轴** → 拆成两张图。双轴几乎永远是误导。
- [ ] **默认配色** → matplotlib/seaborn 默认色辨识度差
- [ ] **多余边框** → 只保留左+下坐标轴（数据墨水比原则）
- [ ] **装饰元素** → 阴影、3D、渐变都是噪音

### 颜色规则

颜色只有一个用途：**标记需要关注的东西。**

```
异常/核心指标 → 红色/橙色（醒目色）
对比/次要指标 → 灰色/浅蓝（退到背景）
同组正常值   → 统一中性色
```

> 错误示范：每条折线不同颜色 → 观众不知道看哪里。
> 正确示范：只有异常那条是红色，其余全是浅灰。

### 前注意属性

人眼不假思索就能感知的差异，按认知优先级：

| 优先级 | 属性 | 用法 |
|--------|------|------|
| 1 | 颜色 | 红色在灰色中最跳 |
| 2 | 大小 | 核心指标放大 |
| 3 | 位置 | 最重要放左上角（F 型阅读） |
| 4 | 粗细 | 主线加粗，参考线变细 |
| 5 | 标注 | 圈出异常点，直接写数字 |

### 图型速查

```
一个数字           = 大字展现（不要图）
两个数字对比       = 文字 + 百分比
3-5 个分类对比     = 横向柱状图（降序排列）
时间趋势           = 折线图
归因分解           = 瀑布图
相关性（少量点）   = 散点图
相关性（大量点）   = 热力图
构成占比           = 堆叠柱状图（不用饼图，>3 分类人眼分不清）
```

---

## 四、画图后：6 秒测试

把图给一个没看过数据的人看 6 秒，拿走，问：

> "这张图说了什么？"

答不上来 = 回去继续删。这是比任何设计原则都更有效的检验标准。

---

## 五、从"分析报告"到"决策摘要"

面向分析师同行的完整报告有 6 个板块。但给决策者看时，需要压缩为一页 4 段：

| 段落     | 作用              | 字数    | 示例（GMV 下跌场景）                                  |
| ------ | --------------- | ----- | --------------------------------------------- |
| **冲突** | 一句话说清发生了什么      | ≤30 字 | "本周 GMV 环比下跌 5.2%，为近 8 周最大跌幅"                 |
| **放大** | 说清量级和影响范围       | 1-2 句 | "从 1280 万降至 1213 万，影响约 8 万用户"                 |
| **归因** | 按贡献度排序，≤3 个原因   | 3-5 句 | "渠道 A 转化率从 3.2% 跌至 1.1%（贡献 3.8pp）→ 落地页改版导致"   |
| **行动** | 必须给出建议，否则分析没有意义 | 1-2 句 | "建议回滚渠道 A 落地页 + 渠道 B 恢复投放。预期 3 天内恢复至 1250 万+" |

---

## 六、代码模板

> 📊 在线演示：[[charts-demo.html|点击查看图表实际效果]]

### 简洁折线图（强调异常）

```python
import matplotlib.pyplot as plt
import numpy as np

# ---- 样例数据 ----
weeks = ['W19','W20','W21','W22','W23','W24','W25','W26']
values = [1310, 1330, 1290, 1320, 1280, 1300, 1310, 1213]

# ---- 策略：灰线打底 → 异常段红色覆盖 ----
fig, ax = plt.subplots(figsize=(10, 4))

# 1) 一根完整的灰色细线（全部 8 周）
ax.plot(weeks, values, color='#cccccc', linewidth=1.5, marker='o', markersize=5)

# 2) 异常段（W25→W26）用红色粗线覆盖灰色
anomaly_mask = [False, False, False, False, False, False, True, True]  # 覆盖最后两点
ax.plot(np.array(weeks)[anomaly_mask], np.array(values)[anomaly_mask],
        color='#e74c3c', linewidth=2.5, marker='o', markersize=9)

# 3) 在异常点下方直接标注，不用图例
ax.annotate('-5.2%', xy=(weeks[-1], values[-1]),
            xytext=(0, -34), textcoords='offset points',
            fontsize=11, fontweight='bold', color='#e74c3c', ha='center')

# 4) 可选：从异常点向左画一条虚线，暗示下跌幅度
ax.plot([weeks[-1], weeks[-1]], [values[-1], values[-2]],
        color='#e74c3c', linewidth=0.8, linestyle='dashed', alpha=0.4)

# 5) 删繁就简
ax.spines[['top', 'right']].set_visible(False)
ax.grid(False)
ax.set_title('本周 GMV 环比下跌 5.2%，为近 8 周最大跌幅',
             fontsize=14, fontweight='bold', loc='left')
plt.tight_layout()
```

### 瀑布图（归因分解）

```python
import waterfall_chart  # pip install waterfallcharts

values = {"上周": 1280, "渠道A转化下降": -49, "渠道B减投": -18,
          "渠道C增长": +8, "其他": -8, "本周": 1213}

waterfall_chart.plot(list(values.keys()), list(values.values()),
                      net_label='本周', formatting='{:,.0f}万')
plt.title('GMV 周环比归因分解（万元）', fontsize=14, fontweight='bold')
```

---

## 七、常见错误速查

| ❌ 错误 | ✅ 改正 | 违反的原则 |
|------|------|------|
| 标题写"GMV 趋势图" | 写"GMV 本周下跌 5.2%，为近 8 周最大跌幅" | 一句话结论 |
| 每条线不同颜色 | 只给关注的那条加颜色，其余灰色 | 颜色规则 |
| 饼图超过 3 块 | 横向柱状图，按值排序 | 图型速查 |
| 双 Y 轴对比 | 拆成上下两张图，共用 X 轴 | 删除清单 |
| 图例在右上角 | 直接标注在线旁边 | 前注意属性 |
| 满屏网格线 | 全删，需要参考线才画一条虚线 | 数据墨水比 |
| 装饰性 3D / 阴影 / 渐变 | 删掉，扁平化 | 删除清单 |

---

## 八、推荐资源

- **《Storytelling with Data》** — Cole Knaflic，本方法论的原著
- **《The Visual Display of Quantitative Information》** — Edward Tufte，数据墨水比理论
- **《Storytelling with Data: Let's Practice!》** — Cole Knaflic，配套练习册
- **[storytellingwithdata.com](https://www.storytellingwithdata.com/)** — 官方博客，每月更新案例

---

*基于 Cole Knaflic《Storytelling with Data: A Data Visualization Guide for Business Professionals》整理，结合业务分析场景本地化适配。*

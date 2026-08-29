# 波浪能最大输出功率设计

> 2022 高教社杯全国大学生数学建模竞赛 **A 题**（波浪能最大输出功率设计）的完整求解实现：动力学建模、数值求解、能量输出优化、灵敏度分析，以及论文配图。

## 题目概述

波浪能装置由**浮子**（圆柱壳 + 圆锥壳）、**振子**（圆柱体）、中轴与 **PTO 系统**（弹簧 + 阻尼器）组成。浮子在波浪激励力（矩）作用下垂荡/纵摇，带动振子相对运动，驱动阻尼器做功输出能量。题目要求：

| 子问题 | 运动形式 | 阻尼器模型 | 目标 |
|--------|---------|-----------|------|
| 问题 1 | 垂荡（2 自由度） | 线性 / 非线性 | 前 40 周期位移、速度时间序列 |
| 问题 2 | 垂荡（2 自由度） | 线性 / 非线性 | 最大平均输出功率及最优阻尼 |
| 问题 3 | 垂荡 + 纵摇（4 自由度） | 线性 | 前 40 周期位移、角位移时间序列 |
| 问题 4 | 垂荡 + 纵摇（4 自由度） | 线性 | 最大总输出功率及最优阻尼 |

## 目录结构

```
.
├── 建模思路.md              # 建模报告（求解思路与公式推导）
├── RESULTS.md               # 计算结果报告（本文档的数值来源）
├── A题/                     # 题目与附件数据（题目 PDF、附件 1-4）
├── code/                    # 求解代码（Python + SciPy）
│   ├── utils.py             #   参数读取、矩阵构建、RK45 求解、频域稳态解、功率计算
│   ├── problem1.py          #   问题 1：垂荡动力学（线性 + 非线性）
│   ├── problem2.py          #   问题 2：垂荡能量优化（Brent / Nelder-Mead）
│   ├── problem3.py          #   问题 3：四自由度耦合动力学
│   ├── problem4.py          #   问题 4：双自由度能量优化
│   ├── sensitivity_analysis.py  # 灵敏度分析（关键参数 ±20% 扰动）
│   ├── main.py              #   汇总各子问题 → all_results.json
│   └── requirements.txt     #   依赖清单
└── figures/                 # 结果数据 + 论文配图 + LaTeX 表格
    ├── problem_1~4_results.json  # 各子问题结果
    ├── all_results.json          # 汇总结果
    ├── sensitivity_results.json  # 灵敏度分析数据
    ├── fig_1~4_*.pdf             # 4 张时程可视化图
    ├── gen_fig_1~4_*.py          # 对应绘图脚本
    ├── TABLE_summary.tex         # 优化结果汇总表
    ├── TABLE_snapshot.tex        # 问题 1 指定时刻快照表
    └── latex_includes.tex        # 图表 LaTeX 引用片段
```

## 环境要求

- Python ≥ 3.9
- 依赖库（`numpy`、`scipy`、`pandas`、`matplotlib`、`openpyxl`）：

```bash
pip install -r code/requirements.txt
```

## 快速开始

### 1. 复现计算

各子问题相互独立，可任意顺序运行；`main.py` 最后汇总。所有路径均相对脚本文件自身解析，从任意目录执行均可：

```bash
python code/problem1.py              # 问题 1
python code/problem2.py              # 问题 2
python code/problem3.py              # 问题 3
python code/problem4.py              # 问题 4
python code/sensitivity_analysis.py  # 灵敏度分析
python code/main.py                  # 汇总 → figures/all_results.json
```

结果写入 `figures/*_results.json` 与 `figures/result*.xlsx`。

### 2. 复现论文配图

绘图脚本读取 `figures/problem_1_results.json` 生成矢量 PDF（需在**项目根目录**执行）：

```bash
python figures/gen_fig_1_heave_displacement.py   # 图 1 浮子/振子垂荡位移时程
python figures/gen_fig_2_heave_velocity.py       # 图 2 浮子/振子垂荡速度时程
python figures/gen_fig_3_relative_motion.py      # 图 3 相对位移/速度时程
python figures/gen_fig_4_pto_power.py            # 图 4 PTO 瞬时功率
```

> 绘图脚本依赖共享绘图工具 `_utils/plot_utils.py`（提供学术配色与中文字体），该工具未纳入版本库；脚本会在运行时自动从 `~/.claude/skills/shared-scripts/` 拷贝，若不存在请先放置该文件。

### 3. 查看结果

直接阅读 [`RESULTS.md`](RESULTS.md)（完整数值报告）或 [`建模思路.md`](建模思路.md)（建模推导）。

## 关键结果

| 子问题 | 阻尼模型 | 最优阻尼 | 最大平均输出功率 |
|--------|---------|---------|-----------------|
| 问题 2 | 线性 | C\* = 37193.8 N·s/m | 229.334 W |
| 问题 2 | 非线性 | α\* = 100000，P\* = 0.417 | 229.980 W |
| 问题 4 | 直线 | C<sub>z</sub>\* = 59152.9 N·s/m | 318.336 W |
| 问题 4 | 旋转 | C<sub>θ</sub>\* = 100000 N·m·s | 0.063 W（可忽略） |
| 问题 4 | 合计 | — | **318.400 W** |

**模型检验**：线性阻尼问题 2 的频域解析解（229.334 W）与时域 RK45（229.316 W）误差 < 0.01%，交叉验证一致；所有结果无 NaN/Inf，位移量级 0.1–0.5 m、速度 0.6–1.0 m/s、纵摇角约 0.03 rad，符合波浪能装置物理量级。纵摇通道贡献可忽略的原因是扭转弹簧（k<sub>θ</sub>=250000 N·m）相对 J<sub>2</sub>ω² 极刚，浮子与振子纵摇近乎锁定。

## 求解方法

- **动力学**：二体耦合二阶 ODE `M Z'' + C Z' + K Z = F(t)`，RK45 数值积分（`scipy.integrate.solve_ivp`）。
- **优化**：线性阻尼用频域稳态解析解 + Brent（`scipy.optimize.minimize_scalar`）；非线性阻尼用时域稳态平均功率 + 粗网格 + Nelder-Mead。
- **稳态处理**：优化目标取 80 周期积分、末 30 周期平均，消除刚性模态缓慢瞬态的影响。
- **灵敏度**：关键参数 ±20% 扰动，量化功率对波浪频率/激励力/附加质量/兴波阻尼的敏感度。

## 结果数据格式

- `figures/problem_1_results.json`：`{linear, nonlinear}` 两套完整时间序列（`t / z1 / v1 / z2 / v2`，898 点）+ 指定时刻快照。
- `figures/all_results.json`：四子问题汇总，含 `summary` 关键结论，是论文撰写与绘图的主输入。
- `figures/sensitivity_results.json`：各参数扫描值及目标变化率。

---

*代码按 `建模思路.md` 自动实现并计算，结果见 `RESULTS.md`；图表脚本与 LaTeX 片段见 `figures/`。*

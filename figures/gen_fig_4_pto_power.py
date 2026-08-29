import os, sys, shutil
os.makedirs('_utils', exist_ok=True)
for src in ['plot_utils.py']:
    for search in [os.path.expanduser('~/.claude/skills/shared-scripts')]:
        p = os.path.join(search, src)
        if os.path.isfile(p):
            shutil.copy2(p, f'_utils/{src}')  # copies .py file, NOT .pdf
            break
sys.path.insert(0, '.')  # plain dot
from _utils.plot_utils import setup_style, save_fig, PALETTE
setup_style('soft')  # 竞赛论文：Soft 配色

import json
import numpy as np

# ---- 读取数据（问题1 线性 + 非线性阻尼）----
with open('figures/problem_1_results.json', 'r', encoding='utf-8') as fp:
    data = json.load(fp)
t = np.asarray(data['linear']['t'], dtype=float)

lin = data['linear']
non = data['nonlinear']
vrel_lin = np.asarray(lin['v2']) - np.asarray(lin['v1'])   # 相对速度（线性）
vrel_non = np.asarray(non['v2']) - np.asarray(non['v1'])   # 相对速度（非线性）

# ---- PTO 瞬时功率（模型给定阻尼参数）----
# 线性阻尼：P_lin(t) = C · v_rel^2 , C = 10000 N·s/m
C = 10000.0
P_lin = C * vrel_lin ** 2
# 非线性阻尼：P_nl(t) = α · |v_rel|^(P+2) , α = 10000, P = 0.5
alpha = 10000.0
P_exp = 0.5
P_non = alpha * np.abs(vrel_non) ** (P_exp + 2.0)

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(7, 4))

# 线性阻尼功率：浅蓝面积填充 + 实线
ax.fill_between(t, P_lin, color=PALETTE[0], alpha=0.30, linewidth=0, zorder=1)
ax.plot(t, P_lin, color=PALETTE[0], linewidth=1.6, label='线性阻尼', zorder=3)
# 非线性阻尼功率：珊瑚色虚线
ax.plot(t, P_non, color=PALETTE[1], linewidth=1.6, linestyle='--', label='非线性阻尼', zorder=3)

# 40 周期平均功率参考线（线性）
P_mean = float(np.mean(P_lin))
ax.axhline(P_mean, color='#666666', linewidth=1.0, linestyle='-.', zorder=2)
ax.text(t.max() * 0.02, P_mean * 1.06, f'平均功率 {P_mean:.1f} W',
        fontsize=8, va='bottom', ha='left',
        bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))

ax.set_xlabel('时间 (s)')
ax.set_ylabel('PTO 瞬时功率 (W)')
ax.legend(loc='upper right', frameon=True)
ax.set_xlim(0, t.max())
ax.set_ylim(0, None)

save_fig(fig, 'figures/fig_4_pto_power.pdf')

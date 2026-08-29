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

# ---- 读取数据（问题1 线性阻尼时间序列）----
with open('figures/problem_1_results.json', 'r', encoding='utf-8') as fp:
    data = json.load(fp)
lin = data['linear']
t = np.asarray(lin['t'], dtype=float)
v1 = np.asarray(lin['v1'], dtype=float)   # 浮子垂荡速度
v2 = np.asarray(lin['v2'], dtype=float)   # 振子垂荡速度
T = lin['meta']['T']

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(7, 4))

# 主图：前 40 个波浪周期的完整速度时程
ax.plot(t, v1, color=PALETTE[0], linewidth=1.8, label='浮子')
ax.plot(t, v2, color=PALETTE[1], linewidth=1.8, linestyle='--', label='振子')
ax.axhline(0, color='#AAAAAA', linewidth=0.8, linestyle=':', zorder=1)

# 稳态末段放大窗口（后 3 个周期）
t_lo = t.max() - 3 * T
mask = t >= t_lo
ax.axvspan(t_lo, t.max(), color=PALETTE[4], alpha=0.12, zorder=0)

ins = fig.add_axes([0.54, 0.18, 0.36, 0.34], facecolor='white')
ins.plot(t[mask], v1[mask], color=PALETTE[0], linewidth=1.6)
ins.plot(t[mask], v2[mask], color=PALETTE[1], linewidth=1.6, linestyle='--')
ins.text(0.03, 0.92, '稳态末段（后 3 周期）', transform=ins.transAxes,
         fontsize=8, va='top', ha='left',
         bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))
ins.tick_params(labelsize=8)
ins.patch.set_alpha(0.95)
ins.set_zorder(10)

ax.set_xlabel('时间 (s)')
ax.set_ylabel('垂荡速度 (m/s)')
ax.legend(loc='upper left', frameon=True)
ax.set_xlim(0, t.max())

save_fig(fig, 'figures/fig_2_heave_velocity.pdf')

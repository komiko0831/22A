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
zrel_lin = np.asarray(lin['z2']) - np.asarray(lin['z1'])   # 相对位移（线性）
vrel_lin = np.asarray(lin['v2']) - np.asarray(lin['v1'])   # 相对速度（线性）
zrel_non = np.asarray(non['z2']) - np.asarray(non['z1'])   # 相对位移（非线性）
vrel_non = np.asarray(non['v2']) - np.asarray(non['v1'])   # 相对速度（非线性）

import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 5.4), sharex=True)

# 上：相对位移
ax1.plot(t, zrel_lin, color=PALETTE[0], linewidth=1.6, label='线性阻尼')
ax1.plot(t, zrel_non, color=PALETTE[1], linewidth=1.6, linestyle='--', label='非线性阻尼')
ax1.axhline(0, color='#AAAAAA', linewidth=0.8, linestyle=':', zorder=1)
ax1.set_ylabel('相对位移 (m)')
ax1.legend(loc='upper right', frameon=True, fontsize=9)

# 下：相对速度
ax2.plot(t, vrel_lin, color=PALETTE[0], linewidth=1.6, label='线性阻尼')
ax2.plot(t, vrel_non, color=PALETTE[1], linewidth=1.6, linestyle='--', label='非线性阻尼')
ax2.axhline(0, color='#AAAAAA', linewidth=0.8, linestyle=':', zorder=1)
ax2.set_ylabel('相对速度 (m/s)')
ax2.legend(loc='upper right', frameon=True, fontsize=9)

ax2.set_xlabel('时间 (s)')
ax2.set_xlim(0, t.max())

save_fig(fig, 'figures/fig_3_relative_motion.pdf')

# -*- coding: utf-8 -*-
"""
问题4：垂荡-纵摇双自由度 PTO 能量输出优化
================================================
浮子做垂荡 + 纵摇运动，直线阻尼系数 Cz 与旋转阻尼系数 Cθ 均为常量，
均在 [0, 100000] 内取值。建立最优阻尼系数模型，使总平均输出功率最大。
总功率 = 垂荡 PTO 功率 + 纵摇 PTO 功率（二者解耦，可分别优化）。
"""
import os
import numpy as np
from scipy.optimize import minimize_scalar

from utils import (load_attach3, coupled_steady_power, save_json)

FIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'figures')


def main():
    p = load_attach3()[4]
    omega, ma, Ja, Bz, Bth, f, L = (p['omega'], p['ma'], p['Ja'],
                                    p['Bz'], p['Bth'], p['f'], p['L'])
    print(f'[problem4] ω={omega} s^-1')

    # ---- 垂荡方向：优化 Cz ----
    neg_Pz = lambda Cz: -coupled_steady_power(ma, Ja, Bz, Bth, f, L, omega,
                                              Cz, 0.0)[0]
    rz = minimize_scalar(neg_Pz, bounds=(0.0, 1e5), method='bounded',
                         options={'xatol': 1e-6})
    Cz_opt = float(rz.x)
    Pz_opt = float(-rz.fun)

    # ---- 纵摇方向：优化 Cθ ----
    neg_Pth = lambda Cth: -coupled_steady_power(ma, Ja, Bz, Bth, f, L, omega,
                                                0.0, Cth)[1]
    rth = minimize_scalar(neg_Pth, bounds=(0.0, 1e5), method='bounded',
                          options={'xatol': 1e-6})
    Cth_opt = float(rth.x)
    Pth_opt = float(-rth.fun)

    # ---- 联合验证：在最优点的总功率 ----
    Pz_o, Pth_o, P_tot = coupled_steady_power(ma, Ja, Bz, Bth, f, L, omega,
                                              Cz_opt, Cth_opt)

    # ---- 50×50 响应面（供画图） ----
    grid = np.linspace(0.0, 1e5, 50)
    surface = np.zeros((50, 50))
    for i, Cz in enumerate(grid):
        for j, Cth in enumerate(grid):
            surface[i, j] = coupled_steady_power(ma, Ja, Bz, Bth, f, L, omega,
                                                 Cz, Cth)[2]
    # 响应面极大值（应为联合最优点的近邻）
    imax, jmax = np.unravel_index(np.argmax(surface), surface.shape)

    print(f'  [垂荡]  最优 Cz*  = {Cz_opt:.2f} N·s/m,  Pz_max = {Pz_opt:.4f} W')
    print(f'  [纵摇]  最优 Cθ*  = {Cth_opt:.2f} N·m·s,  Pθ_max = {Pth_opt:.4f} W')
    print(f'  [联合]  总功率 Pmax = {P_tot:.4f} W (垂荡 {Pz_o:.4f} + 纵摇 {Pth_o:.4f})')
    print(f'  [响应面] 网格极大值点 (Cz={grid[imax]:.1f}, Cθ={grid[jmax]:.1f}) '
          f'→ {surface[imax, jmax]:.4f} W')

    results = dict(
        omega=omega,
        meta=dict(ma=ma, Ja=Ja, Bz=Bz, Bth=Bth, f=f, L=L),
        heave=dict(Cz_opt=Cz_opt, Pz_max=Pz_opt),
        pitch=dict(Cth_opt=Cth_opt, Pth_max=Pth_opt),
        total=dict(Cz_opt=Cz_opt, Cth_opt=Cth_opt, P_max=P_tot,
                   Pz=Pz_o, Pth=Pth_o),
        grid=dict(Cz=list(grid), Cth=list(grid), surface=surface.tolist(),
                  surface_max=float(surface.max()),
                  surface_argmax=dict(Cz=float(grid[imax]), Cth=float(grid[jmax]))),
        method='线性系统频域稳态解析 + Brent 分方向优化（垂荡/纵摇解耦）',
    )
    save_json(results, os.path.join(FIG_DIR, 'problem_4_results.json'))
    return results


if __name__ == '__main__':
    main()

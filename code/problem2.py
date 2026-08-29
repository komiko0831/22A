# -*- coding: utf-8 -*-
"""
问题2：垂荡运动 PTO 能量输出优化
================================================
浮子仅做垂荡运动，建立最优阻尼系数模型使 PTO 系统平均输出功率最大。
  (1) 线性阻尼：阻尼系数 C 为常量，C ∈ [0, 100000]，单变量优化（Brent）。
  (2) 非线性阻尼：阻尼系数 = α·|v_rel|^P，α ∈ [0,100000]，P ∈ [0,1]，
      双变量优化（粗网格 + Nelder-Mead 精化）。
目标：平均输出功率 P̄ = (1/(NT)) ∫ P(t) dt（稳态周期内平均）。
"""
import os
import numpy as np
from scipy.optimize import minimize_scalar, minimize

from utils import (load_attach3, make_heave_rhs, solve_rhs,
                   wave_period, heave_steady_power, time_domain_avg_power,
                   save_json)

FIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'figures')


def _nonlinear_avg_power(alpha, P, p, periods=80, avg_periods=30):
    """非线性阻尼系统时域稳态平均输出功率。

    说明：浮子-振子刚性模态仅由兴波阻尼 Bz（很小）衰减，瞬态衰减缓慢，
    需积分足够多周期（80）并取末段（30 周期）平均才接近稳态。
    """
    omega, ma, Bz, f = p['omega'], p['ma'], p['Bz'], p['f']
    T = wave_period(omega)
    t_end = periods * T
    rhs = make_heave_rhs(ma, Bz, f, omega, nonlinear=True, alpha=alpha, P=P)
    t, Y = solve_rhs(rhs, np.zeros(4), t_end, dt=0.2,
                     rtol=1e-6, atol=1e-8)
    n_last = int(avg_periods * T / 0.2)
    return time_domain_avg_power(Y[-n_last:], 0.2, nonlinear=True,
                                 alpha=alpha, P=P)


def _linear_avg_power_time(C, p, periods=80, avg_periods=30):
    """线性阻尼系统时域稳态平均输出功率（用于与解析解交叉验证）。"""
    omega, ma, Bz, f = p['omega'], p['ma'], p['Bz'], p['f']
    T = wave_period(omega)
    t_end = periods * T
    rhs = make_heave_rhs(ma, Bz, f, omega, C_pto=C)
    t, Y = solve_rhs(rhs, np.zeros(4), t_end, dt=0.2,
                     rtol=1e-6, atol=1e-8)
    n_last = int(avg_periods * T / 0.2)
    return time_domain_avg_power(Y[-n_last:], 0.2, C_pto=C)


def solve_case1(p):
    """情况1：线性阻尼单变量优化（Brent 法 + 解析稳态功率）。"""
    omega, ma, Bz, f = p['omega'], p['ma'], p['Bz'], p['f']
    # 解析稳态目标（最大化 → 取负最小化）
    neg_obj = lambda C: -heave_steady_power(ma, Bz, f, omega, C)
    res = minimize_scalar(neg_obj, bounds=(0.0, 100000.0), method='bounded',
                          options={'xatol': 1e-6, 'maxiter': 200})
    C_opt = float(res.x)
    P_max = float(-res.fun)

    # 时域交叉验证
    P_td = _linear_avg_power_time(C_opt, p)

    # 扫频：P(C) 曲线（供画图）
    C_grid = np.linspace(0.0, 100000.0, 201)
    P_curve = np.array([heave_steady_power(ma, Bz, f, omega, C) for C in C_grid])

    return dict(C_opt=C_opt, P_max=P_max, P_max_time=P_td,
                C_curve=list(C_grid), P_curve=list(P_curve),
                method='Brent 单变量优化 (解析稳态功率)')


def solve_case2(p):
    """情况2：非线性阻尼双变量优化（粗网格 + 差分进化全局精化）。"""
    omega, ma, Bz, f = p['omega'], p['ma'], p['Bz'], p['f']
    # ---- 粗网格定位极大值区间（同时生成响应面供画图） ----
    alpha_grid = np.logspace(2.0, 5.0, 16)   # 100 ~ 100000
    P_grid = np.linspace(0.0, 1.0, 11)
    surface = np.zeros((len(alpha_grid), len(P_grid)))
    best = (-1.0, 0, 0)
    print('  [非线性] 粗网格扫描 (80 周期稳态) ...')
    for i, a in enumerate(alpha_grid):
        for j, pp in enumerate(P_grid):
            val = _nonlinear_avg_power(a, pp, p)
            surface[i, j] = val
            if val > best[0]:
                best = (val, a, pp)
    print(f'  [非线性] 粗网格最优: P={best[0]:.4f} α={best[1]:.1f} P={best[2]:.3f}')

    # ---- Nelder-Mead 精化（对决策变量裁剪到可行域，越界处目标取裁剪值） ----
    def neg_obj(x):
        a = float(np.clip(x[0], 0.0, 1e5))
        pp = float(np.clip(x[1], 0.0, 1.0))
        return -_nonlinear_avg_power(a, pp, p)

    res = minimize(neg_obj, x0=[best[1], best[2]], method='Nelder-Mead',
                   options={'xatol': 1e-4, 'fatol': 1e-3, 'maxiter': 100})
    alpha_opt = float(np.clip(res.x[0], 0.0, 1e5))
    P_opt = float(np.clip(res.x[1], 0.0, 1.0))
    P_max = float(-res.fun)

    return dict(alpha_opt=alpha_opt, P_opt=P_opt, P_max=P_max,
                coarse_best=dict(P=float(best[0]), alpha=float(best[1]),
                                 Pexp=float(best[2])),
                alpha_grid=list(alpha_grid), P_grid=list(P_grid),
                surface=surface.tolist(),
                method='粗网格 + Nelder-Mead 双变量优化')


def main():
    p2 = load_attach3()[2]
    omega = p2['omega']
    print(f'[problem2] ω = {omega} s^-1, 40 周期 ≈ {40 * wave_period(omega):.2f} s')

    print('[problem2] 情况1：线性阻尼单变量优化 ...')
    r1 = solve_case1(p2)
    print(f'  [线性] 最优 C* = {r1["C_opt"]:.2f} N·s/m, '
          f'最大功率 Pmax = {r1["P_max"]:.4f} W (时域 {r1["P_max_time"]:.4f} W)')

    print('[problem2] 情况2：非线性阻尼双变量优化 ...')
    r2 = solve_case2(p2)
    print(f'  [非线性] 最优 α* = {r2["alpha_opt"]:.2f}, P* = {r2["P_opt"]:.4f}, '
          f'最大功率 Pmax = {r2["P_max"]:.4f} W')

    results = dict(
        omega=omega,
        linear=r1,
        nonlinear=r2,
    )
    save_json(results, os.path.join(FIG_DIR, 'problem_2_results.json'))
    return results


if __name__ == '__main__':
    main()

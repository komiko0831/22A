# -*- coding: utf-8 -*-
"""
灵敏度分析
================================================
对优化问题的关键参数做 ±20% 扰动，考察其对最大输出功率与最优阻尼系数的
影响。本题为线性（或线性化）系统，采用频域稳态解析解，可快速精确重优化。

分析对象：
  问题2 情况1（线性阻尼）：ω、f、Bz、ma 对 Pmax 与 C* 的影响
  问题4（垂荡-纵摇）：     ω、f、L 对总功率与 Cz* 的影响
"""
import os
import numpy as np
from scipy.optimize import minimize_scalar

from utils import (load_attach3, heave_steady_power, coupled_steady_power,
                   save_json)

FIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'figures')


def _opt_heave(ma, Bz, f, omega):
    """垂荡线性系统：给定参数下重优化 C，返回 (C*, Pmax)。"""
    neg = lambda C: -heave_steady_power(ma, Bz, f, omega, C)
    res = minimize_scalar(neg, bounds=(0.0, 1e5), method='bounded',
                          options={'xatol': 1e-6})
    return float(res.x), float(-res.fun)


def _opt_coupled(ma, Ja, Bz, Bth, f, L, omega):
    """四自由度系统：给定参数下重优化 Cz（Cθ 取最优 100000），返回 (Cz*, Pmax)。"""
    neg = lambda Cz: -coupled_steady_power(ma, Ja, Bz, Bth, f, L, omega,
                                           Cz, 1e5)[2]
    res = minimize_scalar(neg, bounds=(0.0, 1e5), method='bounded',
                          options={'xatol': 1e-6})
    return float(res.x), float(-res.fun)


def _sweep(base, perturb_params, objective):
    """对 base 中的参数列表 perturb_params 做 ±20% 扫描，返回灵敏度字典。

    objective(params_dict) -> (optimal_param, objective_value)
    """
    out = {}
    for name in perturb_params:
        base_val = base[name]
        deltas = np.linspace(-0.20, 0.20, 11)      # -20% ~ +20%
        values, objs, opts = [], [], []
        for d in deltas:
            p = dict(base)
            p[name] = base_val * (1.0 + d)
            opt, val = objective(p)
            values.append(float(p[name]))
            objs.append(float(val))
            opts.append(float(opt))
        out[name] = dict(
            base_value=float(base_val),
            ratio=list(deltas),
            values=values,
            objective=objs,
            optimal_param=opts,
        )
        # 端点变化率（供 tornado 图）
        lo, hi = objs[0], objs[-1]
        out[name]['delta_pct'] = float((hi - lo) / objs[5] * 100.0)
    return out


def main():
    p2 = load_attach3()[2]
    p4 = load_attach3()[4]
    results = {}

    # ---- 问题2 情况1：垂荡线性优化灵敏度 ----
    base2 = dict(omega=p2['omega'], ma=p2['ma'], Bz=p2['Bz'], f=p2['f'])

    def obj2(p):
        return _opt_heave(p['ma'], p['Bz'], p['f'], p['omega'])

    print('[sensitivity] 问题2 线性阻尼灵敏度 ...')
    results['problem2_linear'] = _sweep(base2, ['omega', 'f', 'Bz', 'ma'], obj2)
    for name, r in results['problem2_linear'].items():
        print(f'  {name}: base={r["base_value"]:.4g}, '
              f'±20% 目标变化率 {r["delta_pct"]:+.2f}%')

    # ---- 问题4：垂荡-纵摇优化灵敏度 ----
    base4 = dict(omega=p4['omega'], ma=p4['ma'], Ja=p4['Ja'],
                 Bz=p4['Bz'], Bth=p4['Bth'], f=p4['f'], L=p4['L'])

    def obj4(p):
        return _opt_coupled(p['ma'], p['Ja'], p['Bz'], p['Bth'],
                            p['f'], p['L'], p['omega'])

    print('[sensitivity] 问题4 双自由度优化灵敏度 ...')
    results['problem4'] = _sweep(base4, ['omega', 'f', 'L', 'Bz'], obj4)
    for name, r in results['problem4'].items():
        print(f'  {name}: base={r["base_value"]:.4g}, '
              f'±20% 目标变化率 {r["delta_pct"]:+.2f}%')

    save_json(results, os.path.join(FIG_DIR, 'sensitivity_results.json'))
    return results


if __name__ == '__main__':
    main()

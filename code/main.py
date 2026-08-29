# -*- coding: utf-8 -*-
"""
主程序 —— 2022 高教社杯 A 题：波浪能最大输出功率设计
================================================
汇总各子问题结果，生成 figures/all_results.json（供 paper-figure 画图）。

各子问题可独立运行（problem1.py ~ problem4.py + sensitivity_analysis.py），
本脚本读取它们输出的 JSON 并汇总关键结论，避免重复计算。
"""
import os
import json
import numpy as np

FIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'figures')


def _load(name):
    path = os.path.join(FIG_DIR, name)
    with open(path, 'r', encoding='utf-8') as fp:
        return json.load(fp)


def _floats(d, keys):
    return {k: round(float(d[k]), 6) for k in keys if k in d}


def main():
    all_res = {}

    # ---- 问题1 ----
    r1 = _load('problem_1_results.json')
    lin = r1['linear']; non = r1['nonlinear']
    all_res['problem1'] = dict(
        omega=lin['meta']['omega'],
        linear=dict(damping='C=10000 N·s/m', at_times=lin['at_times']),
        nonlinear=dict(damping='α=10000, P=0.5', at_times=non['at_times']),
    )

    # ---- 问题2 ----
    r2 = _load('problem_2_results.json')
    all_res['problem2'] = dict(
        omega=r2['omega'],
        linear=dict(C_opt=r2['linear']['C_opt'], P_max=r2['linear']['P_max'],
                    P_max_time=r2['linear']['P_max_time']),
        nonlinear=dict(alpha_opt=r2['nonlinear']['alpha_opt'],
                       P_opt=r2['nonlinear']['P_opt'],
                       P_max=r2['nonlinear']['P_max']),
    )

    # ---- 问题3 ----
    r3 = _load('problem_3_results.json')
    all_res['problem3'] = dict(
        omega=r3['omega'], Cz=r3['Cz'], Cth=r3['Cth'],
        snapshots=r3['snapshots'],
    )

    # ---- 问题4 ----
    r4 = _load('problem_4_results.json')
    all_res['problem4'] = dict(
        omega=r4['omega'],
        heave=dict(Cz_opt=r4['heave']['Cz_opt'], Pz_max=r4['heave']['Pz_max']),
        pitch=dict(Cth_opt=r4['pitch']['Cth_opt'], Pth_max=r4['pitch']['Pth_max']),
        total=r4['total'],
    )

    # ---- 关键结论汇总表（供论文表格） ----
    all_res['summary'] = dict(
        问题2线性最优阻尼系数_N_s_m=r2['linear']['C_opt'],
        问题2线性最大功率_W=r2['linear']['P_max'],
        问题2非线性最优比例系数=r2['nonlinear']['alpha_opt'],
        问题2非线性最优幂指数=r2['nonlinear']['P_opt'],
        问题2非线性最大功率_W=r2['nonlinear']['P_max'],
        问题4最优直线阻尼_N_s_m=r4['heave']['Cz_opt'],
        问题4最优旋转阻尼_N_m_s=r4['pitch']['Cth_opt'],
        问题4最大总功率_W=r4['total']['P_max'],
    )

    out_path = os.path.join(FIG_DIR, 'all_results.json')
    with open(out_path, 'w', encoding='utf-8') as fp:
        json.dump(all_res, fp, ensure_ascii=False, indent=2)
    print(f'[main] 已汇总 {out_path} ({os.path.getsize(out_path)} bytes)')
    print('\n=== 关键结果 ===')
    for k, v in all_res['summary'].items():
        print(f'  {k} = {v:.4f}' if isinstance(v, float) else f'  {k} = {v}')


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""
问题1：浮子-振子垂荡运动动力学建模与求解
================================================
中轴底座固定于隔层中心，浮子仅做垂荡运动。建立浮子与振子二自由度运动模型，
在波浪激励力 f·cos(wt) 作用下，计算前 40 个波浪周期内、时间间隔 0.2 s 的
垂荡位移与速度。两种情况：
  (1) 直线阻尼器阻尼系数为常量 C = 10000 N·s/m（线性阻尼）
  (2) 阻尼系数与相对速度绝对值的幂成正比：系数 10000，幂指数 0.5（非线性阻尼）
"""
import os
import numpy as np
import openpyxl

from utils import (load_attach3, make_heave_rhs, solve_rhs,
                   wave_period, save_json)

FIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'figures')


def run_case(linear=True):
    """求解问题1的单个阻尼情况，返回 (t, y=[z1,z2,v1,v2], label)。"""
    p = load_attach3()[1]
    omega, ma, Bz, f = p['omega'], p['ma'], p['Bz'], p['f']
    T = wave_period(omega)
    t_end = 40 * T                       # 前 40 个波浪周期
    dt = 0.2

    y0 = np.zeros(4)                     # 静平衡初始：z1=z2=0, v1=v2=0
    if linear:
        C = 10000.0
        rhs = make_heave_rhs(ma, Bz, f, omega, C_pto=C)
        label = '线性阻尼 C=10000 N·s/m'
    else:
        alpha, P = 10000.0, 0.5
        rhs = make_heave_rhs(ma, Bz, f, omega, nonlinear=True,
                             alpha=alpha, P=P)
        label = '非线性阻尼 α=10000, P=0.5'

    t, Y = solve_rhs(rhs, y0, t_end, dt=dt, omega=omega)
    return t, Y, label, dict(omega=omega, ma=ma, Bz=Bz, f=f, T=T)


def _write_xlsx(t, Y, path, pitch=False):
    """写结果 xlsx（列序与 result1 模板一致）。"""
    wb = openpyxl.Workbook()
    ws = wb.active
    if pitch:
        ws.append(['时间(s)', '浮子垂荡位移(m)', '浮子垂荡速度(m/s)',
                   '浮子纵摇角位移(rad)', '浮子纵摇角速度(rad/s)',
                   '振子垂荡位移(m)', '振子垂荡速度(m/s)',
                   '振子纵摇角位移(rad)', '振子纵摇角速度(rad/s)'])
        for i in range(len(t)):
            ws.append([round(t[i], 6), *[round(float(Y[i, j]), 8) for j in range(8)]])
    else:
        ws.append(['时间(s)', '浮子位移(m)', '浮子速度(m/s)',
                   '振子位移(m)', '振子速度(m/s)'])
        for i in range(len(t)):
            ws.append([round(t[i], 6),
                       round(float(Y[i, 0]), 8), round(float(Y[i, 2]), 8),
                       round(float(Y[i, 1]), 8), round(float(Y[i, 3]), 8)])
    wb.save(path)
    print(f"[problem1] 已写 xlsx {path} ({len(t)} 行)")


def _report_at_times(t, Y):
    """提取 t=10,20,40,60,100s 的位移/速度，供论文表格使用。"""
    times = [10.0, 20.0, 40.0, 60.0, 100.0]
    out = {}
    for tt in times:
        idx = int(round(tt / 0.2))
        out[str(tt)] = {
            '浮子位移_m': float(Y[idx, 0]),
            '浮子速度_ms': float(Y[idx, 2]),
            '振子位移_m': float(Y[idx, 1]),
            '振子速度_ms': float(Y[idx, 3]),
        }
    return out


def main():
    results = {}

    # ---- 情况1：线性阻尼 ----
    print('[problem1] 求解 情况1：线性阻尼 ...')
    t, Y1, lab1, meta1 = run_case(linear=True)
    _write_xlsx(t, Y1, os.path.join(FIG_DIR, 'result1-1.xlsx'))
    r1 = _report_at_times(t, Y1)
    results['linear'] = dict(label=lab1, meta=meta1, at_times=r1,
                             t=list(t), z1=list(Y1[:, 0]), v1=list(Y1[:, 2]),
                             z2=list(Y1[:, 1]), v2=list(Y1[:, 3]))
    print(f'  [线性] t=10s: z1={Y1[50,0]:.6f} v1={Y1[50,2]:.6f} '
          f'z2={Y1[50,1]:.6f} v2={Y1[50,3]:.6f}')

    # ---- 情况2：非线性阻尼 ----
    print('[problem1] 求解 情况2：非线性阻尼 ...')
    t2, Y2, lab2, meta2 = run_case(linear=False)
    _write_xlsx(t2, Y2, os.path.join(FIG_DIR, 'result1-2.xlsx'))
    r2 = _report_at_times(t2, Y2)
    results['nonlinear'] = dict(label=lab2, meta=meta2, at_times=r2,
                                t=list(t2), z1=list(Y2[:, 0]), v1=list(Y2[:, 2]),
                                z2=list(Y2[:, 1]), v2=list(Y2[:, 3]))
    print(f'  [非线性] t=10s: z1={Y2[50,0]:.6f} v1={Y2[50,2]:.6f} '
          f'z2={Y2[50,1]:.6f} v2={Y2[50,3]:.6f}')

    save_json(results, os.path.join(FIG_DIR, 'problem_1_results.json'))
    return results


if __name__ == '__main__':
    main()

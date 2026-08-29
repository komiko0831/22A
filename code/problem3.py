# -*- coding: utf-8 -*-
"""
问题3：浮子-振子垂荡-纵摇四自由度耦合动力学
================================================
中轴底座固定于隔层中心，中轴架经转轴铰接于底座，浮子做垂荡 + 纵摇运动。
建立四自由度（浮子垂荡 z1、振子垂荡 z2、浮子纵摇 θ1、振子纵摇 θ2）运动模型。
直线阻尼器 Cz = 10000 N·s/m、旋转阻尼器 Cθ = 1000 N·m·s 均为常量。
在 f·cos(wt) 与 L·cos(wt) 激励下，计算前 40 个波浪周期、0.2 s 间隔的
垂荡位移/速度与纵摇角位移/角速度，输出 result3.xlsx。
"""
import os
import numpy as np
import openpyxl

from utils import (load_attach3, make_coupled_rhs, solve_rhs,
                   wave_period, save_json)

FIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'figures')


def _write_xlsx(t, Y, path):
    """写 result3.xlsx：8 列状态（浮子/振子 × 垂荡位移/速度/纵摇角/角速度）。"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['时间(s)',
               '浮子垂荡位移(m)', '浮子垂荡速度(m/s)',
               '浮子纵摇角位移(rad)', '浮子纵摇角速度(rad/s)',
               '振子垂荡位移(m)', '振子垂荡速度(m/s)',
               '振子纵摇角位移(rad)', '振子纵摇角速度(rad/s)'])
    for i in range(len(t)):
        ws.append([round(t[i], 6)] + [round(float(Y[i, j]), 8) for j in range(8)])
    wb.save(path)
    print(f'[problem3] 已写 xlsx {path} ({len(t)} 行)')


def main():
    p = load_attach3()[3]
    omega, ma, Ja, Bz, Bth, f, L = (p['omega'], p['ma'], p['Ja'],
                                    p['Bz'], p['Bth'], p['f'], p['L'])
    Cz, Cth = 10000.0, 1000.0           # 直线/旋转阻尼系数（常量）
    T = wave_period(omega)
    t_end = 40 * T
    dt = 0.2
    print(f'[problem3] ω={omega} s^-1, T={T:.4f} s, 40 周期={t_end:.2f} s')

    rhs = make_coupled_rhs(ma, Ja, Bz, Bth, f, L, omega, Cz, Cth)
    y0 = np.zeros(8)                    # 静平衡初始
    t, Y = solve_rhs(rhs, y0, t_end, dt=dt)

    # 状态布局: [z1, z2, θ1, θ2, vz1, vz2, ωθ1, ωθ2]
    _write_xlsx(t, Y, os.path.join(FIG_DIR, 'result3.xlsx'))

    # 论文要求的指定时刻快照
    snap_times = [10.0, 20.0, 40.0, 60.0, 100.0]
    snapshots = {}
    for tt in snap_times:
        idx = int(round(tt / dt))
        snapshots[str(tt)] = dict(
            浮子垂荡位移_m=float(Y[idx, 0]), 浮子垂荡速度_ms=float(Y[idx, 4]),
            浮子纵摇角_rad=float(Y[idx, 2]), 浮子纵摇角速度_rads=float(Y[idx, 6]),
            振子垂荡位移_m=float(Y[idx, 1]), 振子垂荡速度_ms=float(Y[idx, 5]),
            振子纵摇角_rad=float(Y[idx, 3]), 振子纵摇角速度_rads=float(Y[idx, 7]))

    results = dict(
        omega=omega, T=T, Cz=Cz, Cth=Cth,
        meta=dict(ma=ma, Ja=Ja, Bz=Bz, Bth=Bth, f=f, L=L),
        snapshots=snapshots,
        t=list(t),
        z1=list(Y[:, 0]), z2=list(Y[:, 1]),
        theta1=list(Y[:, 2]), theta2=list(Y[:, 3]),
        vz1=list(Y[:, 4]), vz2=list(Y[:, 5]),
        wtheta1=list(Y[:, 6]), wtheta2=list(Y[:, 7]),
    )
    save_json(results, os.path.join(FIG_DIR, 'problem_3_results.json'))

    print('[problem3] t=10s 快照:')
    for k, v in snapshots['10.0'].items():
        print(f'    {k} = {v:.6f}')
    return results


if __name__ == '__main__':
    main()

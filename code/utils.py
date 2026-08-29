# -*- coding: utf-8 -*-
"""
公共工具模块 —— 2022 高教社杯 A 题：波浪能最大输出功率设计
================================================================
提供：
  1. 附件3/附件4 数据读取（含硬编码回退，保证无附件时仍可运行）
  2. 物理/几何常数与派生量（吃水深度、静水恢复系数、转动惯量等）
  3. 二自由度垂荡系统、四自由度垂荡-纵摇系统的质量/阻尼/刚度矩阵
  4. RK45 数值积分求解器（scipy.solve_ivp）
  5. 频域稳态解析解（线性系统，用于快速精确的功率优化）
  6. 平均输出功率计算与 JSON 保存
"""
import os
import json
import numpy as np

# ============================= 物理常数 =============================
RHO = 1025.0      # 海水密度 kg/m^3
G   = 9.8         # 重力加速度 m/s^2

# ============================= 附件4：几何/物理参数 =============================
# 浮子（圆柱壳体 + 圆锥壳体）
M1 = 4866.0       # 浮子质量 kg
R1 = 1.0          # 浮子底半径 m
H1 = 3.0          # 浮子圆柱部分高度 m
HT = 0.8          # 浮子圆锥部分高度 m
# 振子（圆柱体）
M2 = 2433.0       # 振子质量 kg
R2 = 0.5          # 振子半径 m
H2 = 0.5          # 振子高度 m

# ============================= PTO / 结构刚度 =============================
K_Z   = 80000.0       # 直线弹簧刚度 N/m
K_THETA = 250000.0    # 扭转弹簧刚度 N·m
C_THETA_REST = 8890.7 # 静水恢复力矩系数 N·m（纵摇）

# ============================= 附件3：各问题水动力参数 =============================
# 列: 问题, 圆频率, 垂荡附加质量, 纵摇附加转动惯量, 垂荡兴波阻尼, 纵摇兴波阻尼,
#     垂荡激励力振幅, 纵摇激励力矩振幅
_ATTACH3 = {
    1: dict(omega=1.4005, ma=1335.535, Ja=6779.315, Bz=656.3616,
            Bth=151.4388, f=6250.0, L=1230.0),
    2: dict(omega=2.2143, ma=1165.992, Ja=7131.29, Bz=167.8395,
            Bth=2992.724, f=4890.0, L=2560.0),
    3: dict(omega=1.7152, ma=1028.876, Ja=7001.914, Bz=683.4558,
            Bth=654.3383, f=3640.0, L=1690.0),
    4: dict(omega=1.9806, ma=1091.099, Ja=7142.493, Bz=528.5018,
            Bth=1655.909, f=1760.0, L=2140.0),
}


def load_attach3():
    """从附件3.xlsx读取各问题水动力参数；文件缺失时用硬编码回退。"""
    import openpyxl
    path = os.path.join(os.path.dirname(__file__), '..', 'A题', '附件3.xlsx')
    path = os.path.abspath(path)
    data = {}
    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        for r in rows[1:]:
            if r is None or r[0] is None:
                continue
            key = int(str(r[0]).replace('问题', ''))
            data[key] = dict(omega=float(r[1]), ma=float(r[2]), Ja=float(r[3]),
                             Bz=float(r[4]), Bth=float(r[5]), f=float(r[6]),
                             L=float(r[7]))
    except Exception as e:
        print(f"[utils] 附件3读取失败，使用硬编码参数 ({e})")
        data = _ATTACH3
    return data


# ============================= 派生几何/水动力常数 =============================
# 垂荡静水恢复力系数 C_h = rho*g*pi*R1^2
C_H = RHO * G * np.pi * R1 ** 2          # ≈ 31557.3 N/m


def _float_inertia():
    """浮子绕隔层转轴的纵摇转动惯量 J1（圆柱薄壳 + 圆锥薄壳）。"""
    lt = np.sqrt(R1 ** 2 + HT ** 2)      # 圆锥母线长
    S_c = 2 * np.pi * R1 * H1            # 圆柱侧面积
    S_t = np.pi * R1 * lt                # 圆锥侧面积
    m_c = M1 * S_c / (S_c + S_t)
    m_t = M1 - m_c
    J_c = m_c * (R1 ** 2 / 2 + H1 ** 2 / 3)
    J_t = m_t * (R1 ** 2 / 4 + HT ** 2 / 6)
    return J_c + J_t


def _osc_inertia():
    """振子绕隔层转轴的纵摇转动惯量 J2（平行轴定理）。"""
    x_eq = M2 * G / K_Z                    # 静平衡弹簧伸长量 ≈ 0.298 m
    l_eq = H2 / 2 + x_eq + 0.5             # 振子质心到转轴距离（弹簧原长0.5m）
    l_eq = 0.7980                          # 建模思路给定静平衡距离
    J_center = M2 / 12 * (3 * R2 ** 2 + H2 ** 2)
    return J_center + M2 * l_eq ** 2


J1 = _float_inertia()          # ≈ 14340.7 kg·m^2
J2 = _osc_inertia()            # ≈ 1752.3  kg·m^2
X_EQ = M2 * G / K_Z            # 振子静平衡伸长量 ≈ 0.2980 m


# ============================= 矩阵构建 =============================
def heave_matrices(ma, Bz, C_pto):
    """二自由度垂荡系统质量/阻尼/刚度矩阵（线性阻尼 C_pto）。"""
    M = np.array([[M1 + ma, 0.0],
                  [0.0, M2]])
    Cd = np.array([[Bz + C_pto, -C_pto],
                   [-C_pto, C_pto]])
    K = np.array([[C_H + K_Z, -K_Z],
                  [-K_Z, K_Z]])
    return M, Cd, K


def coupled_matrices(ma, Ja, Bz, Bth, Cz, Cth):
    """四自由度垂荡-纵摇系统（解耦分块）质量/阻尼/刚度矩阵。"""
    M = np.diag([M1 + ma, M2, J1 + Ja, J2])
    Cd = np.array([
        [Bz + Cz, -Cz, 0.0, 0.0],
        [-Cz, Cz, 0.0, 0.0],
        [0.0, 0.0, Bth + Cth, -Cth],
        [0.0, 0.0, -Cth, Cth],
    ])
    K = np.array([
        [C_H + K_Z, -K_Z, 0.0, 0.0],
        [-K_Z, K_Z, 0.0, 0.0],
        [0.0, 0.0, C_THETA_REST + K_THETA, -K_THETA],
        [0.0, 0.0, -K_THETA, K_THETA],
    ])
    return M, Cd, K


# ============================= 动力学右端函数 =============================
def make_heave_rhs(ma, Bz, f_amp, omega, C_pto=None,
                   nonlinear=False, alpha=None, P=None):
    """返回闭包形式的垂荡 ODE 右端（绑定激励力振幅与频率）。"""
    def rhs(t, y):
        z = y[0:2]
        v = y[2:4]
        vrel = v[1] - v[0]                      # 振子相对浮子速度 z2'-z1'
        if nonlinear:
            fdamp_pto = alpha * np.abs(vrel) ** P * vrel   # 非线性 PTO 阻尼力
        else:
            fdamp_pto = C_pto * vrel            # 线性 PTO 阻尼力
        # 浮子: 兴波阻尼 -Bz*v1 + PTO 阻尼 +C*vrel
        # 振子: PTO 阻尼 -C*vrel（等大反向）
        f_damp = np.array([-Bz * v[0] + fdamp_pto, -fdamp_pto])
        f_spring = np.array([
            -C_H * z[0] - K_Z * (z[0] - z[1]),   # 浮子: 静水恢复 + 弹簧
            -K_Z * (z[1] - z[0]),                # 振子: 弹簧
        ])
        f_exc = np.array([f_amp * np.cos(omega * t), 0.0])
        M = np.array([[M1 + ma, 0.0], [0.0, M2]])
        a = np.linalg.solve(M, f_exc + f_damp + f_spring)
        return np.concatenate([v, a])
    return rhs


def make_coupled_rhs(ma, Ja, Bz, Bth, f_amp, L_amp, omega, Cz, Cth):
    """四自由度垂荡-纵摇系统 ODE 右端（线性阻尼 Cz, Cth）。

    y = [z1, z2, theta1, theta2, vz1, vz2, vth1, vth2]。
    """
    M, Cd, K = coupled_matrices(ma, Ja, Bz, Bth, Cz, Cth)
    Minv = np.linalg.inv(M)

    def rhs(t, y):
        x = y[0:4]     # 位移/角位移
        v = y[4:8]     # 速度/角速度
        F = np.array([f_amp * np.cos(omega * t), 0.0,
                      L_amp * np.cos(omega * t), 0.0])
        a = Minv @ (F - Cd @ v - K @ x)
        return np.concatenate([v, a])
    return rhs


# ============================= 数值积分 =============================
def solve_rhs(rhs, y0, t_end, dt=0.2, periods=40, omega=None,
              rtol=1e-8, atol=1e-10):
    """RK45 积分，输出固定 dt 时间网格的解。

    返回 (t, Y)。Y 每行对应一个时刻的状态。
    优化类问题可放宽 rtol/atol 以加速（如 1e-6 / 1e-8）。
    """
    from scipy.integrate import solve_ivp
    n = int(round(t_end / dt)) + 1
    t_eval = np.arange(0.0, t_end + 0.5 * dt, dt)
    t_eval = t_eval[t_eval <= t_end + 1e-12]
    sol = solve_ivp(rhs, (0.0, t_end), y0, method='RK45',
                    t_eval=t_eval, rtol=rtol, atol=atol, max_step=dt)
    return sol.t, sol.y.T


# ============================= 频域稳态解析解 =============================
def steady_state_amplitude(M, Cd, K, F0, omega):
    """线性系统 M x'' + Cd x' + K x = F0 cos(wt) 的稳态复振幅。"""
    Z = -omega ** 2 * M + 1j * omega * Cd + K
    return np.linalg.solve(Z, F0)


def heave_steady_power(ma, Bz, f_amp, omega, C_pto):
    """垂荡二自由度线性系统稳态平均输出功率（解析，精确）。"""
    M, Cd, K = heave_matrices(ma, Bz, C_pto)
    F0 = np.array([f_amp, 0.0])
    Z = steady_state_amplitude(M, Cd, K, F0, omega)
    vrel = 1j * omega * (Z[1] - Z[0])
    return 0.5 * C_pto * np.abs(vrel) ** 2


def coupled_steady_power(ma, Ja, Bz, Bth, f_amp, L_amp, omega, Cz, Cth):
    """四自由度线性系统稳态平均输出功率 = 垂荡功率 + 纵摇功率（解析）。"""
    M, Cd, K = coupled_matrices(ma, Ja, Bz, Bth, Cz, Cth)
    F0 = np.array([f_amp, 0.0, L_amp, 0.0])
    Z = steady_state_amplitude(M, Cd, K, F0, omega)
    vrel_heave = 1j * omega * (Z[1] - Z[0])
    vrel_pitch = 1j * omega * (Z[3] - Z[2])
    P_heave = 0.5 * Cz * np.abs(vrel_heave) ** 2
    P_pitch = 0.5 * Cth * np.abs(vrel_pitch) ** 2
    return P_heave, P_pitch, P_heave + P_pitch


# ============================= 平均功率（时域） =============================
def time_domain_avg_power(y, dt, C_pto=None, nonlinear=False, alpha=None, P=None):
    """由时域解计算平均 PTO 输出功率。

    y: [N, 4] = [z1, z2, v1, v2]（仅垂荡）。
    线性：P = C * vrel^2；非线性：P = alpha * |vrel|^(P+2)。
    """
    vrel = y[:, 3] - y[:, 2]
    if nonlinear:
        p = alpha * np.abs(vrel) ** (P + 2)
    else:
        p = C_pto * vrel ** 2
    return float(np.mean(p))


# ============================= 保存工具 =============================
def save_json(obj, path):
    """保存 JSON（确保 NaN/Inf 被安全处理）。"""
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    def _clean(o):
        if isinstance(o, dict):
            return {k: _clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [_clean(v) for v in o]
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        if isinstance(o, (np.ndarray,)):
            return _clean(o.tolist())
        if isinstance(o, float) and (np.isnan(o) or np.isinf(o)):
            return None
        return o

    with open(path, 'w', encoding='utf-8') as fp:
        json.dump(_clean(obj), fp, ensure_ascii=False, indent=2)
    print(f"[utils] 已保存 {path} ({os.path.getsize(path)} bytes)")


def wave_period(omega):
    return 2.0 * np.pi / omega


if __name__ == '__main__':
    print(f"垂荡静水恢复系数 C_h  = {C_H:.4f} N/m")
    print(f"浮子纵摇转动惯量 J1    = {J1:.4f} kg·m^2")
    print(f"振子纵摇转动惯量 J2    = {J2:.4f} kg·m^2")
    print(f"振子静平衡伸长量 x_eq  = {X_EQ:.4f} m")
    print(f"吃水深度（静平衡）     = {np.cbrt((M1 + M2) * G / (RHO * G * np.pi * R1 ** 2)) if False else '见建模思路 ≈ 2.80 m'}")
    a3 = load_attach3()
    print("附件3 加载:", {k: v['omega'] for k, v in a3.items()})

#!/usr/bin/env python3
"""
verify_00potential.py — TTT-Fusion 機構A（00ポテンシャル）の独立検証

theory_core.md §4.2 の式と experiment_design.md §6.2 のパラメータ範囲を
そのまま用いて、docs/falsification_00potential.md の全数値を再現する。

依存: numpy, scipy のみ。   実行: python3 verify_00potential.py
"""
import numpy as np
from scipy.integrate import quad

# ---- 物理定数（CODATA 2022 / PDG） -----------------------------------------
e     = 1.602176634e-19      # C
eps0  = 8.8541878188e-12     # F/m
c     = 299792458.0          # m/s
mp    = 1.67262192595e-27    # kg
me    = 9.1093837139e-31     # kg
hbar  = 1.054571817e-34      # J*s
hbarc = 197.3269804          # MeV*fm
e2    = 1.43996454           # MeV*fm  (e^2/4pi eps0)
mu_dd = 2.01410177784 * 931.49410372 / 2   # MeV/c^2, d+d の換算質量

E_INC = 0.010                # MeV = 10 keV
R_HE, V0, R0 = 1.7, 50.0, 1.5   # fm, MeV, fm  (theory_core.md §4.2)


# ---- ポテンシャル -----------------------------------------------------------
def V_base(R):
    """クーロン + 湯川型核力"""
    return e2 / R - V0 * np.exp(-(R / R0) ** 2)


def V_ttt(R, k00=0.0, V00=0.0):
    """theory_core.md §4.2 の boxed 式そのまま"""
    return V_base(R) + 0.5 * k00 * (R - R_HE) ** 2 - V00


def V_local(R, V00=0.0, w=1.0):
    """最大限譲歩した版：局在したガウス井戸に置き換え"""
    return V_base(R) - V00 * np.exp(-((R - R_HE) / w) ** 2)


# ---- WKB --------------------------------------------------------------------
def turning_points(f, lo=0.3, hi=3000.0, n=2_000_000):
    R = np.linspace(lo, hi, n)
    s = np.sign(f(R))
    return R[np.where(np.diff(s) != 0)[0]]


def ln_P(f):
    """WKB: ln P = -(2/hbar) * int sqrt(2 mu (V-E)) dR

    遠方で V > E のまま発散する場合は外側転回点が存在せず、障壁は無限に続く。
    """
    if f(3000.0) > E_INC:            # 束縛されたまま：自由領域に出られない
        return None, turning_points(lambda R: f(R) - E_INC)
    tp = turning_points(lambda R: f(R) - E_INC)
    if len(tp) < 2:
        return None, tp
    R1, R2 = tp[0], tp[-1]
    I, _ = quad(lambda x: np.sqrt(max(2 * mu_dd * (f(x) - E_INC), 0.0)),
                R1, R2, limit=600)
    return -2 * I / hbarc, (R1, R2)


# ---- §2 k00 項の符号 --------------------------------------------------------
print("=" * 74)
print("§2  k00 項の符号   (d+d, E = 10 keV)")
print("=" * 74)
print(f"{'設定':28s} {'内側':>10s} {'外側':>12s} {'幅':>10s} {'ln P':>10s}")
for label, kw in [("従来（00項なし）",        dict()),
                  ("k00 = 10 MeV/fm^2",       dict(k00=10.0)),
                  ("k00 = 100 MeV/fm^2",      dict(k00=100.0)),
                  ("V00 = 0.5 MeV（定数のみ）", dict(V00=0.5))]:
    L, tp = ln_P(lambda R: V_ttt(R, **kw))
    if L is None:
        n_in = f"{tp[0]:.2f} fm" if len(tp) >= 1 else "存在しない"
        print(f"{label:28s} {n_in:>10s} {'存在しない':>12s} {'inf':>10s} {'-inf':>10s}")
    else:
        print(f"{label:28s} {tp[0]:>7.2f} fm {tp[1]:>9.1f} fm "
              f"{tp[1]-tp[0]:>7.1f} fm {L:>10.3f}")

Rs = np.linspace(0.6, 50, 200000)
print(f"\n  V_max (R<50fm):  従来 = {V_ttt(Rs).max():.3f} MeV   "
      f"k00=10 -> {V_ttt(Rs, k00=10.).max():.1f} MeV   "
      f"比 = {V_ttt(Rs, k00=10.).max()/V_ttt(Rs).max():.0f} 倍")

# ---- §3 最大限譲歩した局在井戸 ---------------------------------------------
print("\n" + "=" * 74)
print("§3  局在したガウス井戸（幅 1 fm）に置き換えた場合")
print("=" * 74)
L0, _ = ln_P(V_base)
for V00 in [0.0, 0.1, 0.5, 1.0]:
    L, _ = ln_P(lambda R: V_local(R, V00))
    print(f"  V00 = {V00:4.1f} MeV -> ln P = {L:8.3f}   増強 = {np.exp(L - L0):.2f} 倍")
print(f"\n  外側転回点 R2 = e^2/E = {e2/E_INC:.0f} fm  <- WKB積分を支配しているのはここ")

# ---- §4.1 スケール ----------------------------------------------------------
print("\n" + "=" * 74)
print("§4.1  波長と核子間距離   (R = 2 fm)")
print("=" * 74)
R_fm = 2e-15
for name, f in [("S-Band", 2.4e9), ("W-Band", 9.0e10),
                ("THz-Band", 3.0e11), ("Optical", 1.93e14)]:
    lam = c / f
    print(f"  {name:10s} lambda = {lam:9.3e} m   (kR)^2 = {(2*np.pi*R_fm/lam)**2:.2e}")

# ---- §4.2 必要な電場 --------------------------------------------------------
print("\n" + "=" * 74)
print("§4.2  必要な電場")
print("=" * 74)
F_req = 1.602176634e-13 / 1e-15          # 1 MeV / 1 fm  [N]
E_req = F_req / e
E_sch = me**2 * c**3 / (e * hbar)        # Schwinger 臨界電場
print(f"  必要電場          = {E_req:.3e} V/m")
print(f"  陽子の1fmでの場   = {e/(4*np.pi*eps0*(1e-15)**2):.3e} V/m")
print(f"  Schwinger 臨界場  = {E_sch:.3e} V/m   -> 必要/E_S = {E_req/E_sch:.0f} 倍")
I_req = 0.5 * eps0 * c * E_req**2
print(f"  対応レーザー強度  = {I_req/1e4:.2e} W/cm^2   (現行記録 ~1e23 W/cm^2)")

print("\n  ポンデロモーティブポテンシャル U_p = e^2 E0^2 / (4 m_p omega^2), E0 = 1e8 V/m:")
for name, f in [("S-Band", 2.4e9), ("THz-Band", 3.0e11), ("Optical", 1.93e14)]:
    w = 2 * np.pi * f
    print(f"    {name:10s} U_p = {e**2*(1e8)**2/(4*mp*w**2)/e:.3e} eV")

# ---- §5 電子遮蔽 ------------------------------------------------------------
print("\n" + "=" * 74)
print("§5  電子遮蔽による増強   f = exp( (1/2) sqrt(E_G/E) * U_e / E )")
print("=" * 74)
EG = 986.1  # keV, d+d の Gamow エネルギー
print(f"{'E [keV]':>9s} {'R2 [fm]':>10s} {'f (Ue=25eV)':>13s} {'f (Ue=300eV)':>14s}")
for Ek in [1, 2, 5, 10, 30]:
    row = [np.exp(0.5 * np.sqrt(EG / Ek) * Ue / Ek) for Ue in (0.025, 0.300)]
    print(f"{Ek:>9d} {e2/(Ek/1000):>10.0f} {row[0]:>13.2f} {row[1]:>14.2f}")

print("\n結論: 機構A（00ポテンシャル）は棄却。障壁に効くのは R2 を動かす遮蔽であり、"
      "\n      幾何学を置くべきスケールは fm ではなく pm。")

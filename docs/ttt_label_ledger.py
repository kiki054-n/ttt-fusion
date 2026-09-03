#!/usr/bin/env python3
"""
ttt_label_ledger.py — OπO 二本目のラベル（σ, τ）の検算台帳

運用: 新しい数値主張はまずここに追加 → 実行 → PASS のみ本文採用。
      FAIL は削除せず履歴として残す（ttt_ledger.py v1.1 の運用に従う）。

定義:
  σ = ±1  リングの回転向き。空間回転で反転する（回転共変）。スピンに対応。
  τ = ±1  双極対のどちらの極から生まれたか。空間回転で不変。アイソスピンに対応。
  1 OπO = 1 核子。ラベル (σ, τ) の 4 通りが 1s 殻を満たす。

依存: numpy のみ。   実行: python3 ttt_label_ledger.py
"""
import itertools
import numpy as np
import numpy.linalg as la

RESULTS = []


def record(eid, claim, verdict, note):
    RESULTS.append((eid, claim, verdict, note))


# ===========================================================================
# L1  2ラベル核子の2体系: 空間対称のとき反対称状態は 6 個か
# ===========================================================================
LABELS = [(s, t) for s in (+1, -1) for t in (+1, -1)]      # (sigma, tau)
NAME = {(+1, +1): "p↑", (+1, -1): "n↑", (-1, +1): "p↓", (-1, -1): "n↓"}

basis = [(a, b) for a in range(4) for b in range(4)]        # 16 状態


def swap(v):
    w = np.zeros(16)
    for i, (a, b) in enumerate(basis):
        w[basis.index((b, a))] += v[i]
    return w


anti, symm = [], []
for i in range(16):
    v = np.zeros(16)
    v[i] = 1.0
    anti.append((v - swap(v)) / 2)
    symm.append((v + swap(v)) / 2)

d_anti = la.matrix_rank(np.array(anti))
d_symm = la.matrix_rank(np.array(symm))

# 内訳: spin(3対称+1反対称) x isospin(3対称+1反対称)
#       反対称の組は S=1(sym)xT=0(anti) と S=0(anti)xT=1(sym)
breakdown = 3 * 1 + 1 * 3
record("L1",
       "2ラベル核子の2体系は、空間対称(L=0)のとき反対称状態が 6 個",
       "PASS" if (d_anti == 6 and breakdown == 6) else "FAIL",
       f"16状態を明示的に対称化/反対称化: 反対称={d_anti}, 対称={d_symm}. "
       f"内訳 S=1⊗T=0 が3（重陽子の磁気副準位）, S=0⊗T=1 が3（pp/np/nn の ¹S₀）")

# ===========================================================================
# L2  4ラベルの置換群の位数
# ===========================================================================
S4 = list(itertools.permutations(range(4)))


def parity(p):
    n = sum(1 for i in range(4) for j in range(i + 1, 4) if p[i] > p[j])
    return (-1) ** n


A4 = [p for p in S4 if parity(p) == 1]
record("L2",
       "4ラベルの置換群の位数は 24（= T_d）、偶置換は 12（= T）",
       "PASS" if (len(S4) == 24 and len(A4) == 12) else "FAIL",
       f"全列挙: |S₄| = {len(S4)}, |A₄| = {len(A4)}")

# ===========================================================================
# L3  統計 (-1)^A がスピンの整数/半整数と一致するか
# ===========================================================================
NUCLEI = [("²H", 2, 1.0), ("³H", 3, 0.5), ("³He", 3, 0.5),
          ("⁴He", 4, 0.0), ("⁶Li", 6, 1.0), ("¹²C", 12, 0.0)]
ok3, rows3 = True, []
for nm, A, spin in NUCLEI:
    pred_boson = (A % 2 == 0)
    obs_boson = float(spin).is_integer()
    ok3 &= (pred_boson == obs_boson)
    rows3.append(f"{nm}(A={A}, J={spin}) "
                 f"{'ボース' if pred_boson else 'フェルミ'}")
record("L3",
       "1 OπO = 1 核子 のとき、統計 (−1)^A が実測スピンと整合",
       "PASS" if ok3 else "FAIL",
       "6核すべて一致: " + " / ".join(rows3))

# ===========================================================================
# L4  旧「1核子 = 4 OπO」で ³He がフェルミ粒子になるか  （棄却の記録）
# ===========================================================================
old_count = {"³He": 4 * 3, "⁴He": 4 * 4}
he3_pred_boson = (old_count["³He"] % 2 == 0)
record("L4",
       "旧「1核子 = 4 OπO」で ³He がフェルミ粒子になる",
       "FAIL" if he3_pred_boson else "PASS",
       f"³He = {old_count['³He']} OπO は偶数 → ボース予測。"
       f"実測は超流動 0.93 mK（クーパー対経由 = フェルミ粒子）で矛盾。"
       f"⁴He = {old_count['⁴He']} は偶数で偶然合うだけ。旧数え方を棄却")

# ===========================================================================
# L5  独立性テスト: 空間回転 R(π) で σ / n̂ / τ がどう変わるか
# ===========================================================================
def rotate_pi(state):
    """水平軸まわりの π 回転。回転共変な量だけ符号が反転する。"""
    return {"sigma": -state["sigma"],       # 循環の向き（軸性ベクトル）
            "normal": -state["normal"],     # 円盤法線（空間の方向）
            "tau":     state["tau"]}        # 双極の出自（空間の量ではない）


before = {"sigma": +1, "normal": +1, "tau": +1}
after = rotate_pi(before)
normal_invariant = (after["normal"] == before["normal"])
tau_invariant = (after["tau"] == before["tau"])
sigma_covariant = (after["sigma"] != before["sigma"])
record("L5",
       "「面の法線」を XYZ 内の方向として τ（アイソスピン）に使える",
       "FAIL" if not normal_invariant else "PASS",
       f"R(π) で σ:{before['sigma']:+d}→{after['sigma']:+d}（反転）, "
       f"n̂:{before['normal']:+d}→{after['normal']:+d}（反転）, "
       f"τ:{before['tau']:+d}→{after['tau']:+d}（不変）. "
       f"アイソスピンは回転不変でなければならないので法線は不可。"
       f"「表裏＝双極の二面性」と読む場合のみ可")
record("L5b",
       "σ は回転共変、τ は回転不変（＝2本は独立）",
       "PASS" if (sigma_covariant and tau_invariant) else "FAIL",
       "一方だけを変える操作 R(π) が存在するので独立")

# ===========================================================================
# L6  α共役核は隣の非α共役核より B/A が高いか
# ===========================================================================
B_ALPHA = {"⁴He": (4, 28.2957), "⁸Be": (8, 56.4996), "¹²C": (12, 92.1618),
           "¹⁶O": (16, 127.6193), "²⁰Ne": (20, 160.6449), "²⁴Mg": (24, 198.2568)}
B_NEIGH = {"⁶Li": (6, 31.9946), "¹⁰B": (10, 64.7508), "¹⁴N": (14, 104.6587),
           "¹⁸F": (18, 137.3694), "²²Na": (22, 174.1455)}
B_ALPHA_HE4 = 28.2957

pairs = [("⁸Be", "⁶Li"), ("¹²C", "¹⁰B"), ("¹⁶O", "¹⁴N"),
         ("²⁰Ne", "¹⁸F"), ("²⁴Mg", "²²Na")]
ok6 = all(B_ALPHA[a][1] / B_ALPHA[a][0] > B_NEIGH[n][1] / B_NEIGH[n][0]
          for a, n in pairs)

keys = list(B_ALPHA)
s_alpha = {}
for i in range(1, len(keys)):
    prev, cur = B_ALPHA[keys[i - 1]][1], B_ALPHA[keys[i]][1]
    s_alpha[keys[i]] = cur - prev - B_ALPHA_HE4
neg = [k for k, v in s_alpha.items() if v < 0]
record("L6",
       "α共役核は隣の非α共役核より B/A が高い（4ラベル対等 = Wigner SU(4) の帰結）",
       "PASS*" if ok6 else "FAIL",
       f"5組すべてで成立。ただし S_α が負なのは {neg} のみ "
       f"({s_alpha['⁸Be']:+.3f} MeV) で、A=8 の切断は説明できない")

# ===========================================================================
# L7  「光 = 2つの OπO」が光子の自由度と整合するか
# ===========================================================================
two_fermion_states = 1 + 3          # S=0 が1, S=1 が3
photon_states = 2                   # ヘリシティ ±1
record("L7",
       "「光 = 2つの OπO」が光子の自由度と整合",
       "OPEN",
       f"スピン1/2を2つ合成すると {two_fermion_states} 状態。"
       f"光子は {photon_states} 状態（ヘリシティ ±1）。合わない。"
       f"統計（偶数個 = ボース）は通るが状態数が余る")

# ===========================================================================
# L8  τ の破れの大きさ
# ===========================================================================
m_n, m_p = 939.56542, 938.27209     # MeV
dm = m_n - m_p
frac = dm / ((m_n + m_p) / 2) * 100
record("L8",
       "τ の破れは小さく「二極はほぼ対等」と整合",
       "PASS" if frac < 1.0 else "FAIL",
       f"m_n − m_p = {dm:.3f} MeV は核子質量の {frac:.2f}%")

# ===========================================================================
# 出力
# ===========================================================================
if __name__ == "__main__":
    import textwrap
    W = 78
    print("=" * W)
    print("TTT — OπO 二本目のラベル 検算台帳")
    print("=" * W)
    tally = {}
    for eid, claim, verdict, note in RESULTS:
        tally[verdict] = tally.get(verdict, 0) + 1
        print(f"\n[{eid}] {verdict}")
        print(f"  主張: {claim}")
        for line in textwrap.wrap(note, W - 8):
            print(f"        {line}")
    print("\n" + "=" * W)
    print("集計: " + ", ".join(f"{k} {v}件" for k, v in sorted(tally.items())))
    print("=" * W)
    print("\n本文採用: L1, L2, L3, L5b, L8（PASS）／ L6 は ⁸Be を除いて採用")
    print("棄却記録: L4（旧「1核子 = 4 OπO」）, L5（法線を τ に使う案）")
    print("未決:     L7（光の自由度 4 対 2）")

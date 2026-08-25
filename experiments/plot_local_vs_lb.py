"""local validation vs LB 相関図の再生成（冪等）。

データ点は README.md の実験ログ・コンペ提出ログに基づく。
使い方: uv run python experiments/plot_local_vs_lb.py
新しい点を追加するときは POINTS に (name, local_avg, lb) を足すだけ。
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# (name, local_avg, LB public score)
POINTS: list[tuple[str, float, float]] = [
    ("exp2", 50.355, 85.680),
    ("exp5", 49.14, 80.460),
    ("exp6", 35.67, 58.495),
    ("exp7", 39.64, 50.550),
    ("exp7b", 38.755, 53.860),
    ("exp8b", 51.57, 75.960),
    ("exp12", 51.975, 87.075),
    ("exp14", 52.92, 86.130),
    ("exp15", 44.865, 75.960),
    ("exp17", 53.685, 89.910),
    ("exp19", 53.325, 89.370),
    ("exp27", 56.925, 86.355),
    ("exp31", 58.2, 95.220),   # 合成推定: gpt_oss 66.22 + gemma 単発 fallback 50.22 の平均
    ("exp32", 59.56, 94.970),  # 合成推定: gpt_oss 68.90 + gemma 単発 fallback 50.22 の平均
]

# (name, local_avg, LB, note) — raw/件経済が EXFIL 系（18 raw/件）と異なるため回帰には含めない
REFERENCE_POINTS: list[tuple[str, float, float, str]] = [
    ("exp34", 5.475, 9.405, "cd_2msg 純粋CD: 6 raw/件。local は生成律速・hosted は replay 律速"),
    ("exp37", 10.39, 18.310, "cd_burst8 race: 34 raw/件。exp34 の約2倍（local→LB 比 1.76 で予測通り）"),
]

OUT = Path(__file__).parent / "local_vs_lb_correlation.png"


def main() -> None:
    local = np.array([p[1] for p in POINTS])
    lb = np.array([p[2] for p in POINTS])
    n = len(POINTS)

    slope, intercept, r, p_value, _ = stats.linregress(local, lb)
    rho, p_rho = stats.spearmanr(local, lb)

    fig, ax = plt.subplots(figsize=(8.5, 6))
    ax.scatter(local, lb, s=42, zorder=3, label=f"submissions (n={n})")
    for name, x, y in POINTS:
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(5, 4), fontsize=8)

    xs = np.linspace(local.min() - 2, local.max() + 2, 100)
    ax.plot(xs, intercept + slope * xs, "r--", alpha=0.7,
            label=f"LB = {intercept:.1f} + {slope:.2f} x local")

    for name, x, y, note in REFERENCE_POINTS:
        ax.scatter([x], [y], s=60, marker="D", zorder=4, label=f"{name} (reference)")
        ax.annotate(name, (x, y), textcoords="offset points", xytext=(5, 4), fontsize=8)

    ax.set_xlabel("local validation score (avg of 2 models, 600s/model)")
    ax.set_ylabel("LB public score")
    ax.set_title(f"local vs LB  (Pearson r={r:.2f} p={p_value:.1e}, Spearman rho={rho:.2f} p={p_rho:.1e})")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT, dpi=120)
    print(f"saved {OUT}")
    print(f"n={n}  LB = {intercept:.2f} + {slope:.3f} x local")
    print(f"Pearson r={r:.3f} (p={p_value:.2e})  Spearman rho={rho:.3f} (p={p_rho:.2e})")


if __name__ == "__main__":
    main()

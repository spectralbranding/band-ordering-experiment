# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "matplotlib"]
# ///
"""Figure for E2. Reads output/e2_max_delay_rows.csv.

Plots the paired fast-minus-mid difference in Arm B against the band, one line per
delay horizon. Where a line crosses zero is where the ordering inverts. Every line
crosses; the horizon moves where the crossing falls, not whether there is one.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "output"
df = pd.read_csv(OUT / "e2_max_delay_rows.csv")
T95 = 2.262  # t(.975, df=9)

FAST, MID = "esn-fast (leak 1.0)", "esn-mid (leak 0.3)"
BANDS = (1, 2, 4, 8)
DELAYS = (2, 4, 8, 16, 32)
SHADES = ("#d0d0d0", "#a0a0a0", "#c1462c", "#5a5a5a", "#1b1b1b")

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4), sharey=True)

for ax, n_fixed in zip(axes, (350, 2800)):
    for d, shade in zip(DELAYS, SHADES):
        means, errs = [], []
        for k in BANDS:
            sel = df[
                (df.n == n_fixed)
                & (df.arm == "B-drive")
                & (df.band_k == k)
                & (df.max_delay == d)
            ]
            f = sel[sel.substrate == FAST].sort_values("seed").ipc.to_numpy()
            m = sel[sel.substrate == MID].sort_values("seed").ipc.to_numpy()
            diff = f - m
            means.append(diff.mean())
            errs.append(T95 * diff.std(ddof=1) / np.sqrt(len(diff)))
        feasible = bool(df[(df.n == n_fixed) & (df.max_delay == d)].feasible.iloc[0])
        ax.errorbar(
            BANDS,
            means,
            yerr=errs,
            color=shade,
            marker="o" if d == 8 else "s",
            ls="-" if feasible else ":",
            lw=2.2 if d == 8 else 1.5,
            ms=6 if d == 8 else 4.5,
            capsize=3,
            elinewidth=1.0,
            label=f"max_delay {d}" + ("" if feasible else "  (infeasible)"),
        )
    ax.axhline(0, color="#000", lw=1.0, ls="--", alpha=0.7)
    ax.set_xscale("log", base=2)
    ax.set_xticks(list(BANDS))
    ax.set_xticklabels(["1x", "2x", "4x", "8x"])
    ax.set_xlabel("observation band (sampling interval)")
    ax.set_title(f"n = {n_fixed}", fontsize=10, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.25, lw=0.6)

axes[0].set_ylabel("Arm B capacity difference, fastest minus middle")
axes[0].legend(frameon=False, fontsize=8.0, loc="lower left")
fig.suptitle(
    "E2 – the inversion survives every delay horizon; the horizon moves where it happens",
    fontsize=11.5,
    x=0.02,
    ha="left",
    weight="bold",
)
fig.text(
    0.02,
    -0.07,
    "Paired per-seed difference between the fastest and middle substrate in Arm B, 10 seeds, bars are 95% CI. "
    "Crossing zero is the inversion.\n"
    "Every horizon crosses, at both sample budgets, in 10 of 10 seeds – so the published Arm A / Arm B distinction "
    "is not an artefact of holding max_delay at 8 (bold line).\n"
    "But the crossing moves: a longer horizon inverts the ordering at a finer band and reverses all three substrates "
    "rather than only demoting the fastest.\n"
    "The n = 350 and n = 2800 panels agree, including for the horizon that is infeasible at the smaller budget "
    "(dotted), so none of this is estimator bias.",
    fontsize=8.2,
    color="#555",
)
fig.tight_layout(rect=[0, 0.04, 1, 0.94])
fig.savefig(OUT / "figures" / "e2_max_delay.png", dpi=200, bbox_inches="tight")
print(f"wrote {OUT / 'figures' / 'e2_max_delay.png'}")

# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "matplotlib"]
# ///
"""Figure for E1. Reads output/e1_architecture_rows.csv."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "output"
df = pd.read_csv(OUT / "e1_architecture_rows.csv")
T95 = 2.262  # t(.975, df=9)

SHADES = ("#1b1b1b", "#6b6b6b", "#a8a8a8")
MARKERS = ("o", "s", "^")

FAMILIES = [
    ("esn", "Leaky echo-state network\n(first-order leak)"),
    ("mass-spring", "Damped Duffing oscillator bank\n(second-order resonant)"),
]
ARMS = [
    ("A-readout", "A. Read less often"),
    ("B-drive", "B. Drive and read slower"),
]

fig, axes = plt.subplots(2, 2, figsize=(10.5, 8.0), sharex=True)

for r, (fam, fam_label) in enumerate(FAMILIES):
    sub_f = df[df.family == fam]
    order = (
        sub_f.groupby("substrate").tau_drive_steps.first().sort_values().index.tolist()
    )
    ymax = sub_f.ipc.max() * 1.12
    for c, (arm, arm_label) in enumerate(ARMS):
        ax = axes[r][c]
        grp_arm = sub_f[sub_f.arm == arm]
        for i, name in enumerate(order):
            agg = (
                grp_arm[grp_arm.substrate == name]
                .groupby("band_k")
                .ipc.agg(["mean", "std", "count"])
                .reset_index()
            )
            err = (T95 * agg["std"] / agg["count"] ** 0.5).fillna(0)
            ax.errorbar(
                agg.band_k,
                agg["mean"],
                yerr=err,
                color=SHADES[i],
                marker=MARKERS[i],
                lw=1.8,
                ms=6,
                capsize=3,
                elinewidth=1.1,
                label=name,
            )
        ax.set_xscale("log", base=2)
        ax.set_xticks([1, 2, 4, 8])
        ax.set_xticklabels(["1x", "2x", "4x", "8x"])
        ax.set_ylim(0, ymax)
        ax.set_title(f"{arm_label}", fontsize=10, loc="left")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(alpha=0.25, lw=0.6)
        ax.legend(frameon=False, fontsize=8.0, loc="upper right")
        if r == 1:
            ax.set_xlabel("observation band (sampling interval)")
    axes[r][0].set_ylabel(f"{fam_label}\n\ntotal capacity", fontsize=9)

fig.suptitle(
    "E1 – the Arm B inversion replicates on a second architecture; "
    "Arm A's innocence does not",
    fontsize=11.5,
    x=0.02,
    ha="left",
    weight="bold",
)
fig.text(
    0.02,
    -0.07,
    "Two architecture families, three substrates each, differing only in time constant. "
    "Mean of 10 seeds on identical drives, bars are 95% CI, n held fixed at 350.\n"
    "Top row: in the ESN family, decimating the readout (A) reorders nothing while slowing "
    "the drive (B) inverts the ordering – the published result.\n"
    "Bottom row: in the oscillator family, slowing the drive inverts it again (10 of 10 seeds), "
    "but decimating the readout ALSO costs the fastest substrate its top rank,\n"
    "because a resonant substrate read below twice its oscillation frequency is aliased. "
    "A leaky integrator has no oscillation and no such limit.",
    fontsize=8.2,
    color="#555",
)
fig.tight_layout(rect=[0, 0.04, 1, 0.95])
fig.savefig(OUT / "figures" / "e1_architecture.png", dpi=200, bbox_inches="tight")
print(f"wrote {OUT / 'figures' / 'e1_architecture.png'}")

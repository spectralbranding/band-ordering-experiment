# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "matplotlib"]
# ///
"""Figure for the band-ordering study. Reads output/band_ordering_rows.csv."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "output"
df = pd.read_csv(OUT / "band_ordering_rows.csv")
df = df[df.substrate != "nanowire-network (real)"]

STYLE = {
    "esn-fast (leak 1.0)": ("#1b1b1b", "o", "-"),
    "esn-mid (leak 0.3)": ("#6b6b6b", "s", "-"),
    "esn-slow (leak 0.1)": ("#a8a8a8", "^", "-"),
    "nanowire-network (real)": ("#c1462c", "D", "--"),
}

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.4), sharey=True)
T95 = 2.262  # t(.975, df=9)

for ax, (arm, title) in zip(
    axes,
    [
        ("A-readout", "A. Read less often\n(native drive, decimated readout)"),
        ("B-drive", "B. Drive and read slower\n(a genuine band change)"),
    ],
):
    sub = df[df.arm == arm]
    for name, grp in sub.groupby("substrate"):
        c, m, ls = STYLE[name]
        agg = grp.groupby("band_k").ipc.agg(["mean", "std", "count"]).reset_index()
        err = T95 * agg["std"] / agg["count"] ** 0.5
        err = err.fillna(0)
        ax.errorbar(
            agg.band_k,
            agg["mean"],
            yerr=err,
            color=c,
            marker=m,
            ls=ls,
            lw=1.8,
            ms=6,
            capsize=3,
            elinewidth=1.1,
            label=name,
        )
    ax.set_xscale("log", base=2)
    ax.set_xticks([1, 2, 4, 8])
    ax.set_xticklabels(["1x", "2x", "4x", "8x"])
    ax.set_xlabel("observation band (sampling interval)")
    ax.set_title(title, fontsize=10, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(alpha=0.25, lw=0.6)

axes[0].set_ylabel("total information processing capacity")
axes[0].legend(frameon=False, fontsize=8.5, loc="upper right")
fig.suptitle(
    "Substrate ordering is conditional on the band \u2013 but only when the DRIVE slows",
    fontsize=11.5,
    x=0.02,
    ha="left",
    weight="bold",
)
fig.text(
    0.02,
    -0.04,
    "Three simulated reservoirs differing only in time constant. Mean of 10 seeds, bars are 95% CI. "
    "n held fixed at 350 across all bands. Seed 20260830.\n"
    "Left: the fastest substrate stays first at every band. Right: it goes from first to last, in 10 of 10 seeds. "
    "The real substrate is omitted \u2013 it had not reached estimator saturation and cannot be fairly ranked.",
    fontsize=8.2,
    color="#555",
)
fig.tight_layout(rect=[0, 0.02, 1, 0.94])
fig.savefig(OUT / "figures" / "band_ordering.png", dpi=200, bbox_inches="tight")
print(f"wrote {OUT / 'figures' / 'band_ordering.png'}")

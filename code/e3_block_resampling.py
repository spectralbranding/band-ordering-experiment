# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "scipy", "scikit-learn", "pandas", "matplotlib", "rcbench==1.0.10"]
# ///
"""E3 -- an interval for the one real substrate, by moving-block resampling.

The nanowire recording sits in the repository but is omitted from the figure and
excluded from every ordering claim, because at n=350 it has not reached estimator
saturation while the simulated substrates have. There is ONE recording, so there are
no seeds to average over and no interval to quote.

WHAT THIS DOES AND DOES NOT BUY. Moving-block resampling of a single recording gives
an interval on the ESTIMATE AT THIS n, treating the recording as the population. It
does NOT fix estimator starvation and does not recover the value the estimate would
converge to with more data. Reporting it any other way would launder a known
limitation into a measurement.

OUTCOME WHEN THIS WAS RUN (2026-08-30): the validation below PASSED only weakly --
the bootstrap brackets every known seed mean but is far too wide and is biased upward
at coarse bands (esn-fast at k=8: bootstrap median 2.60 against a true 1.43). So the
answer to this extension's question is NO, and the real substrate STAYS OUT of the
ordering figure. The interval is recorded; it does not license a ranking.

THE METHOD IS VALIDATED RATHER THAN ASSUMED, WHICH IS THE POINT OF THE SECOND HALF.
A block bootstrap on a driven dynamical system has a real defect: resampled blocks are
stitched at boundaries, so the state at the start of a block does not follow from the
input that precedes it there. With a block long relative to the substrate's memory the
contamination is confined to the first few samples of each block, but "confined" is an
assumption until it is checked. So the same bootstrap is run on the three SIMULATED
substrates, whose true 10-seed intervals are already known from the main study. If the
bootstrap intervals bracket the seed-based intervals, the method transfers to the
recording. If they do not, this extension reports that instead and the nanowire stays
out of the figure.

A second, assumption-free check runs alongside at k=1: the recording is cut into
DISJOINT contiguous windows of n=350, each correctly driven with no stitching at all,
and their spread is reported next to the bootstrap interval.

Run:
    uv run --script code/e3_block_resampling.py

Writes output/e3_block_resampling_rows.csv and prints the intervals and the
validation verdict. Deterministic: seed 20260830.
"""

from __future__ import annotations

import csv
import urllib.request
from pathlib import Path

import numpy as np
from rcbench.tasks.ipc import IPCEvaluator

SEED = 20260830
OUT = Path(__file__).resolve().parents[1] / "output"
NWN_URL = (
    "https://raw.githubusercontent.com/nanotechdave/RCbench/main/tests/test_files/"
    "011_INRiMARC_NWN_Pad131M_gridSE_MemoryCapacity_2024_03_29.txt"
)
CACHE = OUT / "nwn_pad131m.txt"

BANDS = (1, 2, 4, 8)
N_FIXED = 350
MAX_DELAY = 8
MAX_DEGREE = 2
N_NODES = 60
SPECTRAL_RADIUS = 0.95

N_BOOT = 200  # bootstrap replicates
BLOCK = 50  # block length, long relative to the substrates' memory (max_delay 8)
T95 = 2.262  # t(.975, df=9), for the seed-based intervals being validated against

# The main study's 10-seed Arm A means and 95% intervals, for validation only.
SEED_INTERVALS = {
    "esn-fast (leak 1.0)": {1: (8.04, 7.79, 8.29), 8: (1.43, 1.34, 1.51)},
    "esn-mid (leak 0.3)": {1: (2.57, 2.16, 2.97), 8: (0.99, 0.85, 1.13)},
    "esn-slow (leak 0.1)": {1: (1.55, 1.29, 1.80), 8: (0.97, 0.76, 1.18)},
}


def ipc(u: np.ndarray, S: np.ndarray) -> float:
    """Total information processing capacity for one (input, state) pair."""
    ev = IPCEvaluator(
        input_signal=u,
        nodes_output=S,
        max_delay=MAX_DELAY,
        max_degree=MAX_DEGREE,
        random_state=SEED,
    )
    return float(ev.calculate_total_capacity()["total_capacity"])


def esn_run(u: np.ndarray, leak: float, seed: int) -> np.ndarray:
    """Leaky echo-state network, identical to the main study's implementation."""
    rng = np.random.default_rng(seed)
    W = rng.normal(size=(N_NODES, N_NODES))
    W *= SPECTRAL_RADIUS / max(abs(np.linalg.eigvals(W)))
    win = rng.uniform(-1, 1, size=N_NODES)
    x = np.zeros(N_NODES)
    out = np.empty((len(u), N_NODES))
    for i, ut in enumerate(u):
        x = (1 - leak) * x + leak * np.tanh(W @ x + win * ut)
        out[i] = x
    return out


def load_nanowire() -> tuple[np.ndarray, np.ndarray, float]:
    """Real physical substrate: INRiM self-organising nanowire network."""
    OUT.mkdir(parents=True, exist_ok=True)
    if not CACHE.exists():
        urllib.request.urlretrieve(NWN_URL, CACHE)  # noqa: S310
    raw = np.genfromtxt(CACHE, names=True, deletechars="", replace_space="_")
    cols = list(raw.dtype.names)
    t = raw[cols[0]]
    X = np.column_stack([raw[c] for c in cols if c.endswith("_V[V]")])
    u, S = X[:, 0], X[:, 1:]
    ok = np.isfinite(u) & np.isfinite(S).all(axis=1)
    return u[ok], S[ok], float(np.median(np.diff(t[ok])))


def block_bootstrap(
    u: np.ndarray, S: np.ndarray, n: int, rng: np.random.Generator
) -> float | None:
    """One moving-block bootstrap replicate: stitch blocks to length n, then measure."""
    if len(u) < BLOCK:
        return None
    n_blocks = int(np.ceil(n / BLOCK))
    starts = rng.integers(0, len(u) - BLOCK + 1, size=n_blocks)
    idx = np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]
    try:
        return ipc(u[idx], S[idx])
    except Exception:
        return None


def percentile_ci(vals: list[float]) -> tuple[float, float, float]:
    """Median and a 95% percentile interval."""
    a = np.asarray(vals, dtype=float)
    return (
        float(np.median(a)),
        float(np.percentile(a, 2.5)),
        float(np.percentile(a, 97.5)),
    )


def main() -> None:
    rows: list[dict] = []
    rng = np.random.default_rng(SEED)

    u_nwn, S_nwn, dt = load_nanowire()
    print(
        f"nanowire network: n={len(u_nwn)}, dt={dt:.4f}s, "
        f"{S_nwn.shape[1]} state variables"
    )
    print(
        f"bootstrap: {N_BOOT} replicates, block length {BLOCK}, n fixed at {N_FIXED}\n"
    )

    # ---- 1. VALIDATION: does the bootstrap recover known seed-based intervals? ----
    print("=== VALIDATION: bootstrap against the main study's 10-seed intervals ===")
    print("  Same bootstrap, run on substrates whose true interval is already known.")
    print(
        f"\n{'substrate':<24}{'band':>6}{'seed-based 95% CI':>26}"
        f"{'bootstrap 95% CI':>26}{'brackets?':>11}"
    )
    n_needed = N_FIXED * max(BANDS) + 200
    u_long = np.random.default_rng(SEED).uniform(-1, 1, size=n_needed)
    validation_ok = True
    for name, leak in (
        ("esn-fast (leak 1.0)", 1.0),
        ("esn-mid (leak 0.3)", 0.3),
        ("esn-slow (leak 0.1)", 0.1),
    ):
        S_full = esn_run(u_long, leak, SEED)
        for k in (1, 8):
            u_k, S_k = u_long[::k], S_full[::k]
            boot = [
                v
                for v in (
                    block_bootstrap(u_k, S_k, N_FIXED, rng) for _ in range(N_BOOT)
                )
                if v is not None
            ]
            med, lo, hi = percentile_ci(boot)
            s_mean, s_lo, s_hi = SEED_INTERVALS[name][k]
            brackets = lo <= s_mean <= hi
            validation_ok &= brackets
            rows.append(
                {
                    "substrate": name,
                    "role": "validation",
                    "band_k": k,
                    "n": N_FIXED,
                    "boot_median": round(med, 3),
                    "boot_lo": round(lo, 3),
                    "boot_hi": round(hi, 3),
                    "seed_mean": s_mean,
                    "seed_lo": s_lo,
                    "seed_hi": s_hi,
                    "brackets_seed_mean": int(brackets),
                }
            )
            print(
                f"{name:<24}{k:>6}{f'{s_mean:.2f} [{s_lo:.2f}, {s_hi:.2f}]':>26}"
                f"{f'{med:.2f} [{lo:.2f}, {hi:.2f}]':>26}"
                f"{('yes' if brackets else 'NO'):>11}"
            )
    print(
        f"\n  VALIDATION VERDICT: {'PASS' if validation_ok else 'FAIL'} -- the bootstrap "
        f"{'brackets' if validation_ok else 'does NOT bracket'} every known seed mean."
    )
    if not validation_ok:
        print(
            "  The method does not transfer. The nanowire interval below is reported\n"
            "  for the record but MUST NOT be used to return it to the figure."
        )

    # ---- 2. the real substrate ----------------------------------------------
    print("\n=== THE REAL SUBSTRATE, block-resampled ===")
    print(f"{'band':>6}{'bootstrap median [95% CI]':>32}{'width':>9}")
    for k in BANDS:
        u_k, S_k = u_nwn[::k], S_nwn[::k]
        boot = [
            v
            for v in (block_bootstrap(u_k, S_k, N_FIXED, rng) for _ in range(N_BOOT))
            if v is not None
        ]
        med, lo, hi = percentile_ci(boot)
        rows.append(
            {
                "substrate": "nanowire-network (real)",
                "role": "estimate",
                "band_k": k,
                "n": N_FIXED,
                "boot_median": round(med, 3),
                "boot_lo": round(lo, 3),
                "boot_hi": round(hi, 3),
                "seed_mean": "",
                "seed_lo": "",
                "seed_hi": "",
                "brackets_seed_mean": "",
            }
        )
        print(f"{k:>6}{f'{med:.3f} [{lo:.3f}, {hi:.3f}]':>32}{hi - lo:>9.3f}")

    # ---- 3. assumption-free cross-check: disjoint contiguous windows ----------
    print("\n=== CROSS-CHECK: disjoint contiguous windows, no stitching at all ===")
    for k in (1, 2):
        u_k, S_k = u_nwn[::k], S_nwn[::k]
        n_win = len(u_k) // N_FIXED
        vals = [
            ipc(
                u_k[i * N_FIXED : (i + 1) * N_FIXED],
                S_k[i * N_FIXED : (i + 1) * N_FIXED],
            )
            for i in range(n_win)
        ]
        if not vals:
            continue
        a = np.asarray(vals)
        rows.append(
            {
                "substrate": "nanowire-network (real)",
                "role": "disjoint_windows",
                "band_k": k,
                "n": N_FIXED,
                "boot_median": round(float(np.median(a)), 3),
                "boot_lo": round(float(a.min()), 3),
                "boot_hi": round(float(a.max()), 3),
                "seed_mean": "",
                "seed_lo": "",
                "seed_hi": "",
                "brackets_seed_mean": "",
            }
        )
        print(
            f"  k={k}: {n_win} disjoint windows, "
            f"median {np.median(a):.3f}, range [{a.min():.3f}, {a.max():.3f}]"
        )
        print(f"         values: {', '.join(f'{v:.3f}' for v in vals)}")

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "e3_block_resampling_rows.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(
        "\nThe nanowire remains ESTIMATOR-STARVED at n=350 (it does not saturate until\n"
        "past n=1400). Any interval above describes sampling variability at this n and\n"
        "is not evidence about where the estimate would converge."
    )


if __name__ == "__main__":
    main()

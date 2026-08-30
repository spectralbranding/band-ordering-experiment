# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "scipy", "scikit-learn", "pandas", "matplotlib", "rcbench==1.0.10"]
# ///
"""E2 -- the arm the study is missing: does the verdict survive re-tuning max_delay?

Extension E2 of the band-ordering study. Arm A varies the readout interval and Arm B
varies the drive, but NEITHER varies `max_delay`, which is itself a band parameter --
the horizon over which the capacity estimator looks for memory. The study held it
fixed at 8 and never examined it, and a reader who notices can ask whether the whole
Arm A / Arm B distinction survives re-tuning the delay horizon per band. This sweeps
it and reports whether the two published verdicts hold at every horizon.

The two verdicts under test, stated as the study states them:
  FINDING 1  Arm B inverts the ordering: fast is first at k=1 and last at k=8.
  FINDING 2  Arm A preserves the top rank at every band.

max_delay IS CONFOUNDED WITH ESTIMATOR BUDGET, AND THAT IS THE WHOLE DIFFICULTY.
The IPC basis at max_degree 2 carries d + d(d+1)/2 terms, so it grows quadratically
in the delay horizon: 5 terms at d=2, 44 at d=8, 560 at d=32. Against a fixed n, a
long horizon starves the estimator exactly as a small n does -- which is the same trap
the main study's n-fixed discipline was built for, arriving through a different door.
Raising d without watching n reports estimator overload as a band interaction.

So the sweep runs at TWO sample counts and the pair is the control:
  n = 350   the main study's own n, so every cell is directly comparable to its tables
  n = 2800  eight times the budget, where a horizon of 32 is comfortably supported
A verdict that changes at n=350 and holds at n=2800 is estimator bias. One that
changes at both is a real interaction with the delay horizon.

Cells whose basis-to-sample ratio falls below 2 are marked infeasible in the CSV and
EXCLUDED FROM EVERY VERDICT, in the same way the main study excluded the estimator-
starved nanowire recording rather than quietly ranking it.

Run:
    uv run --script code/e2_max_delay.py

Writes output/e2_max_delay_rows.csv and prints the tables and verdicts.
Deterministic: seed 20260830, reusing the main study's seeds and input construction.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from rcbench.tasks.ipc import IPCEvaluator

SEED = 20260830
N_SEEDS = 10
OUT = Path(__file__).resolve().parents[1] / "output"

BANDS = (1, 2, 4, 8)
MAX_DELAYS = (2, 4, 8, 16, 32)
N_REGIMES = (350, 2800)
MAX_DEGREE = 2
N_NODES = 60
SPECTRAL_RADIUS = 0.95
T95 = 2.262  # t(.975, df=9)
MIN_RATIO = 2.0  # samples per basis term below which a cell is not ranked

SUBSTRATES = {
    "esn-fast (leak 1.0)": 1.0,
    "esn-mid (leak 0.3)": 0.3,
    "esn-slow (leak 0.1)": 0.1,
}


def basis_size(max_delay: int) -> int:
    """Number of IPC basis terms at max_degree 2 and the given delay horizon."""
    return max_delay + max_delay * (max_delay + 1) // 2


def ipc(u: np.ndarray, S: np.ndarray, max_delay: int) -> float:
    """Total information processing capacity at one delay horizon."""
    ev = IPCEvaluator(
        input_signal=u,
        nodes_output=S,
        max_delay=max_delay,
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


def summarise(vals: list[float]) -> tuple[float, float, float, float]:
    """Mean, SD, and a t-based 95% CI; returns (mean, sd, lo, hi)."""
    a = np.asarray(vals, dtype=float)
    m, sd = float(a.mean()), float(a.std(ddof=1))
    half = T95 * sd / np.sqrt(len(a))
    return m, sd, m - half, m + half


def main() -> None:
    rows: list[dict] = []

    print("basis terms at max_degree 2, and samples per term:")
    for d in MAX_DELAYS:
        b = basis_size(d)
        cells = "  ".join(f"n={n}: {n / b:5.2f}" for n in N_REGIMES)
        print(f"  max_delay {d:>3}  basis {b:>4}   {cells}")
    print(f"  cells below {MIN_RATIO:.1f} samples per term are not ranked\n")

    for n_fixed in N_REGIMES:
        n_needed = n_fixed * max(BANDS) + 200
        for s_i in range(N_SEEDS):
            seed = SEED + s_i
            rng = np.random.default_rng(seed)
            u_long = rng.uniform(-1, 1, size=n_needed)
            for name, leak in SUBSTRATES.items():
                S_full = esn_run(u_long, leak, seed)
                for k in BANDS:
                    # Arm A: native drive, decimated readout.
                    u_a, S_a = u_long[::k][:n_fixed], S_full[::k][:n_fixed]
                    # Arm B: input held for k steps, then read.
                    u_slow = u_long[: n_fixed + 200]
                    S_b = esn_run(np.repeat(u_slow, k), leak, seed)[k - 1 :: k][
                        :n_fixed
                    ]
                    u_b = u_slow[:n_fixed]
                    for arm, (u_x, S_x) in (
                        ("A-readout", (u_a, S_a)),
                        ("B-drive", (u_b, S_b)),
                    ):
                        for d in MAX_DELAYS:
                            rows.append(
                                {
                                    "substrate": name,
                                    "arm": arm,
                                    "band_k": k,
                                    "max_delay": d,
                                    "basis_terms": basis_size(d),
                                    "samples_per_term": round(
                                        n_fixed / basis_size(d), 3
                                    ),
                                    "feasible": int(
                                        n_fixed / basis_size(d) >= MIN_RATIO
                                    ),
                                    "seed": seed,
                                    "n": n_fixed,
                                    "ipc": round(ipc(u_x, S_x, d), 3),
                                }
                            )
            print(f"  n={n_fixed} seed {seed} done ({s_i + 1}/{N_SEEDS})", flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "e2_max_delay_rows.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    subs = list(SUBSTRATES)
    fast, mid = subs[0], subs[1]

    def cell(n_fixed, arm, k, d, sub):
        return [
            r["ipc"]
            for r in rows
            if r["n"] == n_fixed
            and r["arm"] == arm
            and r["band_k"] == k
            and r["max_delay"] == d
            and r["substrate"] == sub
        ]

    for n_fixed in N_REGIMES:
        print(f"\n\n########## n = {n_fixed} ##########")
        for d in MAX_DELAYS:
            feasible = n_fixed / basis_size(d) >= MIN_RATIO
            flag = "" if feasible else "   [INFEASIBLE -- not ranked]"
            print(
                f"\n=== max_delay {d}  ({basis_size(d)} basis terms, "
                f"{n_fixed / basis_size(d):.2f} samples/term){flag} ==="
            )
            for arm in ("A-readout", "B-drive"):
                print(f"  {arm}   mean [95% CI] over {N_SEEDS} seeds")
                print(
                    f"    {'substrate':<24}"
                    + "".join(f"{'k=' + str(k):>22}" for k in BANDS)
                )
                for s_name in subs:
                    cells = []
                    for k in BANDS:
                        m, _, lo, hi = summarise(cell(n_fixed, arm, k, d, s_name))
                        cells.append(f"{m:>8.2f} [{lo:5.2f},{hi:5.2f}]")
                    print(f"    {s_name:<24}" + "".join(f"{c:>22}" for c in cells))
                for k in BANDS:
                    means = {s: summarise(cell(n_fixed, arm, k, d, s))[0] for s in subs}
                    order = sorted(means, key=lambda s: -means[s])
                    print(
                        f"      k={k}: " + "  >  ".join(o.split(" ")[0] for o in order)
                    )

        # ---- the two verdicts, per delay horizon ----
        print(f"\n=== VERDICTS at n = {n_fixed} ===")
        print(
            f"{'max_delay':>10}{'feasible':>10}{'F1 inversion':>16}"
            f"{'fast-mid k=1':>22}{'fast-mid k=8':>22}{'F2 ArmA top rank':>20}"
        )
        for d in MAX_DELAYS:
            feasible = n_fixed / basis_size(d) >= MIN_RATIO
            hits = 0
            for s_i in range(N_SEEDS):
                sd = SEED + s_i

                def v(sub, k, dd=d, ss=sd, nf=n_fixed):
                    return next(
                        r["ipc"]
                        for r in rows
                        if r["n"] == nf
                        and r["arm"] == "B-drive"
                        and r["band_k"] == k
                        and r["max_delay"] == dd
                        and r["substrate"] == sub
                        and r["seed"] == ss
                    )

                hits += (v(fast, 1) > v(mid, 1)) and (v(mid, 8) > v(fast, 8))
            d1 = [
                cell(n_fixed, "B-drive", 1, d, fast)[i]
                - cell(n_fixed, "B-drive", 1, d, mid)[i]
                for i in range(N_SEEDS)
            ]
            d8 = [
                cell(n_fixed, "B-drive", 8, d, fast)[i]
                - cell(n_fixed, "B-drive", 8, d, mid)[i]
                for i in range(N_SEEDS)
            ]
            m1, _, lo1, hi1 = summarise(d1)
            m8, _, lo8, hi8 = summarise(d8)
            top_a = {
                k: max(
                    subs,
                    key=lambda s: summarise(cell(n_fixed, "A-readout", k, d, s))[0],
                )
                for k in BANDS
            }
            f2 = "PRESERVED" if len(set(top_a.values())) == 1 else "REORDERED"
            print(
                f"{d:>10}{('yes' if feasible else 'NO'):>10}{f'{hits}/{N_SEEDS}':>16}"
                f"{f'{m1:+.2f} [{lo1:+.2f},{hi1:+.2f}]':>22}"
                f"{f'{m8:+.2f} [{lo8:+.2f},{hi8:+.2f}]':>22}{f2:>20}"
            )


if __name__ == "__main__":
    main()

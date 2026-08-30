# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "scipy", "scikit-learn", "pandas", "matplotlib", "rcbench==1.0.10"]
# ///
"""Is substrate ordering under a capacity benchmark conditional on the observation band?

This is a METHODOLOGICAL measurement about reservoir-computing benchmarking
practice. It is NOT evidence about cognition, intelligence or minds, and must
never be reported as such.

Two arms, because they are not the same experiment and the difference is the point:

  ARM A (READOUT band). Drive the substrate at its native rate; read the state every
    k-th step. This is what anyone re-analysing an archived recording can do, and it
    is the only arm available for real recorded data -- you cannot re-drive a
    recording. The unread drive samples remain, acting as unobserved input.

  ARM B (DRIVE band). Drive AND read at the coarser rate. This is a genuine change of
    band in Ishida et al.'s sense (they varied the stimulus inter-step interval).
    Available for simulated substrates only.

Comparing A against B on the simulated substrates answers a question the field needs
and nobody has asked: is decimating an archived recording a valid proxy for a real
band change?

Design constraints, both established by a feasibility spike run before any of this
was written:
  * n is HELD FIXED across bands. IPC is strongly biased by sample count, and a naive
    decimation sweep confounds band with estimator bias. The saturation curve is
    reported alongside so the reader can see the bias being controlled for.
  * The input must be i.i.d. for the IPC basis to be well posed. Verified for the real
    substrate (lag-1 autocorrelation .015 at native rate, and decimating an i.i.d.
    series leaves it i.i.d.).

Run:
    uv run --script code/band_ordering_study.py

Writes output/band_ordering_rows.csv, output/saturation_rows.csv and prints the tables.
Deterministic: every random draw is seeded.
"""

from __future__ import annotations

import csv
import urllib.request
from pathlib import Path

import numpy as np
from rcbench.tasks.ipc import IPCEvaluator

SEED = 20260830
N_SEEDS = 10  # independent (reservoir, input) draws per simulated substrate
OUT = Path(__file__).resolve().parents[1] / "output"
NWN_URL = (
    "https://raw.githubusercontent.com/nanotechdave/RCbench/main/tests/test_files/"
    "011_INRiMARC_NWN_Pad131M_gridSE_MemoryCapacity_2024_03_29.txt"
)
CACHE = OUT / "nwn_pad131m.txt"

BANDS = (1, 2, 4, 8)
N_FIXED = 350  # capped by (shortest recording / largest decimation)
MAX_DELAY = 8
MAX_DEGREE = 2
N_NODES = 60
SPECTRAL_RADIUS = 0.95


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
    """Leaky echo-state network. `leak` IS the substrate's time constant.

    Two substrates identical but for `leak` have identical normalised dynamics and
    different physical time constants -- the case a single fixed sampling interval
    cannot tell apart.
    """
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


def summarise(vals: list[float]) -> tuple[float, float, float, float]:
    """Mean, SD, and a t-based 95% CI half-width; returns (mean, sd, lo, hi)."""
    a = np.asarray(vals, dtype=float)
    m, sd = float(a.mean()), float(a.std(ddof=1))
    # t(.975, df=9) = 2.262; hard-coded so the script needs no scipy at report time
    half = 2.262 * sd / np.sqrt(len(a))
    return m, sd, m - half, m + half


def main() -> None:
    rows: list[dict] = []
    sat: list[dict] = []

    # ---- real substrate: ONE recording, so no seed replication is possible ----
    u_nwn, S_nwn, dt = load_nanowire()
    lag1 = float(np.corrcoef(u_nwn[:-1], u_nwn[1:])[0, 1])
    print(
        f"nanowire network: n={len(u_nwn)}, dt={dt:.4f}s, "
        f"{S_nwn.shape[1]} state variables, input lag-1 autocorr {lag1:+.3f}"
    )
    print(f"n held fixed at {N_FIXED}; {N_SEEDS} seeds per simulated substrate\n")

    for k in BANDS:
        rows.append(
            {
                "substrate": "nanowire-network (real)",
                "arm": "A-readout",
                "band_k": k,
                "seed": SEED,
                "n": N_FIXED,
                "ipc": round(ipc(u_nwn[::k][:N_FIXED], S_nwn[::k][:N_FIXED]), 3),
            }
        )
    for n in (350, 700, 1400, 2800):
        sat.append(
            {
                "substrate": "nanowire-network (real)",
                "n": n,
                "ipc": round(ipc(u_nwn[:n], S_nwn[:n]), 3),
            }
        )

    # ---- simulated substrates, differing ONLY in time constant ----------------
    leaks = {
        "esn-fast (leak 1.0)": 1.0,
        "esn-mid (leak 0.3)": 0.3,
        "esn-slow (leak 0.1)": 0.1,
    }
    n_needed = N_FIXED * max(BANDS) + 200

    for s_i in range(N_SEEDS):
        seed = SEED + s_i
        rng = np.random.default_rng(seed)
        u_long = rng.uniform(-1, 1, size=n_needed)  # fresh input per seed
        for name, leak in leaks.items():
            S_full = esn_run(u_long, leak, seed)  # fresh reservoir per seed
            for k in BANDS:
                rows.append(
                    {
                        "substrate": name,
                        "arm": "A-readout",
                        "band_k": k,
                        "seed": seed,
                        "n": N_FIXED,
                        "ipc": round(
                            ipc(u_long[::k][:N_FIXED], S_full[::k][:N_FIXED]), 3
                        ),
                    }
                )
                u_slow = u_long[: N_FIXED + 200]
                S_slow = esn_run(np.repeat(u_slow, k), leak, seed)[k - 1 :: k][:N_FIXED]
                rows.append(
                    {
                        "substrate": name,
                        "arm": "B-drive",
                        "band_k": k,
                        "seed": seed,
                        "n": N_FIXED,
                        "ipc": round(ipc(u_slow[:N_FIXED], S_slow), 3),
                    }
                )
            if s_i == 0:  # saturation is an estimator control, not a claim
                for n in (350, 700, 1400, 2800):
                    sat.append(
                        {
                            "substrate": name,
                            "n": n,
                            "ipc": round(ipc(u_long[:n], S_full[:n]), 3),
                        }
                    )
        print(f"  seed {seed} done ({s_i + 1}/{N_SEEDS})")

    OUT.mkdir(parents=True, exist_ok=True)
    for fname, data in (("band_ordering_rows.csv", rows), ("saturation_rows.csv", sat)):
        with (OUT / fname).open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0].keys()))
            w.writeheader()
            w.writerows(data)

    # ---- report ---------------------------------------------------------------
    sims = list(leaks)
    for arm, title in (
        ("A-readout", "ARM A -- native drive, decimated READOUT"),
        ("B-drive", "ARM B -- driven AND read at the coarse rate"),
    ):
        print(f"\n=== {title} ===  mean [95% CI] over {N_SEEDS} seeds")
        print(f"{'substrate':<24}" + "".join(f"{'k=' + str(k):>22}" for k in BANDS))
        for s_name in sims:
            cells = []
            for k in BANDS:
                v = [
                    r["ipc"]
                    for r in rows
                    if r["substrate"] == s_name and r["arm"] == arm and r["band_k"] == k
                ]
                m, _, lo, hi = summarise(v)
                cells.append(f"{m:>8.2f} [{lo:5.2f},{hi:5.2f}]")
            print(f"{s_name:<24}" + "".join(f"{c:>22}" for c in cells))
        print("  ORDERING by mean (best first):")
        for k in BANDS:
            means = {
                s_name: summarise(
                    [
                        r["ipc"]
                        for r in rows
                        if r["substrate"] == s_name
                        and r["arm"] == arm
                        and r["band_k"] == k
                    ]
                )[0]
                for s_name in sims
            }
            order = sorted(means, key=lambda s_name: -means[s_name])
            print(f"    k={k}: " + "  >  ".join(o.split(" ")[0] for o in order))

    # ---- does the inversion survive per seed? --------------------------------
    print(f"\n=== INVERSION TEST (Arm B), per seed, {N_SEEDS} seeds ===")
    fast, mid = sims[0], sims[1]

    def val(sub, k, seed, arm="B-drive"):
        return next(
            r["ipc"]
            for r in rows
            if r["substrate"] == sub
            and r["arm"] == arm
            and r["band_k"] == k
            and r["seed"] == seed
        )

    hits = 0
    for s_i in range(N_SEEDS):
        seed = SEED + s_i
        a = val(fast, 1, seed) > val(mid, 1, seed)
        b = val(mid, 8, seed) > val(fast, 8, seed)
        hits += a and b
    print(
        f"  fast beats mid at k=1 AND mid beats fast at k=8: " f"{hits}/{N_SEEDS} seeds"
    )
    diffs = [val(fast, 1, SEED + i) - val(mid, 1, SEED + i) for i in range(N_SEEDS)]
    m, sd, lo, hi = summarise(diffs)
    print(f"  fast - mid at k=1: {m:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    diffs = [val(fast, 8, SEED + i) - val(mid, 8, SEED + i) for i in range(N_SEEDS)]
    m, sd, lo, hi = summarise(diffs)
    print(f"  fast - mid at k=8: {m:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    print("  (CIs excluding zero with opposite signs = the inversion is not noise)")

    print("\n=== SATURATION CONTROL: IPC vs n at fixed native band (seed 1) ===")
    ns = (350, 700, 1400, 2800)
    print(f"{'substrate':<26}" + "".join(f"{'n=' + str(n):>10}" for n in ns))
    for s_name in dict.fromkeys(r["substrate"] for r in sat):
        cells = {r["n"]: r["ipc"] for r in sat if r["substrate"] == s_name}
        print(f"{s_name:<26}" + "".join(f"{cells[n]:>10.3f}" for n in ns))


if __name__ == "__main__":
    main()

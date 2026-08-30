# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "scipy", "scikit-learn", "pandas", "matplotlib", "rcbench==1.0.10"]
# ///
"""E4 -- is E1's aliasing account a mechanism or a three-point coincidence?

E1 explained its Arm A reordering by aliasing: a resonant substrate read below twice
its oscillation frequency loses the structure that carried its capacity, and the
order in which the three oscillator substrates crossed Nyquist was the order in which
they lost rank. That is an ORDINAL COINCIDENCE OVER THREE POINTS. It is the one
genuinely new explanatory claim E1 put into a public README, and it deserves a
measurement rather than an assertion.

THE PREDICTION, STATED SO IT CAN FAIL. If the readout loss is governed by aliasing,
it depends on the substrate's oscillation period measured IN READOUT SAMPLES --

    samples_per_period = (2*pi/omega) / k

-- and NOT on omega or k separately. So points sharing a value of that ratio should
coincide even when they come from very different (omega, k) pairs: the capacity curve
should COLLAPSE onto one function of the ratio. If instead capacity is explained just
as well by k alone ("reading less often always costs the same") or by omega alone
("faster substrates are simply better"), the aliasing account adds nothing.

Two things are therefore measured, and the second is the one that can embarrass us:
  1. WHERE the knee falls -- aliasing predicts it near a ratio of 2, which is Nyquist.
  2. HOW MUCH BETTER the joint ratio explains capacity than k alone or omega alone.
     Reported as variance explained by a cubic fit in each candidate variable. If the
     ratio does not beat both single variables, the mechanism claim must be withdrawn
     from the README and E1's Arm A result stands as an unexplained observation.

Arm B is swept identically as a CONTRAST, not as a second test of the same thing. In
Arm A the substrate is driven at full rate and only the readout is decimated, so
aliasing is available as a mechanism. In Arm B the drive is slowed too, so the
substrate settles between inputs and the loss is timescale matching rather than
aliasing. The two need not collapse on the same variable, and whether they do is
informative either way.

Only the oscillator family is swept. A leaky echo-state network has no oscillation
and therefore no period, so `samples_per_period` is undefined for it -- which is
precisely why Arm A looked harmless there, and is not a gap in this design.

THE UPPER END OF THE OMEGA RANGE IS SET BY THE INTEGRATOR, NOT BY TASTE. E1's
semi-implicit Euler at 4 substeps per drive step is stable to omega = 2.0 but diverges
by omega = 3.2, because the Duffing cubic raises the effective stiffness above the
linear stability limit once the amplitude grows. Raising the substep count would fix
that and would also change E1's published numbers, so the sweep keeps E1's integrator
exactly and stops at E1's own fastest substrate. Any cell that diverges anyway on some
seed is RECORDED AS DIVERGED and excluded, never silently carried as a NaN.

Run:
    uv run --script code/e4_aliasing_collapse.py

Writes output/e4_aliasing_rows.csv and prints the collapse table.
Deterministic: seed 20260830.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from rcbench.tasks.ipc import IPCEvaluator

SEED = 20260830
N_SEEDS = 5  # fewer than the 10 of E1: this sweeps 12 omegas x 8 bands, not 3 x 4
OUT = Path(__file__).resolve().parents[1] / "output"

# 12 log-spaced natural frequencies filling in between and below E1's three
# (2.0, 0.6, 0.2). The top is E1's own fastest substrate; see the integrator note above.
OMEGAS = tuple(round(float(w), 4) for w in np.geomspace(0.12, 2.0, 12))
# 8 bands rather than 4, to fill in the ratio axis between the E1 grid points.
BANDS = (1, 2, 3, 4, 6, 8, 12, 16)
N_FIXED = 350
MAX_DELAY = 8
MAX_DEGREE = 2
N_NODES = 60

# Oscillator family constants, identical to E1.
ZETA = 0.3
BETA = 0.5
K_RADIUS = 0.4
SUBSTEPS = 4

NYQUIST = 2.0  # samples per period below which the substrate is aliased


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


def spring_run(u: np.ndarray, omega: float, seed: int) -> np.ndarray:
    """Bank of coupled damped Duffing oscillators. Identical to E1's implementation."""
    dt = 1.0 / SUBSTEPS
    rng = np.random.default_rng(seed)
    w = omega * np.exp(rng.normal(0, 0.25, size=N_NODES))
    K = rng.normal(size=(N_NODES, N_NODES)) * (rng.random((N_NODES, N_NODES)) < 0.1)
    ev = max(abs(np.linalg.eigvals(K)))
    K *= K_RADIUS / ev if ev > 0 else 1.0
    win = rng.uniform(-1, 1, size=N_NODES)
    x = np.zeros(N_NODES)
    v = np.zeros(N_NODES)
    out = np.empty((len(u), N_NODES))
    w2 = w**2
    for i, ut in enumerate(u):
        for _ in range(SUBSTEPS):
            v = v + dt * (-2 * ZETA * w * v - w2 * (x + BETA * x**3 - K @ x - win * ut))
            x = x + dt * v
        out[i] = x
    return out


def variance_explained(x: np.ndarray, y: np.ndarray, degree: int = 3) -> float:
    """R^2 of a polynomial fit of y on x. The collapse statistic.

    A high value means the single variable `x` accounts for the spread in capacity,
    i.e. the points lie on one curve when plotted against it.
    """
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if len(x) < degree + 2 or np.ptp(x) == 0:
        return float("nan")
    coef = np.polyfit(x, y, degree)
    resid = y - np.polyval(coef, x)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return float(1.0 - (resid**2).sum() / ss_tot) if ss_tot > 0 else float("nan")


def main() -> None:
    rows: list[dict] = []
    n_diverged = 0
    n_needed = N_FIXED * max(BANDS) + 200

    print(f"omegas: {OMEGAS}")
    print(f"bands:  {BANDS}")
    print(
        f"{len(OMEGAS)} x {len(BANDS)} x 2 arms x {N_SEEDS} seeds, n fixed at {N_FIXED}\n"
    )

    for s_i in range(N_SEEDS):
        seed = SEED + s_i
        rng = np.random.default_rng(seed)
        u_long = rng.uniform(-1, 1, size=n_needed)
        for omega in OMEGAS:
            period = 2 * np.pi / omega  # in drive steps
            tau = 1.0 / (ZETA * omega)  # envelope decay, in drive steps
            S_full = spring_run(u_long, omega, seed)
            if not np.isfinite(S_full).all():
                n_diverged += 1
                print(
                    f"    DIVERGED and excluded: omega={omega}, seed={seed}, Arm A",
                    flush=True,
                )
                continue
            for k in BANDS:
                # Arm A: native drive, decimated readout -- aliasing is available.
                a = ipc(u_long[::k][:N_FIXED], S_full[::k][:N_FIXED])
                # Arm B: drive held for k steps, then read -- timescale matching.
                u_slow = u_long[: N_FIXED + 200]
                S_slow_full = spring_run(np.repeat(u_slow, k), omega, seed)
                if not np.isfinite(S_slow_full).all():
                    n_diverged += 1
                    print(
                        f"    DIVERGED and excluded: omega={omega}, seed={seed}, "
                        f"Arm B, k={k}",
                        flush=True,
                    )
                    continue
                S_slow = S_slow_full[k - 1 :: k][:N_FIXED]
                b = ipc(u_slow[:N_FIXED], S_slow)
                for arm, val in (("A-readout", a), ("B-drive", b)):
                    rows.append(
                        {
                            "arm": arm,
                            "omega": omega,
                            "band_k": k,
                            "period_drive_steps": round(period, 4),
                            "tau_drive_steps": round(tau, 4),
                            "samples_per_period": round(period / k, 4),
                            "aliased": int(period / k < NYQUIST),
                            "seed": seed,
                            "n": N_FIXED,
                            "ipc": round(val, 3),
                        }
                    )
        print(f"  seed {seed} done ({s_i + 1}/{N_SEEDS})", flush=True)

    if n_diverged:
        print(f"\n  {n_diverged} cell(s) diverged and were excluded.")

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "e4_aliasing_rows.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # ---- the collapse test ---------------------------------------------------
    print("\n=== COLLAPSE TEST ===")
    print("Variance in log(capacity) explained by a cubic fit in each candidate")
    print("variable. The aliasing account predicts samples_per_period wins in Arm A.\n")
    print(
        f"{'arm':<12}{'samples_per_period':>21}{'band k alone':>16}"
        f"{'omega alone':>15}{'n points':>10}"
    )
    verdicts = {}
    for arm in ("A-readout", "B-drive"):
        sel = [r for r in rows if r["arm"] == arm and r["ipc"] > 0]
        y = np.log(np.array([r["ipc"] for r in sel]))
        cands = {
            "samples_per_period": np.log(
                np.array([r["samples_per_period"] for r in sel])
            ),
            "band_k": np.log(np.array([float(r["band_k"]) for r in sel])),
            "omega": np.log(np.array([r["omega"] for r in sel])),
        }
        r2 = {name: variance_explained(x, y) for name, x in cands.items()}
        verdicts[arm] = r2
        print(
            f"{arm:<12}{r2['samples_per_period']:>21.3f}{r2['band_k']:>16.3f}"
            f"{r2['omega']:>15.3f}{len(sel):>10}"
        )

    a = verdicts["A-readout"]
    wins = (
        a["samples_per_period"] > a["band_k"] and a["samples_per_period"] > a["omega"]
    )
    print(
        f"\n  ARM A VERDICT: samples_per_period "
        f"{'BEATS' if wins else 'DOES NOT BEAT'} both single variables."
    )
    print(
        "  If it does not beat both, the aliasing mechanism claim must be withdrawn\n"
        "  from the public README and E1's Arm A result stands unexplained."
    )

    # ---- where the knee falls ------------------------------------------------
    print("\n=== CAPACITY AGAINST SAMPLES PER PERIOD (Arm A), binned ===")
    print("  Nyquist is 2.0. Aliasing predicts the collapse begins around there.")
    sel = [r for r in rows if r["arm"] == "A-readout"]
    spp = np.array([r["samples_per_period"] for r in sel])
    val = np.array([r["ipc"] for r in sel])
    edges = np.geomspace(max(spp.min(), 1e-3), spp.max(), 13)
    print(f"{'samples/period':>26}{'mean IPC':>12}{'n':>7}   {'aliased?':<10}")
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (spp >= lo) & (spp < hi)
        if m.sum() == 0:
            continue
        mid = float(np.sqrt(lo * hi))
        print(
            f"{f'{lo:8.3f} - {hi:8.3f}':>26}{val[m].mean():>12.3f}{int(m.sum()):>7}"
            f"   {'ALIASED' if mid < NYQUIST else 'resolved':<10}"
        )

    above = val[spp >= NYQUIST]
    below = val[spp < NYQUIST]
    if len(above) and len(below):
        print(
            f"\n  mean IPC resolved (>= {NYQUIST}): {above.mean():.3f}  (n={len(above)})"
            f"\n  mean IPC aliased  (<  {NYQUIST}): {below.mean():.3f}  (n={len(below)})"
            f"\n  ratio: {below.mean() / above.mean():.3f}"
        )


if __name__ == "__main__":
    main()

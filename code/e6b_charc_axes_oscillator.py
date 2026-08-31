# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "scipy", "scikit-learn", "pandas", "matplotlib", "rcbench==1.0.10"]
# ///
"""E6b -- CHARC's three axes on the SECOND architecture family.

E6 ran the band grid on kernel rank, generalization rank and memory capacity for the
ESN family and found that the two arms come apart: Arm B moves every axis, Arm A moves
only the axes computed from the time series. E6 declared its scope as the ESN family
only, because E1 had already shown the oscillator family behaves differently under
Arm A -- it DEMOTES the fastest substrate rather than preserving its top rank -- and
sweeping a second family and a third axis at once would have confounded them.

This runs the same three axes on the oscillator family, with E6's settings held
identical, so the two are directly comparable. The question it answers:

    Is E6's Arm A / Arm B dissociation a property of leaky integrators, or does it
    hold for a second-order resonant substrate too?

E6's account predicts it should HOLD, and for a reason that has nothing to do with the
architecture: KR and GR take one state per input stream, so a manipulation that
changes only which samples are kept cannot move them, whatever the substrate is. If
the dissociation fails here, that account is wrong.

THE PREDICTION IS FIXED BEFORE THE RUN, which matters because E1's Arm A result did
NOT replicate across families and this is the same arm:
  P1  Arm B moves all four axes on the oscillator family too.
  P2  Arm A leaves KR and GR without a detectable change, EVEN THOUGH it is known to
      cost this family its top rank on capacity. That combination -- a demotion on the
      time-series axes and no movement on the single-time-point axes -- is the sharp
      form of the claim.

The oscillator is the same bank of coupled damped Duffing oscillators E1 used, with
E1's constants, so cells are comparable to E1 as well as to E6.

Run:
    uv run --script code/e6b_charc_axes_oscillator.py

Writes output/e6b_charc_axes_oscillator_rows.csv and prints the per-axis tables and
verdicts in E6's format. Deterministic: seed 20260830, reusing E1's seeds and
substrate construction.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from rcbench.tasks.generalizationrank import GeneralizationRankEvaluator
from rcbench.tasks.ipc import IPCEvaluator
from rcbench.tasks.kernelrank import KernelRankEvaluator
from rcbench.tasks.memorycapacity import MemoryCapacityEvaluator

SEED = 20260830
N_SEEDS = 10
OUT = Path(__file__).resolve().parents[1] / "output"

BANDS = (1, 2, 4, 8)
N_FIXED = 350
MAX_DELAY = 8
MAX_DEGREE = 2
N_NODES = 60
SPECTRAL_RADIUS = 0.95

# ---- oscillator-family constants, identical to E1 -------------------------------
ZETA = 0.3  # damping ratio
BETA = 0.5  # cubic stiffening
K_RADIUS = 0.4  # spectral radius of the coupling matrix
SUBSTEPS = 4  # integration substeps per drive step

M_STREAMS = N_NODES  # ensemble size for KR/GR; standard choice is m >= node count
ENS_SYMBOLS = 400  # input symbols per ensemble stream (well past every washout)
GR_NOISE = 0.05  # amplitude of the perturbation making the GR streams "noisy variants"

LEAKS = {
    "spring-fast (omega 2.0)": 2.0,
    "spring-mid (omega 0.6)": 0.6,
    "spring-slow (omega 0.2)": 0.2,
}


def esn_run(u: np.ndarray, omega: float, seed: int) -> np.ndarray:
    """Bank of coupled damped Duffing oscillators. `omega` IS the time constant.

    Byte-identical construction to E1's `spring_run`, so cells are comparable to E1
    as well as to E6. The name is kept so the rest of this script is E6's code
    unchanged -- only the substrate behind it differs.
    """
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


def observed(u_sym: np.ndarray, leak: float, seed: int, k: int, arm: str) -> np.ndarray:
    """Run one input stream under an arm's band condition; return the OBSERVED states.

    Arm A: drive at full rate, keep every k-th sample.
    Arm B: repeat each input symbol k times (a slower drive), keep every k-th sample.
    """
    if arm == "A-readout":
        return esn_run(u_sym, leak, seed)[::k]
    return esn_run(np.repeat(u_sym, k), leak, seed)[k - 1 :: k]


def ipc(u: np.ndarray, S: np.ndarray) -> float:
    ev = IPCEvaluator(
        input_signal=u,
        nodes_output=S,
        max_delay=MAX_DELAY,
        max_degree=MAX_DEGREE,
        random_state=SEED,
    )
    return float(ev.calculate_total_capacity()["total_capacity"])


def memory_capacity(u: np.ndarray, S: np.ndarray) -> float:
    ev = MemoryCapacityEvaluator(
        input_signal=u,
        nodes_output=S,
        max_delay=MAX_DELAY,
        random_state=SEED,
    )
    return float(ev.calculate_total_memory_capacity()["total_memory_capacity"])


def _rank_of(result: dict) -> float:
    """rcbench returns its rank under a key that differs per evaluator; take the number."""
    for key in ("kernel_rank", "generalization_rank", "rank", "effective_rank"):
        if key in result:
            return float(result[key])
    numeric = [v for v in result.values() if isinstance(v, (int, float))]
    if not numeric:
        raise KeyError(f"no numeric rank in {list(result)}")
    return float(numeric[0])


def ensemble_states(leak: float, seed: int, k: int, arm: str, mode: str) -> np.ndarray:
    """Build the (m, n) matrix of one final observed state per input stream.

    mode 'kr': m independent streams -- measures separation of DIFFERENT histories.
    mode 'gr': m noisy variants of one stream -- measures separation of NEAR-IDENTICAL
               histories, so a LOW rank is the good outcome.
    """
    rng = np.random.default_rng(seed + (0 if mode == "kr" else 10_000))
    base = rng.uniform(-1, 1, size=ENS_SYMBOLS)
    states = np.empty((M_STREAMS, N_NODES))
    for j in range(M_STREAMS):
        if mode == "kr":
            u_sym = rng.uniform(-1, 1, size=ENS_SYMBOLS)
        else:
            u_sym = np.clip(base + rng.normal(0, GR_NOISE, size=ENS_SYMBOLS), -1, 1)
        states[j] = observed(u_sym, leak, seed, k, arm)[-1]
    return states


def summarise(vals: list[float]) -> tuple[float, float, float, float]:
    """Mean, SD, and a t-based 95% CI half-width; returns (mean, sd, lo, hi)."""
    a = np.asarray(vals, dtype=float)
    m, sd = float(a.mean()), float(a.std(ddof=1))
    half = 2.262 * sd / np.sqrt(len(a))  # t(.975, df=9)
    return m, sd, m - half, m + half


AXES = ("ipc", "mc", "kr", "gr")
HIGHER_IS_BETTER = {"ipc": True, "mc": True, "kr": True, "gr": False}


def main() -> None:
    rows: list[dict] = []
    n_needed = N_FIXED * max(BANDS) + 200

    for s_i in range(N_SEEDS):
        seed = SEED + s_i
        rng = np.random.default_rng(seed)
        u_long = rng.uniform(-1, 1, size=n_needed)
        for name, leak in LEAKS.items():
            S_full = esn_run(u_long, leak, seed)
            for k in BANDS:
                # ---- Arm A: decimate the readout -----------------------------
                uA, SA = u_long[::k][:N_FIXED], S_full[::k][:N_FIXED]
                # ---- Arm B: slow the drive -----------------------------------
                u_slow = u_long[: N_FIXED + 200]
                SB = esn_run(np.repeat(u_slow, k), leak, seed)[k - 1 :: k][:N_FIXED]
                uB = u_slow[:N_FIXED]

                for arm, u_obs, S_obs in (
                    ("A-readout", uA, SA),
                    ("B-drive", uB, SB),
                ):
                    kr = _rank_of(
                        KernelRankEvaluator(
                            nodes_output=ensemble_states(leak, seed, k, arm, "kr")
                        ).run_evaluation()
                    )
                    gr = _rank_of(
                        GeneralizationRankEvaluator(
                            states=ensemble_states(leak, seed, k, arm, "gr")
                        ).run_evaluation()
                    )
                    rows.append(
                        {
                            "substrate": name,
                            "arm": arm,
                            "band_k": k,
                            "seed": seed,
                            "n": N_FIXED,
                            "m_streams": M_STREAMS,
                            "ipc": round(ipc(u_obs, S_obs), 3),
                            "mc": round(memory_capacity(u_obs, S_obs), 3),
                            "kr": round(kr, 3),
                            "gr": round(gr, 3),
                        }
                    )
        print(f"  seed {s_i + 1}/{N_SEEDS} done")

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "e6b_charc_axes_oscillator_rows.csv"
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {path}")

    subs = list(LEAKS)
    fast, mid, slow = subs

    def cell(sub: str, arm: str, k: int, axis: str) -> list[float]:
        return [
            r[axis]
            for r in rows
            if r["substrate"] == sub and r["arm"] == arm and r["band_k"] == k
        ]

    for axis in AXES:
        better = "higher is better" if HIGHER_IS_BETTER[axis] else "LOWER is better"
        print(f"\n{'=' * 72}\n=== AXIS: {axis.upper()}  ({better}) ===")
        for arm in ("A-readout", "B-drive"):
            print(f"  {arm}:")
            for k in BANDS:
                means = {s: summarise(cell(s, arm, k, axis))[0] for s in subs}
                order = sorted(
                    means,
                    key=lambda s: (-means[s] if HIGHER_IS_BETTER[axis] else means[s]),
                )
                vals = "  ".join(f"{s.split(' ')[0]}={means[s]:.2f}" for s in subs)
                print(
                    f"    k={k}: "
                    + "  >  ".join(o.split(" ")[0] for o in order)
                    + f"    [{vals}]"
                )

        # ---- FINDING 1: does Arm B invert, on this axis? --------------------
        # Stated as a SIGN FLIP in the fast-minus-mid difference between k=1 and k=8,
        # which is the axis-neutral form: on a higher-is-better axis where fast leads
        # at k=1 it reduces exactly to the published test, and it stays meaningful on
        # GR, where LOWER is better and fast does not lead at k=1.
        hits = 0
        for s_i in range(N_SEEDS):
            sd = SEED + s_i

            def v(sub: str, k: int, sd: int = sd) -> float:
                return next(
                    r[axis]
                    for r in rows
                    if r["substrate"] == sub
                    and r["arm"] == "B-drive"
                    and r["band_k"] == k
                    and r["seed"] == sd
                )

            d1, d8 = v(fast, 1) - v(mid, 1), v(fast, 8) - v(mid, 8)
            hits += (d1 > 0) != (d8 > 0)
        print(
            f"  FINDING 1 (Arm B: fast-minus-mid FLIPS SIGN k=1 -> k=8): "
            f"{hits}/{N_SEEDS} seeds"
        )
        for k in (1, 8):
            diffs = [
                cell(fast, "B-drive", k, axis)[i] - cell(mid, "B-drive", k, axis)[i]
                for i in range(N_SEEDS)
            ]
            m, _, lo, hi = summarise(diffs)
            pos = sum(d > 0 for d in diffs)
            print(
                f"    fast - mid at k={k}: {m:+.2f} [{lo:+.2f}, {hi:+.2f}]"
                f"  ({pos}/{N_SEEDS} seeds positive)"
            )

        # ---- FINDING 2: does Arm A preserve the top rank, on this axis? -----
        top = {}
        for k in BANDS:
            means = {s: summarise(cell(s, "A-readout", k, axis))[0] for s in subs}
            top[k] = (
                max(means, key=lambda s: means[s])
                if HIGHER_IS_BETTER[axis]
                else min(means, key=lambda s: means[s])
            )
        preserved = len(set(top.values())) == 1
        print(
            f"  FINDING 2 (Arm A top rank preserved): {preserved}  "
            + "  ".join(f"k={k}:{top[k].split(' ')[0]}" for k in BANDS)
        )
        diffs8 = [
            cell(fast, "A-readout", 8, axis)[i] - cell(slow, "A-readout", 8, axis)[i]
            for i in range(N_SEEDS)
        ]
        m, _, lo, hi = summarise(diffs8)
        print(
            f"    fast - slow at k=8 (Arm A): {m:+.2f} [{lo:+.2f}, {hi:+.2f}]"
            f"  ({sum(d > 0 for d in diffs8)}/{N_SEEDS} seeds positive)"
        )


if __name__ == "__main__":
    main()

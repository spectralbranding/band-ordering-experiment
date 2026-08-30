# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "scipy", "scikit-learn", "pandas", "matplotlib", "rcbench==1.0.10"]
# ///
"""E6 -- one number was never enough: the band sweep on CHARC's three axes.

Extension E6 of the band-ordering study. The study reports ONE scalar per substrate
per band -- total information processing capacity -- and CHARC (Dale et al. 2019,
10.1098/rspa.2018.0723) exists precisely to argue that one number is not enough. Its
behaviour space uses "three common property measures... the kernel rank (KR),
generalization rank and memory capacity". We borrowed the rank rung from that paper
and then did the thing it was written against. This runs the same band grid on all
three axes and asks the question the single-estimator study cannot answer:

    Does the band-conditional reordering appear on EVERY axis, or only on some?

Either answer is a result. On all three, the finding is stronger than a
single-estimator result. On one, it is sharper and says which capacity the band
actually moves.

THE TWO VERDICTS UNDER TEST, stated as the study states them:
  FINDING 1  Arm B inverts the ordering: fast is first at k=1 and last at k=8.
             Tested here as a SIGN FLIP in fast-minus-mid between k=1 and k=8, which
             reduces to the published test on a higher-is-better axis and remains
             meaningful on GR, where lower is better.
  FINDING 2  Arm A preserves the top rank at every band. (ESN family only -- E1
             showed this does NOT replicate on the oscillator family.)

WHAT IS MEASURED, AND HOW IT DIFFERS FROM A SINGLE TRAJECTORY'S RANK. This is the
part most easily got wrong, so it is stated rather than assumed. KR and GR are NOT
the rank of one recorded state trajectory. They follow the ensemble protocol that
rcbench documents from Vidamour et al. 2022 (Nanotechnology 33 485203):

  KR  m distinct input streams are supplied; each produces one reservoir state; the
      m states are stacked and the effective rank of that matrix is taken. It measures
      how well the substrate SEPARATES different input histories. Higher is better.
  GR  the same, except the m streams are noisy variants of ONE common stream. It
      measures how much the substrate separates near-identical histories. LOWER IS
      BETTER -- a high GR means the substrate is amplifying noise, so every ordering
      on this axis is read in the opposite direction to the other two.
  MC  total linear memory capacity over the same trajectories the IPC uses, at the
      study's own max_delay of 8.

IPC is computed alongside so every cell is directly comparable to the published tables.

THE BAND CONDITION IS APPLIED TO THE ENSEMBLE EXACTLY AS THE STUDY APPLIES IT.
Arm A drives at full rate and lets the observer keep every k-th sample, so the final
OBSERVED state is the last retained sample -- up to k-1 steps stale, which is itself
timescale-dependent and is the point. Arm B stretches the input by repeating each
symbol k times and keeps every k-th sample, exactly as the main study builds it. The
number of input SYMBOLS is held fixed across bands in both arms, which is the study's
own n-fixed discipline arriving on a different axis.

CALIBRATION TARGETED NOTHING. m is set to the node count, the standard choice, and
the rank thresholds are rcbench's own defaults for each evaluator (1e-6 for KR, 1e-3
for GR) rather than anything tuned here. No ordering was targeted, inspected or
tuned for, and this is recorded because it is the obvious thing to suspect.

SCOPE LIMIT, DECLARED. The ESN family only -- the family the two published verdicts
rest on. E1 established that the oscillator family behaves differently on Arm A, and
sweeping a second family and a third axis at once would confound them.

Run:
    uv run --script code/e6_charc_axes.py

Writes output/e6_charc_axes_rows.csv and prints the per-axis tables and verdicts.
Deterministic: seed 20260830, reusing the main study's seeds and input construction.
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

M_STREAMS = N_NODES  # ensemble size for KR/GR; standard choice is m >= node count
ENS_SYMBOLS = 400  # input symbols per ensemble stream (well past every washout)
GR_NOISE = 0.05  # amplitude of the perturbation making the GR streams "noisy variants"

LEAKS = {
    "esn-fast (leak 1.0)": 1.0,
    "esn-mid (leak 0.3)": 0.3,
    "esn-slow (leak 0.1)": 0.1,
}


def esn_run(u: np.ndarray, leak: float, seed: int) -> np.ndarray:
    """Leaky echo-state network. `leak` IS the substrate's time constant.

    Byte-identical construction to the main study, so cells are comparable.
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
    path = OUT / "e6_charc_axes_rows.csv"
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

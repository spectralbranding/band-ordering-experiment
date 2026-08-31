# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "scipy", "scikit-learn", "pandas", "rcbench==1.0.10"]
# ///
"""E7 -- the SECOND rank protocol, and whether the axis split survives it.

The study reports that a readout-only band change moves the time-series axes and
leaves the state-rank axes untouched. That result is computed under the ENSEMBLE
protocol: m distinct input streams, one final state each, stacked and ranked. A
decimation changes WHICH state is taken and never HOW MANY, so the matrix keeps m
rows at every band -- which is the whole content of the insulation argument.

The field carries a SECOND protocol: one input stream, state recorded at EVERY
observed timepoint, those states stacked and ranked. There a decimation changes
which COLUMNS exist, and the insulation argument does not apply.

Predictions were fixed before this ran (see the note's E7 prediction record):
  P-E7-1  the single-stream protocol DOES move the rank measures
  P-E7-2  the movement compresses or favours the SLOW variant; it does not demote
          the fastest, because decimation decorrelates retained states and a fast
          variant has little correlation left to lose
  P-E7-3  the drive-length-fixed variant falls with the column count and is a
          confound, not a result

DESIGN. `states_fixed` holds the number of OBSERVED states fixed across bands, by
lengthening the drive until S states have been retained -- the study's own n-fixed
discipline. `drive_fixed` holds the drive length fixed instead, so the observed
count falls as 1/k; it is reported alongside as the declared confound.

Run:
    uv run --script code/e7_single_stream_rank.py

Writes output/e7_single_stream_rank_rows.csv. Deterministic; seed 20260830.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

SEED = 20260830
N_SEEDS = 10
OUT = Path(__file__).resolve().parents[1] / "output"

BANDS = (1, 2, 4, 8)
N_NODES = 60
SPECTRAL_RADIUS = 0.95
S_STATES = 2 * N_NODES  # observed states in the single-stream matrix (>= node count)
GR_NOISE = 0.05
KR_TOL = 1e-6  # rcbench's own default thresholds, not tuned here
GR_TOL = 1e-3

VARIANTS = {
    "leaking rate 1.0 (fast)": 1.0,
    "leaking rate 0.3 (mid)": 0.3,
    "leaking rate 0.1 (slow)": 0.1,
}


def esn_run(u: np.ndarray, leak: float, seed: int) -> np.ndarray:
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


WASHOUT_DRIVE = 200  # discarded in DRIVE steps, so the physical washout is band-invariant


def observed(u_sym: np.ndarray, leak: float, seed: int, k: int, arm: str) -> np.ndarray:
    """Observed states under an arm's band condition (same construction as E6).

    Washout is applied in DRIVE steps BEFORE the band condition. Discarding a fixed
    number of OBSERVED steps instead would discard k times as much drive at band k,
    so the reservoir would be given a different physical washout at every band --
    which is a confound, not a control.
    """
    if arm == "A-readout":
        full = esn_run(u_sym, leak, seed)
        return full[WASHOUT_DRIVE:][::k]
    full = esn_run(np.repeat(u_sym, k), leak, seed)
    return full[WASHOUT_DRIVE:][k - 1 :: k]


def single_stream_rank(
    leak: float, seed: int, k: int, arm: str, mode: str, hold: str
) -> tuple[float, int]:
    """Rank of the (S, N) matrix of states from ONE stream sampled at every observed step.

    mode 'kr': a plain random stream. mode 'gr': a stream that is a noisy variant of a
    base stream, so a LOW rank is the good outcome.
    hold 'states': lengthen the drive until S_STATES are retained (n-fixed discipline).
    hold 'drive' : keep the drive length fixed, so the retained count falls as 1/k.
    """
    rng = np.random.default_rng(seed + (0 if mode == "kr" else 10_000))
    # 'states': lengthen the drive so S_STATES survive decimation. 'drive': fixed drive.
    span = S_STATES * k if hold == "states" else S_STATES
    n_sym = WASHOUT_DRIVE + span + k
    u = rng.uniform(-1, 1, size=n_sym)
    if mode == "gr":
        base = rng.uniform(-1, 1, size=n_sym)
        u = np.clip(base + rng.normal(0, GR_NOISE, size=n_sym), -1, 1)
    obs = observed(u, leak, seed, k, arm)
    take = min(S_STATES, len(obs))
    X = obs[:take]
    tol = KR_TOL if mode == "kr" else GR_TOL
    r = float(np.linalg.matrix_rank(X, tol=tol))
    return r, int(take)


def summarise(vals: list[float]) -> tuple[float, float, float]:
    a = np.asarray(vals, dtype=float)
    m, sd = float(a.mean()), float(a.std(ddof=1))
    half = 2.262 * sd / np.sqrt(len(a))  # t(.975, df=9)
    return m, m - half, m + half


def main() -> None:
    rows: list[dict] = []
    for hold in ("states", "drive"):
        for arm in ("A-readout", "B-drive"):
            for name, leak in VARIANTS.items():
                for k in BANDS:
                    for mode in ("kr", "gr"):
                        vals, cols = [], 0
                        for s_i in range(N_SEEDS):
                            r, cols = single_stream_rank(
                                leak, SEED + s_i, k, arm, mode, hold
                            )
                            vals.append(r)
                        m, lo, hi = summarise(vals)
                        rows.append(
                            {
                                "hold": hold,
                                "arm": arm,
                                "variant": name,
                                "band_k": k,
                                "axis": mode.upper(),
                                "n_states": cols,
                                "mean": round(m, 3),
                                "ci_lo": round(lo, 3),
                                "ci_hi": round(hi, 3),
                            }
                        )

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "e7_single_stream_rank_rows.csv"
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {path}  ({len(rows)} rows)")

    for hold in ("states", "drive"):
        print(f"\n=== hold = {hold} ===")
        for arm in ("A-readout", "B-drive"):
            for axis in ("KR", "GR"):
                print(f"\n  {arm}  {axis}   (n_states per cell shown)")
                for name in VARIANTS:
                    cells = []
                    for k in BANDS:
                        r = next(
                            x
                            for x in rows
                            if x["hold"] == hold
                            and x["arm"] == arm
                            and x["variant"] == name
                            and x["band_k"] == k
                            and x["axis"] == axis
                        )
                        cells.append(f"{r['mean']:6.2f} [{r['ci_lo']:.2f},{r['ci_hi']:.2f}] n={r['n_states']}")
                    print(f"    {name:26} " + "  ".join(cells))


if __name__ == "__main__":
    main()

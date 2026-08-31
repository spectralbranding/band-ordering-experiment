# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "scipy", "scikit-learn", "pandas", "rcbench==1.0.10"]
# ///
"""E7b -- the SECOND rank protocol on the SECOND architecture family.

E7 measured the single-stream rank protocol on the leaking-rate family only, and the
note says so in print: what remains untested is whether the same protocol dependence
holds on the oscillator-bank family. This is the missing cell of that 2x2. E6b already
carries the oscillator substrate in E6's harness and E7 already carries the protocol in
the leaking-rate harness, so no new apparatus is introduced.

The cell matters because the two families have already come apart once, on the arm
being manipulated here. Under Arm A the leaking-rate family keeps its fastest variant
on top at every band, while the oscillator family loses its top rank at k=2 and never
recovers it (E1). A family difference on the readout arm can therefore appear on a
time-series axis, and it is not safe to assume it cannot appear on a rank axis under a
protocol that is no longer insulated from the readout band.

EVERYTHING EXCEPT THE SUBSTRATE IS E7'S. Seed, seed count, bands, node count, observed
state count, GR noise, rcbench's untuned tolerances, the 200-drive-step washout applied
before the band condition, both arms and both hold conditions. The substrate is E1's
`spring_run` reproduced unchanged, so cells are comparable to E1, E6b and E7 without
adjustment.

Predictions were fixed before this ran (see the note's E7b prediction record):
  P-E7b-1  the single-stream protocol DOES move generalisation rank on this family too;
           the protocol dependence is not a property of leaky integrators
  P-E7b-2  the movement is upward in k for variants not at ceiling, and the slowest
           variant moves most
  P-E7b-3  the ordering is preserved and the fast-minus-slow gap compresses; E1's Arm A
           demotion on this family does NOT transfer to the single-stream rank axis
  P-E7b-4  kernel rank is at the node count for every cell, as it was on E7's family
  P-E7b-5  the drive-length-fixed arm tracks the column count and is a confound

No mechanism is proposed. The retracted aliasing account is not reintroduced.

DESIGN. `states_fixed` holds the number of OBSERVED states fixed across bands, by
lengthening the drive until S states have been retained -- the study's own n-fixed
discipline. `drive_fixed` holds the drive length fixed instead, so the observed count
falls as 1/k; it is reported alongside as the declared confound.

Run:
    uv run --script code/e7b_single_stream_rank_oscillator.py

Writes output/e7b_single_stream_rank_oscillator_rows.csv. Deterministic; seed 20260830.
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
SPECTRAL_RADIUS = 0.95  # unused by this family; kept so the header matches E7's
S_STATES = 2 * N_NODES  # observed states in the single-stream matrix (>= node count)
GR_NOISE = 0.05
KR_TOL = 1e-6  # rcbench's own default thresholds, not tuned here
GR_TOL = 1e-3

# ---- oscillator-family constants, identical to E1 and E6b -----------------------
ZETA = 0.3  # damping ratio
BETA = 0.5  # cubic stiffening
K_RADIUS = 0.4  # spectral radius of the coupling matrix
SUBSTEPS = 4  # integration substeps per drive step

VARIANTS = {
    "omega 2.0 (fast)": 2.0,
    "omega 0.6 (mid)": 0.6,
    "omega 0.2 (slow)": 0.2,
}

TAU = {  # envelope time constant in drive steps, for the record
    "omega 2.0 (fast)": 1.67,
    "omega 0.6 (mid)": 5.56,
    "omega 0.2 (slow)": 16.67,
}


def esn_run(u: np.ndarray, omega: float, seed: int) -> np.ndarray:
    """Bank of coupled damped Duffing oscillators. `omega` IS the time constant.

    Byte-identical construction to E1's `spring_run` and E6b's, so cells are directly
    comparable across the extensions. The name is kept so the rest of this script is
    E7's code unchanged -- only the substrate behind it differs.
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


WASHOUT_DRIVE = (
    200  # discarded in DRIVE steps, so the physical washout is band-invariant
)


def observed(u_sym: np.ndarray, leak: float, seed: int, k: int, arm: str) -> np.ndarray:
    """Observed states under an arm's band condition (same construction as E7).

    Washout is applied in DRIVE steps BEFORE the band condition. Discarding a fixed
    number of OBSERVED steps instead would discard k times as much drive at band k,
    so the substrate would be given a different physical washout at every band --
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
                                "tau_drive_steps": TAU[name],
                                "band_k": k,
                                "axis": mode.upper(),
                                "n_states": cols,
                                "mean": round(m, 3),
                                "ci_lo": round(lo, 3),
                                "ci_hi": round(hi, 3),
                            }
                        )

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "e7b_single_stream_rank_oscillator_rows.csv"
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
                        cells.append(
                            f"{r['mean']:6.2f} [{r['ci_lo']:.2f},{r['ci_hi']:.2f}] n={r['n_states']}"
                        )
                    print(f"    {name:26} " + "  ".join(cells))

    # ---- the three verdicts the predictions are stated in, computed here ----------
    fast, mid, slow = list(VARIANTS)

    def g(hold: str, arm: str, name: str, k: int, axis: str) -> dict:
        return next(
            x
            for x in rows
            if x["hold"] == hold
            and x["arm"] == arm
            and x["variant"] == name
            and x["band_k"] == k
            and x["axis"] == axis
        )

    print("\n=== VERDICTS (hold = states, Arm A) ===")
    moved = []
    for name in VARIANTS:
        a, b = g("states", "A-readout", name, 1, "GR"), g(
            "states", "A-readout", name, 8, "GR"
        )
        overlap = a["ci_lo"] <= b["ci_hi"] and b["ci_lo"] <= a["ci_hi"]
        moved.append(not overlap)
        print(
            f"  P-E7b-1/2 {name:20} GR k=1 {a['mean']:6.2f} -> k=8 {b['mean']:6.2f}"
            f"  delta {b['mean'] - a['mean']:+6.2f}  "
            f"{'RESOLVED' if not overlap else 'unresolved (CIs overlap)'}"
        )
    print(f"  P-E7b-1: generalisation rank moves on this family: {any(moved)}")

    tops = {}
    for k in BANDS:
        means = {n: g("states", "A-readout", n, k, "GR")["mean"] for n in VARIANTS}
        tops[k] = min(means, key=lambda n: means[n])  # LOWER is better on GR
    gap1 = (
        g("states", "A-readout", slow, 1, "GR")["mean"]
        - g("states", "A-readout", fast, 1, "GR")["mean"]
    )
    gap8 = (
        g("states", "A-readout", slow, 8, "GR")["mean"]
        - g("states", "A-readout", fast, 8, "GR")["mean"]
    )
    print(
        f"  P-E7b-3: GR top rank per band: "
        + "  ".join(f"k={k}:{tops[k]}" for k in BANDS)
        + f"   preserved={len(set(tops.values())) == 1}"
    )
    print(
        f"           slow-minus-fast gap {gap1:+.2f} (k=1) -> {gap8:+.2f} (k=8); "
        f"|gap| {'compresses' if abs(gap8) < abs(gap1) else 'does not compress'}"
    )

    kr_all = [
        g(h, a, n, k, "KR")["mean"]
        for h in ("states",)
        for a in ("A-readout", "B-drive")
        for n in VARIANTS
        for k in BANDS
    ]
    print(
        f"  P-E7b-4: kernel rank at the node count in every cell: "
        f"{all(v == float(N_NODES) for v in kr_all)}  "
        f"(min {min(kr_all):.2f}, max {max(kr_all):.2f})"
    )

    # ---- paired per-seed differences, which is the form the note reports in ------
    # Recomputed from the same seeds and the same call, so these are the cells above
    # taken one seed at a time rather than a second measurement.
    def paired(name: str, axis: str, k_lo: int, k_hi: int, arm: str = "A-readout"):
        leak = VARIANTS[name]
        d = [
            single_stream_rank(leak, SEED + i, k_hi, arm, axis.lower(), "states")[0]
            - single_stream_rank(leak, SEED + i, k_lo, arm, axis.lower(), "states")[0]
            for i in range(N_SEEDS)
        ]
        m, lo, hi = summarise(d)
        return m, lo, hi, sum(x > 0 for x in d)

    print("\n=== PAIRED per-seed differences, Arm A, hold = states ===")
    for axis in ("GR", "KR"):
        for name in VARIANTS:
            m, lo, hi, pos = paired(name, axis, 1, 8)
            print(
                f"  {axis}  {name:20} k=8 minus k=1: {m:+6.2f} [{lo:+.2f}, {hi:+.2f}]"
                f"  ({pos}/{N_SEEDS} seeds positive)"
            )
    m, lo, hi, pos = paired(slow, "KR", 1, 2)
    print(
        f"  KR  {slow:20} k=2 minus k=1: {m:+6.2f} [{lo:+.2f}, {hi:+.2f}]"
        f"  ({pos}/{N_SEEDS} seeds positive)"
    )

    print("\n=== PAIRED slow-minus-fast gap on GR, Arm A, hold = states ===")
    for k in BANDS:
        d = [
            single_stream_rank(
                VARIANTS[slow], SEED + i, k, "A-readout", "gr", "states"
            )[0]
            - single_stream_rank(
                VARIANTS[fast], SEED + i, k, "A-readout", "gr", "states"
            )[0]
            for i in range(N_SEEDS)
        ]
        m, lo, hi = summarise(d)
        print(
            f"  k={k}: {m:+6.2f} [{lo:+.2f}, {hi:+.2f}]  "
            f"({sum(x < 0 for x in d)}/{N_SEEDS} seeds negative)"
        )


if __name__ == "__main__":
    main()

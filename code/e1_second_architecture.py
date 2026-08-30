# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "scipy", "scikit-learn", "pandas", "matplotlib", "rcbench==1.0.10"]
# ///
"""E1 -- does the band inversion replicate on a second architecture?

Extension E1 of the band-ordering study. The published result rests entirely on
leaky echo-state networks, whose time constant is a first-order leak. If the Arm B
inversion is a property of leaky integrators rather than of substrates generally,
the finding is far narrower than the README implies. This runs the same two arms,
the same band grid and the same n-fixed discipline on a mechanically different
family and reports whether the inversion replicates.

THE SECOND ARCHITECTURE. A bank of damped Duffing oscillators -- second-order
resonant mechanical dynamics, not first-order leaky integration. Its time constant
is the envelope decay 1/(zeta*omega), set by a natural frequency rather than by a
leak, and it carries a resonance the ESN does not have. Substrates within the family
differ ONLY in omega, exactly as the ESN substrates differ only in leak.

STATIC GAIN IS EQUALISED ACROSS THE THREE OSCILLATOR SUBSTRATES, DELIBERATELY. The
drive enters as a displacement of the equilibrium, so the DC fixed point solves
x + beta*x^3 = K@x + win*u independently of omega. Without this a low-frequency
oscillator has an enormous DC gain and the three substrates would differ in static
gain as well as in time constant, which is not the comparison being made. The ESN
family is already gain-normalised in the same sense: its DC fixed point
x* = tanh(W x* + win u) does not depend on the leak.

CALIBRATION CRITERION, FIXED BEFORE ANY OUTCOME WAS READ. The three oscillator
substrates were placed at envelope time constants of 1.67, 5.56 and 16.67 drive
steps, chosen to span the ESN family's 1.0, 2.8 and 9.5 so that the k=1..8 band grid
straddles the substrates' time constants in both families. Calibration targeted the
time-constant span and numerical stability, never an ordering.

A THIRD FAMILY WAS ATTEMPTED AND REJECTED ON DESIGN GROUNDS, NOT ON ITS RESULT. A
delay-based reservoir in the Appeltant construction cannot be used here: theta/T
sets both the physical time constant and the virtual-node resolution, so reaching a
time constant of tau drive steps with N virtual nodes forces theta/T = 1/(N*tau),
which is far below the regime in which virtual nodes are resolved. The sign-
alternating mask then averages out across the smoothing window, the drive is
attenuated and capacity collapses to a value that barely moves with the time
constant. Run `--delay-probe` to reproduce the table this rests on.

Run:
    uv run --script code/e1_second_architecture.py
    uv run --script code/e1_second_architecture.py --delay-probe

Writes output/e1_architecture_rows.csv and prints the tables and verdicts.
Deterministic: seed 20260830, and the ESN arm reuses the main study's seeds and
input sequences so the two families are compared on identical drives.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
from rcbench.tasks.ipc import IPCEvaluator

SEED = 20260830
N_SEEDS = 10
OUT = Path(__file__).resolve().parents[1] / "output"

BANDS = (1, 2, 4, 8)
N_FIXED = 350
MAX_DELAY = 8
MAX_DEGREE = 2
N_NODES = 60
SPECTRAL_RADIUS = 0.95
T95 = 2.262  # t(.975, df=9)

# Oscillator family constants, shared by all three of its substrates.
ZETA = 0.3  # damping ratio
BETA = 0.5  # cubic stiffening
K_RADIUS = 0.4  # spectral radius of the coupling matrix
SUBSTEPS = 4  # integration substeps per drive step


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

    Identical to the main study's implementation, reproduced here so E1 runs
    standalone and so both families see the same drives.
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


def spring_run(u: np.ndarray, omega: float, seed: int) -> np.ndarray:
    """Bank of coupled damped Duffing oscillators. `omega` IS the time constant.

    Second-order resonant dynamics: the substrate has an oscillation period as well
    as a decay envelope, and neither exists in a leaky integrator. Integrated by
    semi-implicit Euler at SUBSTEPS steps per drive step. The per-oscillator
    frequency spread is drawn from the same seed in every substrate, so the three
    differ only in the scale factor `omega`.
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


def delay_run(
    u: np.ndarray, alpha: float, seed: int, n_virtual: int, eta: float
) -> np.ndarray:
    """Appeltant-style delay reservoir. Used ONLY by the rejection probe."""
    rng = np.random.default_rng(seed)
    mask = rng.choice((-1.0, 1.0), size=n_virtual)
    x = np.zeros(n_virtual)
    out = np.empty((len(u), n_virtual))
    for i, ut in enumerate(u):
        prev = x
        new = np.empty(n_virtual)
        carry = prev[-1]
        for j in range(n_virtual):
            carry = alpha * carry + (1 - alpha) * np.tanh(
                0.5 * prev[j] + eta * mask[j] * ut
            )
            new[j] = carry
        x = new
        out[i] = x
    return out


FAMILIES = {
    "esn": {
        "runner": esn_run,
        "label": "leaky echo-state network (first-order leak)",
        "substrates": {
            "esn-fast (leak 1.0)": 1.0,
            "esn-mid (leak 0.3)": 0.3,
            "esn-slow (leak 0.1)": 0.1,
        },
        "tau": {  # time constant in drive steps, for the record
            "esn-fast (leak 1.0)": 1.0,
            "esn-mid (leak 0.3)": 2.8,
            "esn-slow (leak 0.1)": 9.5,
        },
    },
    "mass-spring": {
        "runner": spring_run,
        "label": "damped Duffing oscillator bank (second-order resonant)",
        "substrates": {
            "spring-fast (omega 2.0)": 2.0,
            "spring-mid (omega 0.6)": 0.6,
            "spring-slow (omega 0.2)": 0.2,
        },
        "tau": {
            "spring-fast (omega 2.0)": 1.67,
            "spring-mid (omega 0.6)": 5.56,
            "spring-slow (omega 0.2)": 16.67,
        },
    },
}


def summarise(vals: list[float]) -> tuple[float, float, float, float]:
    """Mean, SD, and a t-based 95% CI; returns (mean, sd, lo, hi)."""
    a = np.asarray(vals, dtype=float)
    m, sd = float(a.mean()), float(a.std(ddof=1))
    half = T95 * sd / np.sqrt(len(a))
    return m, sd, m - half, m + half


def delay_probe() -> None:
    """Reproduce the table on which the delay-reservoir rejection rests."""
    rng = np.random.default_rng(SEED)
    u = rng.uniform(-1, 1, size=3000)
    print("DELAY-RESERVOIR REJECTION PROBE")
    print("  Reaching a time constant of tau drive steps with N virtual nodes forces")
    print("  theta/T = 1/(N*tau). Virtual nodes are resolved only when theta/T is of")
    print(
        "  order 0.2. Every cell below is far under that, at every N and every gain.\n"
    )
    print(
        f"{'N_virt':>7}{'eta':>6}{'tau':>7}{'alpha':>10}"
        f"{'theta/T':>10}{'|x|max':>10}{'ipc':>9}"
    )
    for nv in (60, 20, 10):
        for eta in (0.6, 3.0):
            for tau in (1.0, 3.3, 10.0):
                al = float(np.exp(-1.0 / (nv * tau)))
                S = delay_run(u, al, SEED, nv, eta)
                print(
                    f"{nv:>7}{eta:>6.1f}{tau:>7.2f}{al:>10.5f}"
                    f"{-np.log(al):>10.4f}{np.abs(S).max():>10.4f}"
                    f"{ipc(u[:N_FIXED], S[:N_FIXED]):>9.3f}",
                    flush=True,
                )
    print(
        "\n  Capacity barely moves with the time constant in any configuration, and the\n"
        "  states are driven down as tau rises because the sign-alternating mask averages\n"
        "  out across the smoothing window. The family cannot both span the ESN's\n"
        "  time-constant range and remain a working reservoir. REJECTED ON DESIGN."
    )


def main() -> None:
    rows: list[dict] = []
    n_needed = N_FIXED * max(BANDS) + 200

    for s_i in range(N_SEEDS):
        seed = SEED + s_i
        rng = np.random.default_rng(seed)
        u_long = rng.uniform(-1, 1, size=n_needed)  # SAME drive for both families
        for fam, spec in FAMILIES.items():
            runner = spec["runner"]
            for name, param in spec["substrates"].items():
                S_full = runner(u_long, param, seed)
                for k in BANDS:
                    rows.append(
                        {
                            "family": fam,
                            "substrate": name,
                            "tau_drive_steps": spec["tau"][name],
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
                    S_slow = runner(np.repeat(u_slow, k), param, seed)[k - 1 :: k][
                        :N_FIXED
                    ]
                    rows.append(
                        {
                            "family": fam,
                            "substrate": name,
                            "tau_drive_steps": spec["tau"][name],
                            "arm": "B-drive",
                            "band_k": k,
                            "seed": seed,
                            "n": N_FIXED,
                            "ipc": round(ipc(u_slow[:N_FIXED], S_slow), 3),
                        }
                    )
        print(f"  seed {seed} done ({s_i + 1}/{N_SEEDS})", flush=True)

    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "e1_architecture_rows.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    def cell(fam, sub, arm, k):
        return [
            r["ipc"]
            for r in rows
            if r["family"] == fam
            and r["substrate"] == sub
            and r["arm"] == arm
            and r["band_k"] == k
        ]

    for fam, spec in FAMILIES.items():
        subs = list(spec["substrates"])
        print(f"\n\n########## FAMILY: {fam} -- {spec['label']} ##########")
        for arm, title in (
            ("A-readout", "ARM A -- native drive, decimated READOUT"),
            ("B-drive", "ARM B -- driven AND read at the coarse rate"),
        ):
            print(f"\n=== {title} ===  mean [95% CI] over {N_SEEDS} seeds")
            print(f"{'substrate':<26}" + "".join(f"{'k=' + str(k):>22}" for k in BANDS))
            for s_name in subs:
                cells = []
                for k in BANDS:
                    m, _, lo, hi = summarise(cell(fam, s_name, arm, k))
                    cells.append(f"{m:>8.2f} [{lo:5.2f},{hi:5.2f}]")
                print(f"{s_name:<26}" + "".join(f"{c:>22}" for c in cells))
            print("  ORDERING by mean (best first):")
            for k in BANDS:
                means = {s: summarise(cell(fam, s, arm, k))[0] for s in subs}
                order = sorted(means, key=lambda s: -means[s])
                print(f"    k={k}: " + "  >  ".join(o.split(" ")[0] for o in order))

        # ---- the replication test, stated the same way for every family ----
        fast, mid = subs[0], subs[1]
        print(f"\n=== INVERSION TEST (Arm B), per seed, {N_SEEDS} seeds ===")
        hits = 0
        for s_i in range(N_SEEDS):
            seed = SEED + s_i

            def v(sub, k, sd=seed):
                return next(
                    r["ipc"]
                    for r in rows
                    if r["family"] == fam
                    and r["substrate"] == sub
                    and r["arm"] == "B-drive"
                    and r["band_k"] == k
                    and r["seed"] == sd
                )

            hits += (v(fast, 1) > v(mid, 1)) and (v(mid, 8) > v(fast, 8))
        print(f"  fast beats mid at k=1 AND mid beats fast at k=8: {hits}/{N_SEEDS}")
        for k in (1, 8):
            diffs = [
                cell(fam, fast, "B-drive", k)[i] - cell(fam, mid, "B-drive", k)[i]
                for i in range(N_SEEDS)
            ]
            m, _, lo, hi = summarise(diffs)
            print(f"  fast - mid at k={k}: {m:+.2f} [{lo:+.2f}, {hi:+.2f}]")

        # Arm A verdict: is the top rank preserved across the whole sweep?
        top_a = {
            k: max(subs, key=lambda s: summarise(cell(fam, s, "A-readout", k))[0])
            for k in BANDS
        }
        print(
            f"  ARM A top rank across bands: "
            + " -> ".join(top_a[k].split(" ")[0] for k in BANDS)
            + ("   (PRESERVED)" if len(set(top_a.values())) == 1 else "   (REORDERED)")
        )


if __name__ == "__main__":
    if "--delay-probe" in sys.argv:
        delay_probe()
    else:
        main()

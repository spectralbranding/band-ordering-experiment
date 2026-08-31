# Rank Order Under a Capacity Benchmark Is Conditional on the Observation Band and the Delay Horizon

Dmitry Zharnikov

ORCID: 0009-0000-6893-9231

DOI: [10.5281/zenodo.22206844](https://doi.org/10.5281/zenodo.22206844)

Working Paper v1.0.0 – August 2026

---

## Abstract

Reservoir-computing benchmarks increasingly report rank orderings, but rarely the observation band or the delay horizon at which the ranking was taken. This note measures both conditions on a common grid, on two architecture families. Under a readout-only change of band, the fastest system loses -6.61 information processing capacity [-6.89, -6.33] while its kernel rank moves -0.50 [-1.27, +0.27]: a readout band destroys memory and leaves separation intact, because rank measures, under the ensemble protocol, are computed from one state per input stream. That insulation belongs to the protocol and not to rank measures: under the field's second protocol the manipulation moves generalisation rank in both, by up to twenty-eight points, and kernel rank in one. Under a change of drive band the ordering reverses in 10 of 10 seeds in both, and the band at which the crossover occurs moves with the delay horizon. The systems compared differ only in their time constant, so this is a demonstration of an effect the field already predicts, not a discovery; the contribution is the measurement and the reporting condition that follows. The note recommends that any published ranking state its observation band, its delay horizon, and which axes under which protocol.

**Keywords**: reservoir computing, benchmarking, information processing capacity, kernel rank, generalisation rank, measurement protocol, observation band, delay horizon, reporting standards, timescale matching.

---

**This is a simulation study, and the limit belongs here rather than in a limitations section.** Four systems were run. The only physical one — a self-organising nanowire network, recorded elsewhere and re-analysed here — is excluded from every ordering claim below, because at the sample budget the band sweep permits it is estimator-starved while the simulated systems are not. What carries the result is two families of simulated variants. **Nothing here is a survey of matter, and nothing here speaks to how computational capacity is distributed across materials** [@nakajima-2020-physical-reservoir-computing; @tanaka-2019-physical-reservoir-computing-review].

The finding a practitioner is least likely to have predicted is not the rank reversal. It is that the reversal does not reach every axis of the standard behaviour space. Reading an existing recording less often costs the fastest variant **-6.61** in total information processing capacity, a resolved loss, while costing it **-0.50** in kernel rank, which is unresolved. The two manipulations usually collapsed into the phrase *changing the sampling rate* act on different capacities: one destroys memory, the other does not touch separation. Stated at the grain that matters, and this is the note's single proposition: **band conditionality of a readout attaches to memory functionals and not to state-rank functionals.**

That result sharpens rather than softens the ranking result behind it. Slowing the drive — a genuine change of band, in the sense used when a stimulus inter-step interval is varied [@ishida-2023-ipc-living-brain] — reorders systems that differ in nothing but their time constant, in 10 of 10 seeds, in both families tested, and the band at which they cross over moves with the delay horizon of the capacity estimator. A published ranking is therefore a statement about those systems *at that band and that horizon*. Neither condition is usually published.

**The effect itself is expected, and the note says so in its own voice — but the canonical source says something sharper than "expected".** Leaky-integrator units exist precisely so that a leaking rate can match a reservoir to the temporal characteristics of a task, and the stability conditions were derived when they were introduced [@jaeger-2007-leaky-integrator-esn]; the parameter has been textbook for as long as the field has had a textbook [@lukosevicius-2009-reservoir-computing-approaches]. That same paper, however, treats the step size as settled: optimising it is "by and large a non-issue", subsampling by an integer factor is a matter of "computational resource management", and beyond two stated provisos — that the coarsening discards no valuable information from the inputs, and that it incurs no significant discretization error — "the quality of the ESN model should remain unaffected". **The measurement below is what those two provisos cost when they fail.** What was missing was not the idea but the measurement: a ranking reported as a function of band and horizon on a common grid, with the axis dependence separated out. This is a demonstration, not a discovery, and the contribution is the reporting condition it licenses.

**What is new is the crossing, not either factor.** Table 1 places the note against the class it belongs to. Existing work compares many systems at one operating point, or sweeps a band on one system. Nobody crosses the two. The recent tutorial review and critique of reservoir-computing benchmarks is the most likely place for such a measurement to already exist; it does not contain one [@wringe-2025-reservoir-computing-benchmarks]. Its best-practice section is the sharpest available test of the point, and it passes in the note's favour: the reporting checklist it gives for an echo-state experiment names the node count, the input bias, **the leakage rate**, the noise, the output feedback, the connectivity, the topology, the weight distribution, and the washout, training and testing lengths — and names neither the observation band nor the delay horizon of the capacity estimator.

Table 1: What the Incumbent Class Varies, and What This Note Varies.

| Work | Systems compared | Band swept | Horizon swept | Axes reported |
|---|---|---|---|---|
| Dale et al [-@dale-2019-substrate-independent-framework], CHARC | many | no — one operating point | no | kernel rank, generalisation rank, memory capacity |
| Ishida et al [-@ishida-2023-ipc-living-brain] | one | yes — eight inter-step intervals | no | capacity |
| Ortín and Pesquera [-@ortin-2019-tradeoff-capacity-rate] | one delay system | yes — rate | no | capacity |
| Nishioka et al [-@nishioka-2025-ultrawideband-ion-gating-reservoir] | one | yes — pulse period, four orders of magnitude | no | capacity |
| Seshasai Chaitanya et al [-@seshasai-chaitanya-2025-tunable-decay-reservoir-node] | one node type | input frequency relative to $1/\tau$ | no | task performance |
| Li et al [-@li-2025-homogeneous-memristors-tunable-decay] | one platform | decay time modulated by read bias | no | task accuracy |
| Pilati et al [-@pilati-2026-rcbench], RCbench | one, demonstrated | no — band exposed and pinned by design | no | standardised suite |
| **This note** | **two families, three variants each** | **yes** | **yes** | **all four, separated** |

*Notes*: "Band swept" means the observation or drive interval is varied within the study. RCbench exposes the sampling rate explicitly and pins it to consistent defaults, which is the correct engineering decision and is the condition this note asks to be reported alongside a comparative claim.

## Method

### *The two arms, which are not the same experiment.*

**Arm A reads less often.** The system is driven at its native rate and the observer keeps every $k$-th sample. This is the only manipulation available to anyone re-analysing an archived recording, because a recording cannot be re-driven. The unread samples still enter the system as drive.

**Arm B drives and reads slower.** The input is stretched by zero-order hold and every $k$-th sample is kept, so the band change reaches the dynamics. This is a band change in the sense that a varied stimulus interval is one, and it is available only for simulated systems.

Separating them is not a formality. They answer different questions and, on the ranking question, they give opposite answers — which means decimating an archive is not a valid proxy for a band change. The practical consequence is unwelcome and is stated rather than buried: **the drive-band question cannot be settled from archived recordings.** It needs control of the drive.

### *The variants, and why they are not called substrates.*

Two architecture families, three variants each, differing in one parameter.

**Leaking-rate variants.** Three leaky echo-state networks, identical in size (60 nodes), topology, spectral radius (0.95), input scaling and seed, differing only in leak rate (1.0, 0.3, 0.1), which *is* the time constant — 1.0, 2.8 and 9.5 drive steps.

**Oscillator-bank variants.** Three banks of coupled damped Duffing oscillators differing only in natural frequency $\omega$ (2.0, 0.6, 0.2), giving envelope time constants of 1.67, 5.56 and 16.67 drive steps, placed to straddle the leaking-rate family's range on the same grid. An oscillator bank is the minimal continuous-time analogue of a leaking-rate network and the simplest cartoon of a physically resonant reservoir; it is included because it has an oscillation period that a leaky integrator does not, and that difference turns out to matter. Calibration targeted time-constant span and numerical stability, never an ordering.

**The manipulated factor is the time constant; the replication factor is architecture family.** These are parameterised variants within an architecture family, not different substrates, and calling them substrates would import a materials claim this design cannot support. The word *substrate* is reserved below for the interpretive target — the claim a published *substrate* ranking makes — which is the only place it earns its keep. A third family, a delay-based reservoir in the standard single-node construction [@appeltant-2011-single-dynamical-node], was attempted and rejected **on design grounds before its result was read**: the delay-to-clock ratio sets both the physical time constant and the virtual-node resolution, so a family spanning this time-constant range cannot simultaneously remain a working reservoir.

### *The estimator, the axes, and what was held fixed.*

Total information processing capacity is used as the scalar, bounded by the number of linearly independent state variables and equalling it under fading memory [@dambre-2012-information-processing-capacity]. The three behaviour-space axes are those of the substrate-independent characterisation framework — kernel rank, generalisation rank and memory capacity [@dale-2019-substrate-independent-framework] — computed under the ensemble protocol in which distinct input streams each produce one state and the stacked states are ranked [@vidamour-2022-nanomagnetic-reservoir-capability]. On generalisation rank, lower is better, so every ordering on that axis reads in the opposite direction to the other three.

Six things were held fixed and are declared rather than assumed, because each is a question a reader is entitled to ask of a band sweep:

1. **Sample count is fixed at $n = 350$ across every band.** Capacity is strongly biased by sample count, so a naive decimation sweep confounds band with estimator bias. A saturation control is reported alongside.
2. **The drive is i.i.d.**, which the capacity basis requires. The simulated arms draw a fresh input per seed; the physical recording was checked at lag-1 autocorrelation .015. Decimating an i.i.d. series leaves it i.i.d., so Arm A does not disturb the basis.
3. **Spectral radius and input scaling were not co-tuned with the time constant.** Both are constants of the run; the leak rate is the only quantity that differs between variants.
4. **No readout is trained anywhere in the pipeline**, so there is no regularisation parameter available to interact with the band. Capacity is a projection onto an orthogonal basis, not a fitted model.
5. **The maximum degree of the capacity basis is fixed at 2 and was never swept.** This is a declared choice, and it carries a bounded comparability cost against work that measured to the sixth degree [@ishida-2023-ipc-living-brain]. Either outcome of a sweep would strengthen the claim below — a further conditionality, or robustness — so the choice is not load-bearing, but it is not free either and is not hidden here.
6. **Ten independent seeds per variant**, each drawing a fresh system and a fresh input; intervals are $t$-based at 95%, $\mathrm{df} = 9$. No correction for multiplicity is applied: the primary statistic is the per-seed count of inversions, and the per-band intervals are description.

The band grid is $k \in \{1, 2, 4, 8\}$ and the delay horizon is swept separately over $d \in \{2, 4, 8, 16, 32\}$ at two sample budgets.

## Results

### *A readout band destroys memory and leaves separation intact.*

Table 2 is the note's lead result. Across a factor of eight in readout interval, the two time-series axes move and the two state-rank axes do not.

Table 2: Effect of a Readout-Only Band Change (Arm A) on the Fastest Variant, by Axis and Family.

| Axis | Leaking-rate family | Oscillator-bank family |
|---|---|---|
| Information processing capacity | **-6.61 [-6.89, -6.33]** | top rank lost; 5.91 to 0.98 |
| Memory capacity | large, resolved loss | top rank lost; 2.91 to 0.12 |
| Kernel rank | **-0.50 [-1.27, +0.27]** | top rank kept; 37.00 to 37.50 |
| Generalisation rank | no detectable change | top rank kept; 9.60 to 9.30 |

*Notes*: Change from $k=1$ to $k=8$; mean [95% CI] where a paired interval is available. Lower is better on generalisation rank. The two families were run separately so that family and axis are not swept together.

The dissociation is clean on both families and is cleaner on the oscillator-bank family, where the same manipulation on the same variants demotes the fastest on both time-series axes and leaves it untouched on both state-rank axes.

**This is structural and must not be dressed as a discovery about materials.** Kernel and generalisation rank take one state per input stream. A manipulation that changes only which samples are kept cannot move them; a manipulation that changes the drive, and therefore the dynamics, can. Two of the three behaviour-space axes are consequently *orthogonal by construction* to a readout-band question — which means that reporting a single capacity scalar is not the deficiency it appears to be when a multi-axis framework is available, and that a study reporting only rank measures would have concluded, wrongly, that the readout band costs nothing.

**One apparent reordering on generalisation rank is not one.** Under Arm A the top-ranked variant appears to change between bands on that axis. The middle-minus-slow difference is unresolved at three of four bands (+0.10 [-0.43, +0.63] at $k=1$; +0.00 [-0.89, +0.89] at $k=4$; +0.50 [-0.63, +1.63] at $k=8$) and the apparent flip rests on a mean difference of exactly zero. **There is no reordering on generalisation rank under Arm A; the variants are tied**, and the vocabulary of one axis must not travel to another.

### *The dissociation belongs to the rank protocol, and the second protocol was run.*

The field computes kernel and generalisation rank in two ways, and they coincide only in a limiting case [@wringe-2025-reservoir-computing-benchmarks]. Everything above uses the **ensemble** form: distinct input streams, one final state each, stacked and ranked [@vidamour-2022-nanomagnetic-reservoir-capability]. The **single-stream** form runs one stream and records the state at every observed timepoint [@dale-2019-substrate-independent-framework]. The insulation argument is about how many states enter the matrix, so it does not transfer, and the second protocol was run rather than left as a caveat — on both architecture families, so that protocol and family are crossed rather than confounded. Predictions were fixed before each run.

Table 5: Generalisation Rank Under a Readout-Only Band Change, by Protocol and Family.

| Protocol | Family | Variant | $k=1$ | $k=8$ | Movement |
|---|---|---|---|---|---|
| Ensemble | both | all six | — | — | no detectable change |
| Single-stream | leaking rate | 1.0 (fast) | 60.00 | 60.00 | at ceiling; none |
| Single-stream | leaking rate | 0.3 (mid) | 52.60 [49.84, 55.36] | 58.50 [57.14, 59.86] | **+5.90, resolved** |
| Single-stream | leaking rate | 0.1 (slow) | 24.90 [22.63, 27.17] | 39.90 [36.61, 43.19] | **+15.00, resolved** |
| Single-stream | oscillator | $\omega$ 2.0 (fast) | 60.00 | 60.00 | at ceiling; none |
| Single-stream | oscillator | $\omega$ 0.6 (mid) | 53.70 [51.46, 55.94] | 60.00 | **+6.30, resolved** |
| Single-stream | oscillator | $\omega$ 0.2 (slow) | 25.80 [24.09, 27.51] | 54.30 [52.36, 56.24] | **+28.50, resolved** |

*Notes*: Mean [95% CI] over ten seeds, 60 nodes, observed-state count held fixed at 120 across bands. Lower is better on generalisation rank; a movement upward is therefore a loss. Resolved means the two intervals do not overlap. The two families were run on identical settings apart from the substrate. Holding the *drive* length fixed instead is a confound and was run as one on both families: the observed count then falls as $1/k$ and rank tracks it exactly (31.00 at 31 states, 16.00 at 16), which is estimator starvation and not a band effect.

**The insulation is a property of the protocol, not of rank measures.** The manipulation that leaves generalisation rank untouched under the ensemble form moves it by fifteen points, resolved, under the single-stream form. **A study reporting "generalisation rank" without naming its protocol has not said which of these two results it obtained.**

**And it is not a property of leaky integrators.** The same protocol was run on the oscillator-bank family with every setting but the substrate held identical, and it moves generalisation rank further there than on the family it was first measured on: paired across seeds, the slowest variant rises **+28.50 [+26.28, +30.72]** from $k=1$ to $k=8$ and the middle variant **+6.30 [+4.06, +8.54]**, each 10 of 10 seeds in the same direction. Predictions were fixed before that run as they were before the first, and this was one of them. **The family that answers a readout-only band change differently on the capacity axis answers it the same way here, and more strongly** — which is what makes the protocol, rather than the architecture, the thing a reader needs told.

**The kernel-rank ceiling, however, is a property of the architecture, and the prediction that it was not is recorded as having failed.** Under the single-stream form on the leaking-rate family kernel rank sits at the node count — 60.00 for every variant, at every band, in both arms — so it is at ceiling and discriminates nothing there, where under the ensemble form it separated the variants cleanly. That was predicted to hold on the oscillator-bank family and does not. The slowest oscillator variant sits at **51.30 [49.87, 52.73]** at $k=1$ and rises **+8.70 [+7.27, +10.13]**, 10 of 10 seeds, to the node count by $k=2$, where it stays. **On that family a readout-only band change moves kernel rank too** — the axis the ensemble protocol places entirely beyond a readout manipulation's reach. The ceiling is therefore reported for the family it was measured on and not for the protocol.

**In neither family is the movement a demotion of the fastest.** The fastest variant is already at ceiling in both, and what moves is the slow and middle variants rising toward it, so the ordering is preserved at every band while the gap between fastest and slowest compresses — from 35.1 to 20.1 on the leaking-rate family, and monotonically from **34.20 [32.49, 35.91]** through 23.00 and 11.40 to **5.70 [3.76, 7.64]** on the oscillator-bank family, 10 of 10 seeds in the same direction at every band. That direction was predicted before both runs; the ordering reversal offered as the alternative did not occur in either, and is recorded as not having occurred. **The Arm A demotion that separates the two families on the capacity axis does not reach this one.** What the compression costs is the axis itself: by $k=8$ two of the three oscillator variants sit exactly at the ceiling, so a generalisation-rank comparison taken at a wide readout band discriminates between fewer systems than the same comparison taken at a narrow one.

### *Rank order reverses when the drive band changes.*

Table 3 gives the ordering as a function of band under Arm B for both families.

Table 3: Total Information Processing Capacity by Observation Band, Arm B, Both Families.

| Variant | $k=1$ | $k=2$ | $k=4$ | $k=8$ |
|---|---|---|---|---|
| Leaking rate 1.0 (fast) | **8.04** [7.79, 8.29] | **6.05** [5.55, 6.55] | 3.46 [3.11, 3.80] | 1.99 [1.81, 2.17] |
| Leaking rate 0.3 (mid) | 2.57 [2.16, 2.97] | 3.51 [3.05, 3.96] | **4.18** [3.67, 4.70] | **3.70** [3.24, 4.16] |
| Leaking rate 0.1 (slow) | 1.55 [1.29, 1.80] | 1.94 [1.62, 2.26] | 2.60 [2.19, 3.00] | 3.46 [3.03, 3.90] |
| $\omega = 2.0$ (fast) | **5.91** [5.57, 6.25] | 3.75 [3.49, 4.01] | 2.39 [2.20, 2.57] | 1.35 [1.18, 1.52] |
| $\omega = 0.6$ (mid) | 3.91 [3.35, 4.47] | **5.59** [5.22, 5.96] | **5.48** [5.03, 5.93] | 3.82 [3.58, 4.05] |
| $\omega = 0.2$ (slow) | 1.86 [1.67, 2.05] | 2.94 [2.45, 3.43] | 4.43 [3.94, 4.92] | **6.20** [5.95, 6.45] |

*Notes*: Mean [95% CI] over ten seeds, $n$ fixed at 350. Bold marks the leading variant at each band within each family.

![](figures/band_ordering.png)

**Figure 1.** Capacity against observation band for the three leaking-rate variants, both arms. Left: the readout-only arm, where the fastest variant is first at every band. Right: the drive arm, where it goes from first to last. Mean of ten seeds, bars are 95% CI, sample count held fixed at 350 across all bands. The one physical system is omitted: it had not reached estimator saturation at that budget and cannot be fairly ranked.

![](figures/e1_architecture.png)

**Figure 2.** The same grid on both architecture families. Top row, leaking-rate variants; bottom row, oscillator-bank variants. Slowing the drive inverts the ordering in both families, so the inversion is not a property of leaky integrators. Decimating the readout reorders nothing in the first family but costs the fastest variant its top rank in the second. No mechanism is claimed for that difference: an aliasing account was tested against a twelve-point sweep and retracted, and what replaces it is a description of a graded, thresholdless timescale mismatch. Series are labelled by their identifiers in the published result tables.

**The fastest variant goes from first to last.** On the leaking-rate family the ordering at $k=1$ is fast > mid > slow and at $k=8$ it is mid > slow > fast; the fast-minus-mid difference is **+5.47 [+4.97, +5.98]** and **-1.71 [-2.07, -1.35]** at the two ends, two intervals of opposite sign, both excluding zero. On the oscillator-bank family the reversal is complete — slow > mid > fast — with fast-minus-slow running **+4.05 [+3.57, +4.53]** at $k=1$ and **-4.85 [-5.09, -4.60]** at $k=8$. **In both families the inversion holds in 10 of 10 seeds.** It is not a property of leaky integrators.

Arm B moves every axis, including the state-rank axes it was Arm A that could not touch: on the leaking-rate family kernel rank falls from 56.4 > 30.0 > 21.3 to 27.4 > 22.8 > 15.9 across the sweep, and on the oscillator-bank family the fastest variant falls from 37.00 to 6.30 while the slowest rises from 30.50 to 40.30. **On the oscillator-bank family this is a demotion and not an inversion**, because at $k=1$ the fastest and middle variants are tied on that axis (+0.40 [-0.29, +1.09], unresolved) even though the demotion at $k=8$ is large and resolved (-16.90 [-18.50, -15.30]). On capacity, where the $k=1$ lead *is* resolved (+2.00 [+1.20, +2.80]) and the sign flip is 10 of 10, inversion is the correct word.

**Arm A, by contrast, reorders one family and not the other.** On the leaking-rate family the fastest variant is first at every band in every seed, with fast-minus-mid at $k=8$ of +0.44 [+0.30, +0.58] — though by $k=8$ the middle and slow variants have converged and their intervals overlap, so what is preserved is the top rank, not a resolved three-way ordering. On the oscillator-bank family the top rank passes to the middle variant at $k=2$ and never returns (-0.37 [-0.65, -0.09] at $k=8$, with 1 of 10 seeds still positive). Even there the demotion is not a reversal: fast-minus-slow at $k=8$ is -0.13 [-0.41, +0.15], unresolved. **Arm A can cost the fastest system its top rank; only Arm B sends it to last.**

### *The crossover band is a joint property of band and horizon.*

The delay horizon of the estimator is itself a band parameter, and it is the sharpest available criticism of the design: if the arms' behaviour were an artefact of holding the horizon at 8, the note would collapse. It is not. The horizon was swept from 2 to 32, at two sample budgets, with the confound handled first — the degree-2 basis grows quadratically in the horizon, from 5 terms at $d=2$ to 560 at $d=32$, so a long horizon starves the estimator exactly as a small $n$ does. Cells below two samples per basis term are marked infeasible and excluded from every verdict.

Table 4: Both Verdicts Across the Delay Horizon, $n = 2800$.

| Delay horizon | Basis terms | Arm B inversion | fast - mid at $k=1$ | fast - mid at $k=8$ | Arm A top rank |
|---|---|---|---|---|---|
| 2 | 5 | 10/10 | +1.05 [+1.01, +1.08] | -0.48 [-0.57, -0.40] | preserved |
| 4 | 14 | 10/10 | +2.44 [+2.36, +2.52] | -1.49 [-1.67, -1.30] | preserved |
| 8 | 44 | 10/10 | +5.15 [+4.99, +5.30] | -2.12 [-2.39, -1.86] | preserved |
| 16 | 152 | 10/10 | +6.66 [+6.24, +7.07] | -2.16 [-2.44, -1.87] | preserved |
| 32 | 560 | 10/10 | +5.43 [+4.96, +5.90] | -2.16 [-2.45, -1.88] | preserved |

*Notes*: Leaking-rate family. The $n = 350$ panel agrees at every horizon, including where it is infeasible and its intervals visibly widen (+5.44 [+3.94, +6.93] against +5.43 [+4.96, +5.90] at $d = 32$). Agreement across a budget that changes feasibility is what rules out estimator bias.

![](figures/e2_max_delay.png)

**Figure 3.** Paired per-seed difference between the fastest and middle leaking-rate variant in the drive arm, across five delay horizons at two sample budgets. Crossing zero is the inversion. Every horizon crosses at both budgets in ten of ten seeds, so the distinction between the two arms is not an artefact of the horizon the study fixed. The band at which the crossing occurs moves with the horizon, which is the reporting consequence.

**But the horizon is not inert, and this is the part with a reporting consequence.** At horizons 2 and 4 the ordering holds fast > mid > slow through $k=4$ and flips only at $k=8$. At horizon 8 the flip begins at $k=4$. At horizons 16 and 32 the ordering at $k=8$ deepens from a demotion of the fastest into a complete reversal. The effect size is also non-monotone in the horizon, peaking at 16 — so the study's own choice of 8 was neither the most nor the least favourable available, which is worth stating plainly because it was made before this sweep existed.

**A reported crossover band is therefore a joint property of the observation band and the delay horizon, not of the band alone.** A comparison that reports where an ordering flips must publish its horizon alongside its sample count.

## A Stylized Account, and What It Does Not Claim

### *Why a leaky integrator already predicts this.*

No new model is offered and none is needed. For a leaky-integrator node with state update
$$x_{t} = (1 - \alpha)\,x_{t-1} + \alpha \, f(W x_{t-1} + W_{\mathrm{in}} u_{t}),$$
the leak $\alpha$ sets the timescale over which drive history is retained, which is why the parameter was introduced [@jaeger-2007-leaky-integrator-esn]. **The step size and the leaking rate are not independent parameters, and the source paper says so in its algebra.** Discretising the continuous leaky-integrator equation with step size $\delta$ and time constant $c$ condenses the two into a compound gain $\gamma = \delta/c$, after which the leaking rate enters the update only through the product $a\gamma$; Jaeger et al show that any such network has an exactly equivalent formulation with $\gamma = 1$ and an effective leaking rate $\tilde a = a\gamma$. **A change of band is therefore a rescaling of every variant's effective leaking rate by a common factor.** Because capacity is not monotone in the effective leak but has an interior optimum, a common rescaling moves three variants to three different places on that curve — which is a reordering. Capacity is a sum over independent fading-memory functionals of the drive [@dambre-2012-information-processing-capacity]. Write it as $C(\Delta, d; \alpha)$ for observation interval $\Delta$ and delay horizon $d$: three values of $\alpha$ generate three curves in $\Delta$, and the pairwise crossings of those curves *are* the rank reversals in Table 3. Nothing further is required. A variant whose retention time is short relative to $\Delta$ has little of the drive left to be read; one whose retention time is long relative to $\Delta$ has its capacity limited instead by how much of the drive it can distinguish. The optimum in $\Delta$ therefore moves with $\alpha$, and orderings taken at a single $\Delta$ are orderings of that crossing structure at one point.

### *Why two of the axes cannot see a readout band, and why no mechanism is claimed for the third.*

Under the ensemble protocol used here, kernel and generalisation rank are functions of a single state snapshot per input stream. A readout decimation changes which snapshot is taken, not how many linearly independent snapshots the ensemble contains, so those axes cannot inherit the $\Delta$-dependence that a delay functional has. That is the whole formal content the lead result needs, and it explains the dissociation in Table 2 without a new parameter.

**The qualification in that first clause is load-bearing, because the field has two rank protocols and they do not behave alike here.** In the form used in this note, $S$ distinct input streams each produce one state, taken at the end of the stream, and the stacked states are ranked [@vidamour-2022-nanomagnetic-reservoir-capability]. In the other common form, a single stream is run and the state is recorded at every timepoint [@dale-2019-substrate-independent-framework]; the two coincide only when each stream is one step long [@wringe-2025-reservoir-computing-benchmarks]. **The dissociation reported here is a property of the first form.** Under the second, the readout band changes which columns enter the matrix, so a rank measure is no longer insulated from it by construction, and Table 5 below shows it moving by a large resolved amount, so the result of Table 2 does not carry over. **This is the note's own thesis turning on the note**: which protocol was used is exactly the kind of unreported choice that decides what a band manipulation appears to do.

**A mechanism for the Arm A interaction was proposed, tested, and is retracted.** An earlier account attributed the oscillator family's readout-only demotion to aliasing, on the ordinal coincidence that the variants lose rank in the order they cross the Nyquist limit. A twelve-point sweep in $\omega$ across eight bands does not support it: capacity depends on the decimation factor far more than on samples per period (variance explained .606 against .188), and there is no knee at Nyquist — the loss rises smoothly through regimes where the oscillation is comfortably resolved. **The honest description is a graded, thresholdless timescale mismatch**: the faster the system relative to the readout interval, the more of its trajectory a decimated readout discards, with correlation +.994 between $\log\omega$ and the log decimation loss. It is offered as a description and explicitly not as a mechanism. The same sweep produced an unexpected positive result for the drive arm, where capacity *does* collapse onto the period-per-drive-interval ratio, $R^2 = .921$ on a single variable against .152 for the band alone — so the arm that carries the ranking claim has a measured account, and the arm that does not, does not.

## Discussion

### *What is demonstrated, and at what size.*

**A published ranking is conditional on the observation band and on the delay horizon**, demonstrated here on variants that differ only in time constant. Both conditions move the ordering; one of them moves only part of the behaviour space. **This is a demonstration of an expected effect, not a discovery**, and the note claims no more: the field predicts band conditionality from timescale matching and has done since leaky-integrator units were introduced. The measurement on a common grid, with the horizon crossed against the band and the axes separated, is what did not exist.

Two consequences follow that a reader can act on. The first is that the drive-band question cannot be answered from archived data, because decimating a recording answers a different question and — on one of the two families here — gives the opposite answer about rank. The second is that a comparison of rankings across studies is uninterpretable unless both conditions are reported, which is a comparability problem rather than a physics problem (Yan et al [-@yan-2024-future-of-reservoir-computing]; Liang et al [-@liang-2024-physical-reservoir-emerging-electronics]).

### *A three-item reporting standard.*

The recommendation is short by design, and it is the reason this note exists rather than a repository.

**Report the observation band.** State the drive interval and the readout interval separately, in physical units and in units of the system's own time constant where one can be estimated. They are different manipulations with different consequences, and a single "sampling rate" conflates them.

**Report the delay horizon of the capacity estimator, alongside the sample count.** That the horizon is a *choice* is already known — the field carries competing conventions for where to cut the sum off — a threshold scaled to the reported capacity [@dambre-2012-information-processing-capacity], and a fixed cutoff proportional to the node count, $k_{\max} = 2N$ — both documented as competing in the benchmark review [@wringe-2025-reservoir-computing-benchmarks]. What is added here is that the choice does not merely move a scalar: **it moves a comparative verdict**, because a crossover band is a joint property of the two. Report the basis size the horizon implies and the samples per basis term, so a reader can see whether the estimator was adequately fed; where that ratio is small, say so and exclude the cell rather than reporting it.

**Report which axes the ranking was taken on, and under which protocol.** A ranking on a memory functional and a ranking on a state-rank measure are not interchangeable, and a readout manipulation is invisible to the second by construction — but only under the ensemble form of the rank measures, and the field uses two forms that coincide only in a limiting case [@wringe-2025-reservoir-computing-benchmarks]. Naming the axis is not enough if the protocol behind it is left to the reader. A study reporting only rank measures will find a readout band harmless; a study reporting only capacity will not see that separation was preserved.

None of the three requires new measurement, new instrumentation, or a change of estimator. A benchmarking suite that exposes the band explicitly and pins it to consistent defaults [@pilati-2026-rcbench] already holds every quantity the first two items ask for; what this note asks is that a comparative claim carry them. The practical templates for how such conditions are set and reported in this field are already established [@cucchi-2022-hands-on-reservoir-computing; @jaurigue-2024-external-timescale-tailoring].

### *Limits, stated rather than implied.*

**Simulation only.** Two families of simulated variants carry every claim. The physical system in the study is excluded from all of them: at $n = 350$ it has not saturated — resampling the single recording gives eight disjoint windows spanning 6.081 to 9.533 — so its position in any ordering would be an artefact of estimator starvation rather than a measurement. The correct fix is a comparison across physically distinct systems measured on a common band grid, which this design cannot supply.

**Variants, not substrates.** Everything ordered here differs in one parameter within one architecture family. The interpretive target — a published *substrate* ranking — is broader than what was manipulated, and the inference from one to the other is an argument, not a measurement. It is made explicitly: if changing only a time constant is enough to reorder, a comparison across systems that differ in far more than their time constant cannot be less exposed.

**One estimator, one basis, one slowing scheme.** Maximum degree is fixed at 2 throughout and is a declared unswept choice, carrying a bounded comparability cost against sixth-degree measurements. The drive is slowed by zero-order hold, which is the standard and physical construction but is one choice.

**The delay horizons swept here are short by the field's own conventions, and this cuts against the note.** With 60 nodes, the $k_{\max} = 2N$ convention would set the cutoff at 120; the sweep reported above reaches 32, and the study's own working value is 8. The reason is stated rather than hidden — at degree 2 the basis grows quadratically, so a horizon of 32 already demands 560 terms and a horizon of 120 is not affordable at any sample budget this design can reach. **Both verdicts hold across every horizon that was affordable**, and the crossover's movement is monotone in the horizon across that range, but a reader who works at the longer conventional cutoff is entitled to treat these results as untested there.

**Ten seeds, no multiplicity correction, fixed effects.** The inversion is 10 of 10 with opposite-signed intervals, which is strong for this design, but it is a statement about these six systems and not a population claim about architectures.

**The dissociation is conditional on the rank protocol, and the condition is measured on both families rather than assumed.** Under the single-stream protocol a readout-only band change moves generalisation rank substantially in each family, and on the oscillator-bank family it moves kernel rank as well. The proposition is therefore stated for the ensemble protocol and is false as a general claim about rank measures. The kernel-rank ceiling holds on the leaking-rate family only: it was predicted to generalise, it does not, and the failed prediction is recorded rather than absorbed. **What the two runs do not settle is any third protocol, or any family outside these two**, and nothing in this design bounds that.

**No mechanism is claimed for the readout arm.** The aliasing account was tested and retracted; what replaces it is a description.

**The recommendation has not been tested against practice.** No reception evidence is available, and none is claimed: whether reporting these three items changes what a reader can conclude from a published ranking is an empirical question this note does not answer.

## Reproducibility

### *The companion computation scripts.*

Every numerical value and every figure reported above is reproducible from the published scripts. The study and its extensions run from `band_ordering_study.py`, `e1_second_architecture.py`, `e2_max_delay.py`, `e3_block_resampling.py`, `e4_aliasing_collapse.py`, `e6_charc_axes.py`, `e6b_charc_axes_oscillator.py`, `e7_single_stream_rank.py` and `e7b_single_stream_rank_oscillator.py`, with the three figures rendered by `make_figure.py`, `make_figure_e1.py` and `make_figure_e2.py`, all orchestrated by `reproduce.sh`, at <https://github.com/spectralbranding/band-ordering-experiment> (commit `f05de9c`). Run with `./reproduce.sh`; the scripts carry inline dependency metadata and need no environment setup, no provider key and no network access beyond fetching the one physical recording. Every draw is seeded (seed 20260830) and the outputs are deterministic: the extensions were executed again from an independent working tree and returned byte-identical result files.

### *Data and code availability.*

Code is openly available at <https://github.com/spectralbranding/band-ordering-experiment> under an MIT licence. The derived result tables, run logs and figures are archived as a companion dataset under CC-BY-4.0 at [10.57967/hf/10236](https://doi.org/10.57967/hf/10236), whose contents are exactly what `reproduce.sh` regenerates. This note is archived at [10.5281/zenodo.22206844](https://doi.org/10.5281/zenodo.22206844) (concept DOI, resolving to the latest version); the version of record for this text is [10.5281/zenodo.22206845](https://doi.org/10.5281/zenodo.22206845). The physical recording re-analysed here is a public test file distributed with the benchmarking library used [@pilati-2026-rcbench] and is not redistributed.

## Acknowledgments

AI assistants (Claude Opus 4.6, Claude Opus 5) were used for initial literature search, for software development — implementing and running the companion computation scripts that reproduce the paper's reported numerical and simulation results — and for editorial refinement; all theoretical claims, propositions, and interpretations are the author's sole responsibility.

## CRediT contributions

Conceptualization, methodology, software, formal analysis, investigation, writing — original draft, writing — review and editing, visualization: Dmitry Zharnikov.

## References

::: {#refs}
:::

<!-- GENERATED FILE - do not hand-edit. This glossary is a rendered projection of the corpus ontology graph, regenerated on each release. -->

## Glossary

_Terms used by **2026bq** (Rank Order Under a Capacity Benchmark Is Conditional on the Observation Band and the Delay Horizon). Defined terms this paper introduces, refines, or imports from the corpus ontology._

*Terms introduced by this paper*

- **Architecture-family variant** (write: `architecture-family variant`)
  - One of several systems within a single architecture family differing in exactly one parameter, used as the unit of analysis in place of "substrate" where no materials claim is supported. Naming the unit this way is what keeps a demonstration on parameterised variants from being read as a comparison across materials. NOT a banned-form replacement for "substrate": that word is RESERVED, not retired, and remains correct where the paper names the interpretive target -- what a published SUBSTRATE ranking is conditional on -- and where it names the one physical system the design could not fairly rank. A `replaces:` entry here would flag those required uses and invite a later editor to delete them.
  - first use: Method - The variants, and why they are not called substrates
- **Band conditionality** (write: `band conditionality`)
  - The property that a rank ordering of systems under a capacity benchmark holds only at the observation band and delay horizon at which it was measured. A published ranking that reports neither is a statement whose conditions are unrecoverable, which is a comparability failure rather than a failure of physics.
  - first use: Abstract; Discussion - What is demonstrated
- **Crossover band** (write: `crossover band`)
  - The band at which two systems exchange rank under a capacity benchmark. It is a joint property of the band and the delay horizon of the estimator rather than of the band alone, so a study reporting where an ordering flips must publish its horizon alongside its sample count.
  - first use: Results - The crossover band is a joint property
- **Drive band** (write: `drive band`)
  - The interval at which input is presented to a reservoir. Changing it changes the system's dynamics, and therefore reaches every axis of a behaviour-space characterisation. It cannot be changed after the fact: an archived recording cannot be re-driven.
  - first use: Method - The two arms
- **Observation band** (write: `observation band`)
  - The pair of intervals at which a dynamical system used as a computational reservoir is driven and read: the drive interval at which input is presented, and the readout interval at which state is recorded. Named as a pair because the two are separable manipulations that a single "sampling rate" conflates, and because a comparative claim is conditional on both.
  - first use: Abstract; Method - The two arms
- **Readout band** (write: `readout band`)
  - The interval at which reservoir state is recorded while the drive is left at its native rate. It is the only band manipulation available to a re-analyst of an archived recording, and it is weaker than a drive change: it costs capacity without necessarily changing rank order.
  - first use: Method - The two arms
- **Readout-band dissociation** (write: `readout-band dissociation`)
  - The result that a readout-band change moves memory functionals and leaves state-rank measures untouched, because rank measures under the ensemble protocol take one state per input stream and so cannot inherit the interval dependence of a delay functional. The dissociation is a property of the measure and its protocol rather than of any material, and it does not hold under the alternative protocol in which a single stream is sampled at every timepoint.
  - first use: Results - A readout band destroys memory; A stylized account

# Simulator Scope Audit — What Can We Actually Test?

**Date**: 2026-02-21
**Purpose**: Honest assessment of what the SPH/MHD and PIC modules can and cannot evaluate, categorized by rigor level per CLAUDE.md ground rules.

---

## Module 1: SPH/MHD (`physics/mhd.py`)

### What it actually computes

The SPH module models mercury as ~200 particles with:
- **Pressure forces** — weakly compressible SPH (cubic spline kernel, artificial viscosity)
- **Viscous coupling** — SPH artificial viscosity (α = 0.2)
- **EM-driven circulation** — tangential force proportional to `drive_strength × amplitude × distance_from_axis`
- **Boundary enforcement** — sphere wall and core exclusion with inelastic reflection
- **Global damping** — 0.5%/step velocity decay

### Critical gap: NO electromagnetic induction

The EM drive in `mhd.py` lines 136-159 is a **kinematic force**, not electromagnetic induction:

```
f_em[particle] = drive_strength × |amplitude[axis]| × tangent_direction
```

This is equivalent to "the field pushes mercury tangentially." It contains:
- **No conductivity dependence** — σ_Hg never appears in the force calculation
- **No skin depth** — field penetrates identically at all frequencies
- **No eddy currents** — no induced currents, no induced B-field feedback
- **No magnetic Reynolds number** in the flow — Rm only appears in the dynamo experiment via the `lorentz_scale` multiplier, which is a uniform force amplifier, not real induction physics
- **No frequency dependence** — a 5 Hz drive and a 200 Hz drive produce identical time-averaged forces (the 30% amplitude modulation averages to the same mean)

### What SPH CAN test (reliably)

| Finding | Category | Why it's reliable |
|---------|----------|-------------------|
| **Flow topology** — 3 independent rotation axes produce different vortex patterns than 1 or 2 | **Model prediction** | SPH hydrodynamics is standard; rotation topology is a geometric consequence |
| **3-axis requirement** — removing any axis changes flow structure | **Model prediction** | Follows from force geometry, not EM assumptions |
| **Core centering dynamics** — buoyancy, drag, pinning forces | **Model prediction** (with caveats) | SPH fluid dynamics is standard, but flux pinning model is phenomenological (spring force, not first-principles Meissner) |
| **Dynamo threshold sharpness** — transition at Rm ≈ 10 | **Model prediction** | The `lorentz_scale` amplifier creates a real nonlinear transition in SPH dynamics. The threshold is a property of the SPH model, consistent with known MHD dynamo physics (Rm_crit ≈ 10-50 in real systems) |
| **Material buoyancy sorting** — Pb floats, Fe sinks in Hg | **Verified** | Archimedes' principle, no model needed |

### What SPH CANNOT test

| Claim | Category | Why it fails |
|-------|----------|-------------|
| **RS frequency preference** | **Circular** | Was hardcoded via `rs_resonance_boost`. With boost disabled (Exp 19), frequency sweep is FLAT |
| **Frequency-dependent EM coupling** | **Not modeled** | EM force has no ω-dependence. Real mercury has skin depth δ = √(2/ωμ₀σ) — the field penetration changes with frequency. SPH doesn't model this. |
| **Eddy current torque** | **Not modeled** | Real conducting sphere in oscillating B has torque ∝ ωτ/(1+(ωτ)²) with peak at ω = 1/τ_d. SPH has no induced current physics. |
| **Material-dependent frequency response** | **Not modeled** | Core material doesn't affect EM force calculation. In reality, ferromagnetic/paramagnetic/diamagnetic cores would modify local B-field geometry. |
| **Sub-dynamo induction effects** | **Not modeled** | At Rm < 1 (bench conditions), real mercury still has eddy currents — just not self-sustaining ones. SPH has zero induction at any sub-dynamo scale. |
| **RS amplitude ratio effects on flow** | **Untested** | Never run with RS boost disabled. The amplitude ratios change the kinematic drive proportions, so they DO affect SPH flow — but whether this is physically meaningful requires the missing EM induction physics. |

### SPH model fidelity assessment

**As a fluid dynamics model**: Adequate for qualitative flow patterns. ~200 particles is very coarse — real SPH simulations use 10⁴-10⁶. Resolution limits vortex structure detail. But topology (1-axis vs 3-axis rotation) is captured.

**As an MHD model**: **Fundamentally inadequate**. The "M" in MHD — the magnetic part — is missing. The EM force is a prescribed kinematic drive, not self-consistent magnetohydrodynamics. This means ANY frequency-dependent or conductivity-dependent result is either (a) not captured at all, or (b) injected via the RS boost.

**As a core dynamics model**: Mixed. Buoyancy and drag are standard physics. Flux pinning is phenomenological — the spring constant and coupling rate are tunable parameters, not derived from superconductor physics. The model captures the qualitative story (strong B → core centers) but not the quantitative transition.

---

## Module 2: PIC Plasma (`physics/pic.py`)

### What it actually computes

Boris pusher for Hg⁺ ions with:
- **Lorentz force** — exact Boris algorithm (symplectic in static B, second-order in time-varying B)
- **Helmholtz coil B-field** — from `fields.py`, full elliptic integral solution (exact for ideal coils)
- **Faraday-induced E** — E = -½(∂B/∂t) × r (from ∇×E = -∂B/∂t for spatially uniform time-varying B)
- **Specular wall reflection** — elastic (energy-conserving) at sphere wall and core
- **DC + AC field model** — per-axis independent B_dc, B_ac, ω, φ

### What PIC CAN test (reliably)

| Finding | Category | Why it's reliable |
|---------|----------|-------------------|
| **3D rotation coherence** (Q_3d ≈ 1.0 for 3-axis drive) | **Verified** | Boris pusher is textbook. Single-particle motion in uniform B is exactly solvable. The Q_3d metric correctly measures angular momentum isotropy. |
| **Single-axis collapse** (Q_3d ≈ 0.003) | **Verified** | Same — B along one axis confines motion to the perpendicular plane. |
| **Faraday energy transfer ∝ f^0.87** | **Verified** | E_ind = -½(∂B/∂t)×r is exact for uniform B. Energy input ∝ ωB_ac is analytic. The sub-linear scaling (0.87 vs 1.0) comes from wall reflections redistributing energy — a real geometric effect. |
| **Cyclotron resonance impossible at bench B** | **Verified** (pencil math) | r_c = mv/(qB) = 1.6-7.9 m >> 5-9 cm sphere. Ions hit walls before completing one orbit. No model assumption needed — pure algebra. |
| **No RS frequency peak in single-particle dynamics** | **Verified** | Boris pusher has no hidden RS assumptions. Absorption is monotonic. If there were a single-particle resonance, Boris would find it. |
| **Phase insensitivity** (Q_3d range 0.955-0.963 across 0°-180°) | **Model prediction** | At these B-fields, ions are unmagnetized. Phase coherence requires gyro-orbits, which require r_c << R_sphere. |

### What PIC CANNOT test

| Claim | Category | Why it fails |
|-------|----------|-------------|
| **Collective plasma effects** | **Not modeled** | No particle-particle Coulomb interaction. No space charge. No plasma waves, instabilities, or collective modes. Real plasma at n_e ≈ 10²² has Debye shielding, plasma oscillations, etc. |
| **Self-consistent fields** | **Not modeled** | Particle currents don't modify B. In reality, plasma currents create their own B-field (important when β = nkT/(B²/2μ₀) is not negligible). |
| **Collisions** | **Not modeled** | No ion-neutral or ion-ion collisions. Real Hg plasma has collisional processes that transfer energy between species and thermalize distributions. |
| **Ionization/recombination** | **Not modeled** | Particle count is fixed. Real plasma has ongoing ionization and recombination, especially at boundaries. |
| **Consciousness coupling** | **Not testable** | No model for this exists in any framework. The PIC results show what the physics does; they say nothing about whether consciousness can interface with it. |

### PIC model fidelity assessment

**As a single-particle dynamics model**: **Excellent**. Boris pusher is the gold standard for PIC codes. Energy conservation verified to machine precision in DC fields (Exp boris). The Helmholtz B-field computation uses exact elliptic integrals. Faraday E is the correct induced field for uniform time-varying B.

**As a plasma model**: **Incomplete**. It's a test-particle code, not a self-consistent plasma simulation. Useful for answering "can a single ion do X?" but not "can the plasma collectively do X?" The 2000-particle ensemble gives good statistics for single-particle quantities (KE, angular momentum) but misses all collective effects.

**Physical relevance**: The PIC results tell us about the geometry of particle orbits in the device's field configuration. They confirm that 3-axis driving creates isotropic energy distribution (Q_3d → 1). They disprove cyclotron resonance at bench B-fields. They correctly predict monotonic Faraday absorption. These are honest, useful results.

---

## Module 3: Core Dynamics (`physics/core_dynamics.py`)

### What it computes
- Flux pinning force: spring toward center, ∝ B² × coupling_strength
- Buoyancy: Archimedes (verified physics)
- Stokes drag + added mass
- RS resonance mismatch → coupling rate modifier (the CIRCULAR part)

### Fidelity assessment

**Buoyancy + drag**: Verified physics. Correct forces.

**Flux pinning**: Phenomenological. The spring model captures "strong B → core centers" but the spring constant (k_pin_base = 500 N/m/T²) is a tunable parameter with no first-principles derivation. Real flux pinning in superconductors involves vortex dynamics, not a simple harmonic potential.

**RS resonance boost**: **Circular by construction.** The sigmoid boost explicitly encodes "RS-tuned parameters are better." With `disable_rs_boost=True`, the coupling rate becomes material-independent (up to `rs_coupling_factor`, which also encodes RS predictions about symmetry → coupling).

**Note**: Even with RS boost disabled, `rs_coupling_factor` still affects coupling rate. This factor encodes RS predictions about magnetic symmetry → coupling efficiency. For a fully agnostic test, this should also be neutralized.

---

## Module 4: Fields (`physics/fields.py`)

### Fidelity: VERIFIED

Helmholtz coil B-field from elliptic integrals is **exact analytical physics**. This is textbook electromagnetism — no model assumptions, no RS content. The field gradient computation uses central differences of the exact field (numerically accurate).

The only caveat: real coils have finite wire thickness, imperfect winding, and mutual inductance effects at AC frequencies. The simulator assumes ideal thin-wire coils. This is standard practice and introduces negligible error at the frequencies of interest (< 1 kHz, where coil self-resonance is not a factor).

---

## Module 5: Materials (`physics/materials.py`)

### Fidelity: MIXED

**Conventional properties** (density, conductivity, susceptibility): **Verified** — from standard handbooks.

**RS displacement values**: **Hypothesis inputs** — from Larson's tables. These are the theoretical framework being tested, not independently verified quantities. They can't be validated by the simulator because the simulator uses them as inputs.

**RS-derived quantities** (optimal frequency, amplitude ratio, phase offsets, coupling factor): **Hypotheses** — derived from RS displacement values via formulas that are themselves RS predictions. The simulator using these as parameters means any "validation" of them is circular.

---

## Summary Matrix

| Physics question | SPH answer | PIC answer | Honest status |
|-----------------|-----------|-----------|---------------|
| Does 3-axis driving create 3D rotation? | Yes (qualitative flow topology) | **Yes** (Q_3d = 0.96-1.0) | **VALIDATED** — both models agree, PIC is rigorous |
| Is there a frequency preference? | FLAT (with RS boost off) | Monotonic (∝ f^0.87) | **NO** — neither model shows a resonance |
| Do RS amplitude ratios matter? | Untested (never run without RS boost) | Slightly worse than equal amps (by symmetry) | **UNTESTED** in MHD, marginal in PIC |
| Is cyclotron resonance possible at bench B? | N/A | **No** — r_c >> R_sphere | **DISPROVEN** |
| Is the dynamo threshold real? | Yes (Rm ≈ 10, sharp transition) | N/A | **MODEL PREDICTION** — consistent with textbook MHD |
| Can the core material change frequency response? | Not modeled (no induction physics) | N/A | **CANNOT TEST** |
| Does RS frequency formula work? | **Cannot test** (was circular) | **No peak found** | **UNTESTED** — simulator lacks the physics to evaluate |
| Is cryo-Hg dynamo viable? | Yes (σ×400 → Rm >> 10) | N/A | **MODEL PREDICTION** — real σ values, real Rm threshold |

---

## What Would Be Needed to Test More

### To test frequency dependence honestly:
The SPH model needs **real electromagnetic induction**:
1. Conductivity-dependent eddy current force: F ∝ σ(∂B/∂t), not just a kinematic tangential push
2. Skin depth: field penetration that varies with ω as δ = √(2/ωμ₀σ)
3. Induced B-field feedback (at least linear response, even if not self-consistent dynamo)

This would be a significant rewrite of `mhd.py` — replacing the kinematic EM drive with an induction-based force model. Estimated complexity: medium-high. The payoff: could test whether f_skin ≈ 60 Hz (for 9cm sphere) is a real optimum, and whether core properties modify it.

### To test collective plasma effects:
The PIC model needs **self-consistent field solving**:
1. Poisson solver for space charge → E_self-consistent
2. Current deposition → B_self-consistent
3. Collision operators (at minimum, binary Coulomb collisions)

This would be a full PIC rewrite — essentially building a real plasma simulation code. Estimated complexity: very high. Probably not worth it for this project — commercial/research PIC codes exist (EPOCH, OSIRIS, etc.) and would be more trustworthy.

### To test RS amplitude ratios in MHD:
Minimal effort — just rerun existing experiments with `disable_rs_boost=True` and compare RS ratios vs equal amplitudes. The SPH flow patterns will differ, and we can see if the difference is physically meaningful (e.g., different vortex structures, different angular momentum distributions). **This is the lowest-hanging fruit.**

### What the simulator cannot test at any fidelity level:
- Consciousness-EM coupling (no model exists anywhere)
- Superconducting transition physics (Cooper pairing is quantum — beyond classical simulation)
- Decoupling / reference frame transition (the core RS prediction — no physics framework for this)
- RS displacement values themselves (these are inputs, not outputs)

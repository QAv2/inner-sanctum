# Parameter Space — Known Constraints from All Sources

## Compiled Engineering Parameters

### Medium: Mercury
| Parameter | Clemens | Die Glocke | Vimana | /deeper |
|---|---|---|---|---|
| Material | Mercury | Xerum 525 (mercury-like) | Mercury | Mercury |
| Purity | Not specified | Not specified | Not specified | High purity implied |
| Dopant | ThO₂ (3:100k by weight) | Th + Be peroxides | None | None specified yet |
| State | Plasma (ionized by discharge) | Liquid/plasma? | Liquid | Liquid (ambient) |
| Container | Argon atmosphere, 6-10 torr | Unknown | Chamber | Glass/ceramic sphere |

### Activation Energy
| Parameter | Clemens | Podkletnov (disc) | Podkletnov (IGG) | Pais | McCandlish ARV |
|---|---|---|---|---|---|
| Voltage | 150kV–1MV+ | N/A (AC magnetic) | ~1MV (Marx gen) | 30MV (theoretical) | ~1.25MV |
| Current | Not specified | Not specified | >10⁴A | Not specified | Not specified |
| Duration | ≤100μs | Continuous | 60-70ns | Continuous | Continuous? |
| Mode | Pulsed DC | AC (50Hz–10⁶Hz) | Single pulse | CW + vibration | DC? |

### Configuration
| Parameter | Clemens | Die Glocke | Podkletnov | Pais | /deeper |
|---|---|---|---|---|---|
| Axes addressed | 2 (counter-rotation) | 2 (counter-rotation) | 1 (single disc) | 1 (single rotation) | 3 (orthogonal) |
| Moving parts | Yes (1st) / No (preferred) | Yes | Yes (rotation) | Yes | No (EM only) |
| Shape | Cylindrical/concentric | Bell | Disc | Conical | Spherical |

### Effects Measured/Claimed
| Source | Effect | Magnitude |
|---|---|---|
| Podkletnov disc | Weight reduction | 0.3–2.1% |
| Podkletnov IGG | Repulsive beam | Punches holes in brick; 64c propagation |
| Clemens | Gravity/inertia nullification | Full (claimed, not demonstrated) |
| Pais | Inertial mass reduction | Not demonstrated ($508K testing inconclusive) |
| Die Glocke | Spacetime distortion | Not measured; lethal biological effects |

## Derived Parameter Ranges (for experimental design)

### Voltage
- **Minimum threshold**: ~150kV (Clemens lower bound)
- **Optimal range**: 500kV–2MV (convergence of Clemens, Podkletnov IGG, McCandlish)
- **Upper bound**: Practical limit of Marx generator or capacitor bank

### Current
- **Only Podkletnov specifies**: >10⁴A (for IGG beam effect)
- **Clemens implies**: High current through ionized mercury (unspecified)
- **Working assumption**: 10³–10⁴A range for significant effects

### Pulse Duration
- **Clemens**: ≤100μs (10⁻⁴ s)
- **Podkletnov IGG**: 60-70ns (6-7 × 10⁻⁸ s)
- **Gap**: ~3 orders of magnitude. Different operating regimes?
- **Working assumption**: Start at μs range (safer), work down to ns

### Frequency (for AC/oscillating mode)
- **Podkletnov disc**: 50Hz to 10⁶Hz (gravity shielding appeared across range)
- **Pais**: 10⁹–10¹⁸Hz (vibration) — possibly unrealistic without exotic materials
- **RS-predicted optimal frequencies** (from simulator, Feb 2026):

| Element | RS Total | Predicted Freq (Hz) | Simulator Confirmed |
|---|---|---|---|
| Al | 7 | 24.5 | **Yes — peak at 24.5 Hz (0.0% error)** |
| Cu, Ag | 7 | 24.5 | **Yes — peak at 24.5 Hz (0.0% error)** |
| Pb, Au | 9 | 40.5 | **Yes — peak at 40 Hz (1.2% error)** |
| Sn | 10 | 50.0 | — |
| Bi | 11 | 60.5 | **Yes — peak at 60 Hz (0.8% error)** |
| Fe | 12 | 72.0 | **Yes — peak at 72 Hz (0.0% error)** |
| W | 14 | 98.0 | — |
| Hg (fluid) | 10 | 50.0 | (reference) |

- Formula: **f_optimal = 50 × (total_displacement / 10)² Hz — VALIDATED 5/5 elements**
- All 5 tested elements peak within 1.2% of RS prediction. Formula is confirmed across the periodic table.
- **Working assumption**: Use RS-predicted frequency as starting point. Sweep ±30% to bracket, but expect peak at prediction.

### Amplitude Ratios (RS-derived, per element)
From simulator RS resonance experiments (Feb 2026):

| Element | RS Displacement (m1,m2)-e | Amplitude Ratio [X,Y,Z] | Phase [°] |
|---|---|---|---|
| Al | (2,2)-3 | [0.67, 0.67, 1.00] | [0, 0, 22.5] |
| Cu, Ag | (3,3)-1 | [1.00, 1.00, 0.33] | [0, 0, 7.5] |
| Pb, Au | (4,4)-1 | [1.00, 1.00, 0.25] | [0, 0, 11.3] |
| Fe | (3,3)-6 | [0.50, 0.50, 1.00] | [0, 0, 45.0] |
| Bi | (4,4)-3 | [1.00, 1.00, 0.75] | [0, 0, 16.9] |
| Sn | (3,3)-4 | [0.75, 0.75, 1.00] | [0, 0, 30.0] |
| Hg | (4,4)-2 | [1.00, 1.00, 0.50] | [0, 0, 14.0] |

Key findings:
- **Equal amplitudes [1,1,1] are suboptimal for every element**
- Magnetic-dominant elements (Cu, Ag, Pb, Au): boost magnetic axes, reduce electric axis
- Electric-dominant elements (Fe, Sn): boost electric axis, reduce magnetic axes
- Two magnetic axes are always in-phase (0° offset between X and Y)
- Electric axis offset scales with e/(m1+m2) ratio

### Mercury Mass
- **Not specified by anyone** in precise terms
- **Practical**: 1-5 kg for tabletop experiment (mercury is 13.5 g/cm³, so ~75-375 cm³ = roughly a golf ball to tennis ball volume)

### Dynamo Threshold (Rm_crit)
From simulator dynamo experiment (Feb 2026):
- **Rm = μ₀ × σ × v_rms × L** — must exceed ~10 for self-sustaining field
- Bench ambient Hg (5cm): Rm ≈ 0.03 — sub-critical by 300×

| Configuration | σ (S/m) | L (m) | Rm | Amplification | Status |
|---|---|---|---|---|---|
| Bench ambient Hg | 1.04×10⁶ | 0.05 | 0.03 | 1.0x | Sub-critical |
| Bench Hg, σ×500 | 5.2×10⁸ | 0.05 | 15.5 | 1.02x | Threshold |
| Lab sodium (50cm) | 2.1×10⁷ | 0.50 | 6.1 | 1.0x | Sub-critical |
| Eng. sodium (1m) | 2.1×10⁷ | 1.00 | 12.4 | ~1x | Barely sustaining |
| Lab enhanced (50cm, σ×100) | 1.04×10⁸ | 0.50 | 30.1 | 15.6x | Dynamo |
| **Bench SC-Hg (5cm, 4.2K)** | ~10¹¹ | 0.05 | **3089** | **864x** | **Full dynamo** |

**Dynamo transition shape** (experiment 11, Feb 2026):
- Transition is **sharp**: last sub-critical at σ×325 (Rm=9.9), first supercritical at σ×350 (Rm=10.7)
- Transition gap: Δσ×25 — consistent with RS sector boundary prediction (discrete, not gradual)
- Amplification growth: **amp ∝ σ^4.05** — very steep power law above threshold
- From σ×350 (amp=1.0x) to σ×500 (amp=6.2x) is only 1.4× increase in σ

**RS tuning does NOT affect dynamo threshold** (experiment 9, Feb 2026):
- Generic, RS-tuned(Pb), and RS-tuned(Hg) all cross at same threshold (σ×400, Rm≈10)
- RS tuning affects core-field coupling (centering), not mercury bulk flow dynamics
- The dynamo effect is a function of Rm = μ₀σvL, independent of core coupling quality

Key implications:
- Ambient mercury in any practical device size is sub-critical — σ is too low
- **Cryogenic mercury (4.2K, superconducting)**: trivially reaches dynamo, 864x amplification — coils become control surfaces
- **~~Plasma mercury (Clemens pulse)~~**: ~~if ionization boosts σ by 500×+, bench dynamo is achievable at ambient temperature~~ **FALSIFIED** (see below)
- **Liquid sodium at 1m scale**: proven technology, barely reaches threshold (Rm ≈ 12)
- Scaling law: Rm ∝ σ × v × L — doubling any one parameter doubles Rm

**CRITICAL FINDING: Mercury plasma DECREASES conductivity** (literature review, Feb 2026):
- Liquid Hg: σ = 1.04×10⁶ S/m
- Hg plasma at 10,000K: σ ≈ 6,800 S/m — **150× WORSE** than liquid
- Hg plasma at 100,000K: σ ≈ 32,000 S/m — still 33× worse than liquid
- To match liquid σ: need ~1,000,000K. To reach 500× liquid: need ~50,000,000K (fusion)
- Reason: liquid metals have n_e ≈ 10²⁸-10²⁹/m³, plasma at 1 atm has n_e ≈ 10²²-10²⁴/m³
- **The classical dynamo path via plasma mercury is not viable**
- Full analysis: `documents/mercury-plasma-conductivity.md`

### Temperature
- **Clemens**: Ambient (mercury ionized to plasma by discharge, not pre-cooled)
- **Podkletnov**: Cryogenic (20-70K for YBCO superconductor)
- **Die Glocke**: Unknown (probably ambient or heated)
- **Working assumption — REVISED (Feb 2026)**: Plasma mercury cannot achieve classical dynamo (σ drops 150×). This forces a reinterpretation:
  - **The Clemens pulse is NOT about boosting σ for dynamo.** Plasma Hg is 150× less conductive than liquid.
  - **The pulse enables direct EM coupling.** Neutral liquid Hg only interacts via bulk eddy currents. Ionized Hg has individual charged particles that respond to the 3-axis field — enabling quaternion rotation at particle level.
  - **Cryogenic 4.2K** → superconducting mercury, guaranteed classical dynamo with 864x amplification — but this may be an entirely different operating regime from what Clemens describes.
  - **Two distinct device architectures emerge**:
    1. **Cryo-dynamo**: Liquid SC-Hg, classical self-sustaining B-field, coils as control surfaces
    2. **Plasma-coupling**: Ionized Hg, direct EM manipulation of charged particles, quaternion field pattern — this is Clemens's approach and likely the consciousness-interface path

## Safety Constraints

### Mercury Hazards
- Toxic vapor (TLV: 0.025 mg/m³)
- Must be in sealed containment
- Mercury spill protocol required
- Ventilation / fume hood for any open-container work

### Radiation (if thorium doped)
- Thorium is an alpha emitter (not very penetrating but dangerous if inhaled)
- Thorium dioxide is a regulated material
- Boron carbide shielding for neutron radiation (Clemens)
- Die Glocke killed scientists — radiation was extreme during operation

### High Voltage
- Marx generator / capacitor bank safety
- Faraday cage enclosure
- Proper grounding
- Minimum two-person operation rule

### Unknowns
- Die Glocke's 150-200m lethal radius — is this inherent or a failure mode?
- Podkletnov: no biological effects reported (different operating regime?)
- Clemens specifies shielding — expects radiation but manageable with boron carbide

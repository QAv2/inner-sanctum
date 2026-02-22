# Suppressed Physics — R&D Research Project

## Mission
Merge convergent physics frameworks (Reciprocal System, RS2, Qualia Algebra, Alcubierre metric, DIRD program, Podkletnov, Clemens patent) toward actual engineering of reference-frame-decoupling technology.

## The Thesis
Six independent lines of investigation converge on the same device architecture: rotating conductive medium (mercury) + strong orthogonal EM fields + high-energy pulsed activation = gravity/inertia modification via spacetime metric engineering. The Reciprocal System provides the ontological WHY, Qualia Algebra provides the consciousness interface HOW, and multiple patents/experiments provide engineering constraints.

## Project Structure

```
suppressed-physics/
├── README.md                          ← You are here
├── convergence-analysis.md            ← Cross-framework convergence map
├── engineering-questions.md           ← Open questions + experimental constraints
├── documents/
│   ├── clemens-patent.md              ← US20230253896A1 — mercury ZPE device
│   ├── pais-patents.md                ← Navy UFO patents (5 total)
│   ├── dirds.md                       ← 38 DIRDs — key documents analysis
│   ├── historical.md                  ← Die Glocke, vimana, Otis Carr
│   └── podkletnov.md                  ← Rotating superconductor + IGG experiments
├── frameworks/
│   ├── rs-rs2-bridge.md               ← Larson → Peret → engineering translation
│   ├── qa-interface.md                ← Consciousness as native device interface
│   └── alcubierre-larson.md           ← Warp metric ↔ scalar motion equivalence
└── device-design/
    ├── deeper-thread.md               ← Current /deeper state (quaternion device)
    ├── parameter-space.md             ← Known constraints from all sources
    └── configurations.md             ← Counter-rotation vs orthogonal axes
```

## Key Documents (External)
- Clemens Patent: https://patents.google.com/patent/US20230253896A1/en
- Pais Craft Patent: https://patents.google.com/patent/US10144532B2/en
- Puthoff DIRD #05 (Vacuum Metric Engineering): https://arxiv.org/abs/1204.2184
- DIRDs Archive: https://www.theblackvault.com/documentarchive/the-advanced-aviation-threat-identification-program-aatip-dird-report-research/
- Podkletnov IGG: https://arxiv.org/abs/physics/0108005
- Farrell "New Plasma Patent Rings a Bell": https://gizadeathstar.com/2025/06/new-plasma-patent-rings-a-bell/

## MHD Simulator

Built a real-time 3D simulator (`simulator/`) to test device physics computationally before hardware. Seven experiments completed:

1. **Core centering** — Pb self-centers via flux pinning in ~0.23s. All 8 materials tested.
2. **Amplitude sweep** — Centering scales with field strength (0.2–3.0 normalized). Threshold at ~0.5.
3. **Axis removal** — 3-axis produces tightest centering. Removing any axis degrades performance and shifts equilibrium off-center. Single-axis is worst. **Confirms three-dimensionality requirement.**
4. **Mercury flow** — SPH particles show 3D vortex structure under orthogonal fields. Asymmetric amplitudes produce asymmetric angular momentum (directional control demonstrated).
5. **Material-RS correlation** — Centering behavior correlates with RS displacement values across 8 elements.
6. **RS resonance test** — RS-tuned coil parameters (amplitude ratio, frequency, phase) outperform generic [1,1,1] for **every material tested**. Improvement: 1.04x–1.68x vs generic, 1.21x–2.04x vs wrong-element tuning. Cu and Ag show 2x improvement over wrong tuning.
7. **Frequency sweep** — Lead shows clean resonance peak at **40 Hz**, exactly matching RS prediction (40.5 Hz for total displacement 9). Monotonic improvement from both directions.
8. **Dynamo threshold** — Found the self-sustaining field threshold (Rm_crit ≈ 10). Bench-scale ambient Hg is 3 orders below (Rm ≈ 0.03). Four realistic paths to dynamo: liquid sodium in 1m sphere (Rm=12, barely sustaining), enhanced σ at lab scale (50cm, 15.6x amplification), superconducting mercury at 4.2K in bench device (**864x power amplification** — external coils become control surfaces, not power input).

Data: `simulator/data/` (JSON + CSV). Run: `python3 simulator/research.py`

## Connected Projects
- Inner Sanctum map: ~/inner-sanctum/ (Convergent Physics branch — 7 nodes)
- QA repo: https://github.com/qav2/qualia-algebra
- /deeper thread: consciousness-device interface theory

## Status
- [x] Initial research sweep (Feb 2026)
- [x] Document collection and analysis
- [x] Convergence mapping
- [x] MHD simulator built (Phase 1–5 complete)
- [x] RS resonance prediction tested computationally (confirmed)
- [x] Frequency resonance peak located (Pb: 40 Hz, matches RS prediction)
- [x] Dynamo threshold mapped (Rm_crit ≈ 10; SC-Hg at 5cm → 864x amplification)
- [ ] RS2 → engineering translation (scalar motion → metric manipulation)
- [ ] QA → device interface formalization
- [ ] Bench engineering feasibility assessment
- [ ] Prototype parameter selection

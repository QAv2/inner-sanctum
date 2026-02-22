# RS Frequency Circularity Analysis

**Date**: 2026-02-21
**Finding**: The 5/5 RS frequency match in MHD experiments is CIRCULAR.

## The Problem

The MHD frequency sweep (Experiment 7, 10, 18) shows peak performance at the RS-predicted
frequency for each element. This was presented as "validation" of the RS frequency formula.

**However**, the RS frequency is hardcoded into the force model:

### How RS frequency enters the simulator

1. `materials.py:rs_resonance_mismatch()` computes:
   ```
   freq_mismatch = abs(log2(frequency / rs_optimal_frequency))
   ```
   This is a direct penalty for being away from the RS frequency.

2. `core_dynamics.py:compute_forces()` line 110-113:
   ```
   rs_mismatch = mat.rs_resonance_mismatch(amplitudes, frequency, phases)
   rs_resonance_boost = 0.5 + 1.5 / (1 + exp(3 × (rs_mismatch - 0.3)))
   ```
   This sigmoid gives boost ≈ 2.0 at perfect match, ≈ 0.5 at large mismatch.

3. The boost multiplies:
   - `effective_coupling_rate` (line 119-121) → faster coupling transition
   - `material_factor` in flux pinning (line 153) → stronger centering force

### Consequence

The MHD frequency peak at f_RS is an OUTPUT of the INPUT assumption. The simulator
was TOLD that f_RS is optimal, and it faithfully reports that f_RS is optimal.

The 5/5 element frequency match means: "the code correctly implements the formula
it was given." It does NOT mean: "the physics produces a resonance at f_RS."

### What this does NOT invalidate

- The RS displacement values themselves (from Larson's periodic table)
- The RS amplitude ratio predictions (structural, from displacement symmetry)
- The qualitative prediction that conducting fluids should have frequency-dependent behavior
- The RS framework as a source of hypotheses

### What this DOES invalidate

- Any claim that "the simulator validated the RS frequency formula"
- The 5/5 frequency match as evidence for RS theory
- Experiment 18's "MHD peaks at RS but PIC doesn't" as a meaningful physics result
  (MHD peaks there because we told it to; PIC doesn't because we didn't)

## The Fix

Strip the RS frequency boost from the force model and rerun the frequency sweep.
If a frequency preference STILL emerges from the actual MHD dynamics (Lorentz force,
eddy currents, viscous coupling), that would be a real physics result.

### What could produce a real frequency preference

1. **Skin depth resonance**: δ = √(2/(ωμ₀σ)). When δ ≈ R_sphere, EM field penetrates
   optimally. Below this, field can't penetrate; above, it passes through.
   f_skin = 2/(μ₀σR²) — depends on conductivity and geometry.

2. **Viscous-EM coupling timescale**: τ_EM × τ_visc resonance condition.

3. **Acoustic resonance**: Speed of sound in Hg ≈ 1450 m/s. In a 5cm sphere,
   fundamental = v/(2R) ≈ 14,500 Hz. Way too high.

4. **Nothing**: The SPH dynamics may be frequency-agnostic, and only the hardcoded
   boost creates a preference. This would mean the real device needs a different
   way to determine optimal frequency.

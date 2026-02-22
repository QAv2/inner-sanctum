# MHD Frequency Analysis — What Physical Modes Exist?

**Date**: 2026-02-21
**Context**: RS frequency in simulator is circular (hardcoded). This document asks:
what REAL physical frequencies exist for conducting mercury in a small sphere?

All calculations are textbook EM/MHD — independently verifiable.

---

## 1. Magnetic Diffusion Frequency

The time for magnetic field to diffuse into/through a conductor:

> **τ_d = μ₀ σ R²**
> **f_d = 1 / (2π τ_d) = 1 / (2π μ₀ σ R²)**

This sets the characteristic frequency where eddy currents are maximally effective.
Below f_d: field penetrates fully, weak eddy currents.
Above f_d: field expelled (skin effect), eddy currents only in thin shell.
AT f_d: optimal penetration-to-current ratio.

### For liquid mercury in sphere geometries

| Parameter | Value |
|-----------|-------|
| μ₀ | 1.257 × 10⁻⁶ T·m/A |
| σ_Hg | 1.04 × 10⁶ S/m |
| R = 2.5 cm (5cm sphere) | τ_d = 1.257e-6 × 1.04e6 × (0.025)² = 8.17 × 10⁻⁴ s → f_d = **195 Hz** |
| R = 4.5 cm (9cm sphere) | τ_d = 1.257e-6 × 1.04e6 × (0.045)² = 2.65 × 10⁻³ s → f_d = **60 Hz** |

**INTERESTING**: f_d for 9cm sphere ≈ 60 Hz. This is in the RS range (40-72 Hz for tested elements). But this depends on geometry, not core material.

## 2. Skin Depth Resonance

The EM skin depth (penetration depth):

> **δ = √(2 / (ω μ₀ σ))**

Setting δ = R (field just penetrates to center):

> **f_skin = 1 / (π μ₀ σ R²)**

This is exactly 2× f_d (same physics, different convention).

| R (cm) | f_skin (Hz) |
|--------|-------------|
| 2.5    | 390         |
| 4.5    | 120         |
| 5.0    | 97          |
| 7.5    | 43          |
| 10.0   | 24          |

### Material dependence through conductivity

The RS formula gives different frequencies for different core materials. But f_skin depends
on the FLUID conductivity (mercury), not the core. Unless... the core material modifies the
effective conductivity of the combined system?

Let me check if any combination of core properties and mercury geometry matches f_RS.

## 3. Cross-check: Does f_RS ∝ f_skin for some effective radius?

RS formula: f_RS = 50 × (d/10)²

If f_RS = f_skin = 1/(π μ₀ σ_Hg R_eff²), then:
R_eff = √(1 / (π μ₀ σ_Hg f_RS))

| Element | d | f_RS (Hz) | R_eff (cm) |
|---------|---|-----------|------------|
| Cu      | 7 | 24.5      | 10.2       |
| Al      | 7 | 24.5      | 10.2       |
| Pb      | 9 | 40.5      | 7.9        |
| Hg      | 10| 50.0      | 7.1        |
| Bi      | 11| 60.5      | 6.5        |
| Fe      | 12| 72.0      | 5.9        |

These are all in the range 6-10 cm radius (12-20 cm diameter spheres).
The trend goes the WRONG way for skin depth — higher displacement → higher frequency
→ SMALLER effective radius. But skin depth resonance for a fixed sphere gives one
frequency, not a material-dependent one.

**Conclusion**: Skin depth resonance for mercury gives a single frequency per geometry.
It cannot explain material-dependent f_RS unless the core somehow changes the effective
geometry or conductivity.

## 4. Alfvén Wave Frequency

Alfvén speed: v_A = B / √(μ₀ ρ)

Standing wave in sphere: f_A = v_A / (2R)

For mercury (ρ = 13,534 kg/m³), B = 0.17 mT:

v_A = 1.7e-4 / √(1.257e-6 × 13534) = 1.7e-4 / √(0.01702) = 1.7e-4 / 0.1304 = 1.30e-3 m/s

f_A = 1.30e-3 / (2 × 0.045) = 0.0145 Hz ≈ **0.015 Hz**

This is 3000× too low. Alfvén waves require much stronger B (or lighter fluid) to
reach 40-70 Hz range. At B = 5 T: f_A ≈ 430 Hz. Still not matching.

**Conclusion**: Alfvén waves are irrelevant at these B-fields.

## 5. Acoustic / Pressure Wave Frequency

Speed of sound in mercury: c_s ≈ 1450 m/s

Fundamental mode in sphere: f = c_s / (2R)

| R (cm) | f_acoustic (Hz) |
|--------|-----------------|
| 2.5    | 29,000          |
| 4.5    | 16,111          |

**WAY too high.** Acoustic modes are irrelevant.

## 6. Magnetohydrodynamic Oscillation Modes

For a conducting sphere in an oscillating external B field, the relevant physics is
the **induced eddy current torque**. The time-averaged torque on a conducting sphere
in a rotating B field has a maximum at:

> **ω_peak = 1 / τ_d = 1 / (μ₀ σ R²)**

This is the magnetic diffusion rate (not frequency in Hz — need to divide by 2π for Hz).

For the torque to be maximized, the field rotation rate must match the eddy current
decay rate. Too slow → field penetrates, no eddy currents. Too fast → field shielded,
only surface currents.

This is the same as f_d from section 1, giving 195 Hz (5cm) or 60 Hz (9cm) for mercury.

## 7. Could the Core Material Modify the Effective System?

The core sits in the center. Possibilities:
- Core conductivity adds to mercury conductivity? No — they're separate bodies.
- Core magnetic permeability focuses the B-field? Pb is diamagnetic (χ = -1.8e-5), negligible.
- Core geometry changes effective radius? Core is 8mm in a 45mm sphere — small perturbation.
- Core RS displacement changes... what exactly? This is the RS claim, but no standard physics mechanism.

**For the record**: the RS displacement values are (m1, m2, e) from Larson's tables:
- Cu: (3,3,1) → d=7
- Al: (3,3,1) → d=7
- Pb: (4,4,1) → d=9
- Hg: (4,4,2) → d=10
- Bi: (4,4,3) → d=11
- Fe: (4,4,4) → d=12

These don't map to any obvious conventional physical property (conductivity, density,
magnetic susceptibility, etc.) in a way that would produce the f_RS formula.

## 8. Summary

| Mechanism | Frequency range | Material-dependent? | Matches f_RS? |
|-----------|----------------|--------------------|----|
| Magnetic diffusion | 60-195 Hz (geometry-dependent) | No (mercury property) | Partly (right ballpark for 9cm) |
| Skin depth resonance | 97-390 Hz | No | No |
| Alfvén waves | 0.015 Hz at 0.17 mT | No | No |
| Acoustic modes | 16-29 kHz | No | No |
| Eddy current torque peak | Same as magnetic diffusion | No | Same as above |

**No standard MHD mechanism produces a material-dependent frequency in the 25-72 Hz range.**

The magnetic diffusion frequency is in the right ballpark for a 9cm mercury sphere (~60 Hz),
but it's a single frequency for a given geometry — it can't explain why different core
materials would have different optimal frequencies.

## 9. Implications

The RS frequency formula f = 50 × (d/10)² predicts material-dependent frequencies
that don't correspond to any known MHD resonance. This means either:

1. **The formula encodes physics we don't model** — some coupling between core
   displacement properties and mercury dynamics that isn't in standard MHD
2. **The formula is wrong** — the 5/5 match was circular (hardcoded), and there's
   no physical basis for material-dependent driving frequency
3. **The mechanism isn't frequency at all** — maybe what matters is the amplitude
   ratios and phase relationships (which DO have geometric content), and the
   frequency is incidental

Option 3 is testable: check if amplitude ratios predict anything real in the MHD
when RS boost is removed.

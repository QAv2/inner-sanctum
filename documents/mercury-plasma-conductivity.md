# Mercury Plasma Electrical Conductivity Research

**Date**: 2026-02-21
**Purpose**: Determine whether ionizing mercury to plasma enhances conductivity for MHD dynamo applications

## Executive Summary

**Plasma does NOT increase mercury's electrical conductivity.** Ionizing mercury *decreases* its conductivity by 2-5 orders of magnitude relative to the liquid state. This is a fundamental physics constraint: liquid metals have free electron densities (~10^28-10^29 m^-3) that plasma at any practical temperature cannot match.

The Clemens pulse likely serves a different purpose than conductivity enhancement.

---

## 1. Mercury Properties

| Property | Value |
|----------|-------|
| Atomic mass | 200.59 u |
| First ionization energy | 10.4375 eV |
| Second ionization energy | 18.756 eV |
| Liquid conductivity (293 K) | 1.04 x 10^6 S/m |
| Boiling point | 630 K (357 C) |
| Superconducting Tc | 4.15 K |
| Heat of vaporization | 59.11 kJ/mol |

## 2. Spitzer Conductivity (Fully Ionized Plasma)

The Spitzer formula gives conductivity for fully ionized plasma:

```
eta_parallel = 5.2e-5 * Z * ln(Lambda) / T_eV^(3/2)   [ohm*m]
sigma = 1 / eta_parallel   [S/m]
```

Where T_eV = kB*T / e, Z = charge state, ln(Lambda) = Coulomb logarithm (5-15 for lab plasmas).

### Results (Z=1, singly ionized Hg):

| T (K) | T (eV) | sigma (S/m) | sigma/sigma_liquid |
|--------|---------|-------------|-------------------|
| 5,000 | 0.43 | 1.1 x 10^3 | 0.001x |
| 10,000 | 0.86 | 3.1 x 10^3 | 0.003x |
| 20,000 | 1.72 | 4.4 x 10^3 | 0.004x |
| 50,000 | 4.31 | 1.7 x 10^4 | 0.017x |
| 100,000 | 8.62 | 3.2 x 10^4 | 0.031x |
| 500,000 | 43.1 | 3.6 x 10^5 | 0.35x |
| 1,000,000 | 86.2 | 1.0 x 10^6 | 1.0x |

**Key finding**: You need ~770,000 K (66 eV) just to MATCH liquid mercury's conductivity. To reach 500x liquid, you'd need ~50 million K (4,200 eV) -- thermonuclear temperatures.

## 3. Saha Ionization Fraction

Mercury ionization fraction at 1 atm (from Saha equation):

| T (K) | Ionization fraction | Notes |
|--------|-------------------|-------|
| 3,000 | 4.4 x 10^-8 | Essentially neutral |
| 5,000 | 2.7 x 10^-4 | Trace ionization |
| 7,000 | 1.3 x 10^-2 | ~1% ionized |
| 10,000 | 0.24 | ~24% ionized |
| 12,000 | 0.59 | ~59% ionized |
| 15,000 | 0.92 | ~92% ionized |
| 20,000 | 0.99 | Fully ionized |

Mercury's high ionization energy (10.44 eV vs 13.6 for H, 15.76 for Ar) means it becomes fully ionized at moderate plasma temperatures (~15,000-20,000 K).

## 4. Partially Ionized Mercury Conductivity

Combining Saha ionization with electron-neutral scattering (Rockwood cross section ~30 x 10^-20 m^2):

| T (K) | x_ion | sigma (S/m) | sigma/sigma_liquid |
|--------|-------|-------------|-------------------|
| 5,000 | 2.7e-4 | ~56 | 0.00005x |
| 7,000 | 0.013 | ~1,600 | 0.0015x |
| 10,000 | 0.24 | ~6,800 | 0.0065x |
| 15,000 | 0.92 | ~14,000 | 0.014x |
| 20,000 | 0.99 | ~11,000 | 0.011x |
| 50,000 | 1.00 | ~44,000 | 0.042x |

**No sweet spot exists.** Partially ionized mercury peaks around 15,000 K at ~14,000 S/m -- still 75x LESS conductive than liquid mercury.

## 5. Practical Mercury Arc Discharge Data

### Mercury Arc Rectifiers (historical)
- Arc voltage: 20-30 V (sustaining)
- Current: 10s to 1,000s of amps
- Core temperature: 5,000-8,000 K
- Electron temperature: 1-2 eV (non-equilibrium)
- Electron density: 10^20 - 10^22 m^-3
- Estimated sigma: ~1,000 - 10,000 S/m
- Post-arc conductivity persists ~0.1 s

### High-Pressure Mercury Lamps
- Arc temperature: 5,000-11,000 K
- Pressure: 1-75 atm
- Core sigma: ~1,000 - 5,000 S/m
- Ignition: 50 kV pulse, operates at 100-200 V

### Mercury MHD Patent (US3430081)
- Mercury vapor seeded with ~1% barium
- Operating temperature: ~1,500 K
- Exploits Hg metastable state (3P2, 5.4 eV) near Ba ionization (5.2 eV)
- Collisional ionization enhancement
- No conductivity values reported

### MHD Generator Context
- Seeded thermal plasma: 10-50 S/m at 2,000-3,000 K
- Required temperature for competitive MHD: >1,800 K
- Cesium seeding at 3,000 K: ~80-180 S/m
- Liquid metal MHD: uses intrinsic sigma ~10^6 S/m (no ionization needed)

## 6. Energy Requirements

For 1 liter of liquid mercury (13.5 kg):
- Vaporization energy: ~4 MJ
- Full ionization energy: ~68 MJ (18.9 kWh)
- Total: ~72 MJ for full plasma conversion

Voltage context:
- Per-atom ionization: 10.44 V (electron through potential)
- Arc ignition: ~50 kV pulse needed
- Sustained arc: 20-30 V
- 150 kV - 1 MV range: far exceeds ionization, would produce hot fully-ionized plasma

## 7. The Critical Ratio

**Question**: Can sigma_plasma / sigma_liquid > 500x?

**Answer**: No. Not even close.

```
sigma_liquid_Hg        = 1.04 x 10^6 S/m
sigma_plasma_10kK      = ~7,000 S/m        (0.007x liquid)
sigma_plasma_100kK     = ~30,000 S/m       (0.03x liquid)
sigma_plasma_1MK       = ~1,000,000 S/m    (1x liquid)
sigma_plasma_50MK      = ~5 x 10^8 S/m     (500x liquid -- thermonuclear)
```

The ratio sigma_plasma/sigma_liquid is LESS THAN 1 for all temperatures below ~770,000 K. The 500x enhancement requires ~50 million K.

## 8. Implications for Device Architecture

### Classical MHD Dynamo Perspective
- Magnetic Reynolds number: Rm = mu_0 * sigma * v * L
- Liquid Hg already has excellent sigma (10^6 S/m)
- Plasma REDUCES sigma, making dynamo HARDER
- The bottleneck for liquid Hg dynamo is v*L, not sigma
- Superconducting Hg (4.15 K) would be ideal for Rm but requires cryogenics

### Reinterpretation: The Clemens Pulse Purpose
If ionizing mercury HURTS conductivity (and therefore dynamo action), then the pulse must serve a different function:

1. **EM field coupling**: Neutral liquid Hg responds weakly to external EM fields (only via eddy currents). Ionized Hg responds directly -- individual charged particles follow EM field lines. The three orthogonal generators can directly couple to and rotate the plasma.

2. **Phase transition enablement**: The ionization may be the mechanism for reference frame decoupling -- not a conductivity boost but a state change that enables the quaternion rotation.

3. **Lorentz force enhancement**: In plasma, the J x B force acts on individual particles with much higher drift velocity than bulk liquid flow. Even though sigma is lower, the force coupling per particle is stronger.

4. **Resonance condition**: The RS-predicted frequencies (40 Hz for Pb, analogous for Hg) may require charged particles to achieve resonant coupling. Neutral atoms can't resonate with EM fields at these frequencies.

5. **Dual purpose**: Ionize Hg to plasma (boost EM coupling) + provide activation energy for transition.

### The Key Insight
The device isn't trying to build a better dynamo. It's trying to create a plasma state where three orthogonal EM fields can directly rotate the charge carriers in a quaternion pattern. The conductivity is incidental -- what matters is that the mercury transitions from a diamagnetic liquid to an ionized medium that the generators can grip.

## Sources

- NIST Atomic Data for Mercury: https://physics.nist.gov/PhysRefData/Handbook/Tables/mercurytable1.htm
- Spitzer & Harm, "Transport Phenomena in a Completely Ionized Gas" (1953)
- NRL Plasma Formulary (2018)
- PlasmaPy library documentation
- US Patent 3,430,081 - Mercury vapor for MHD generators
- Estimated electric conductivities of thermal plasma (PMC, 2024)
- Mercury-arc valve Wikipedia
- Expanded mercury conductivity studies (Phys Rev 147, 1966)
- Mercury arc plasma in axial magnetic field (Int J Electronics 49, 1980)

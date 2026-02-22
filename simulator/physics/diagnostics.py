"""PIC plasma diagnostics — energy, FFT, angular momentum, quaternion order parameter.

The quaternion order parameter Q_3d is the central hypothesis test:
  - In viscous liquid (SPH), coupling forces angular momentum onto one axis → Q_3d → 0
  - In collisionless plasma (PIC), each axis sustains independent rotation → Q_3d → 1
  This is what makes the plasma-coupling architecture fundamentally different.
"""

import numpy as np
from physics.materials import HgIon


def kinetic_energy(vel):
    """Total kinetic energy in Joules. vel: (N, 3)."""
    return 0.5 * HgIon.mass * np.sum(vel**2)


def kinetic_energy_per_axis(vel):
    """KE decomposed by axis: [KE_x, KE_y, KE_z] in Joules. vel: (N, 3)."""
    return 0.5 * HgIon.mass * np.sum(vel**2, axis=0)


def kinetic_energy_eV(vel):
    """Total KE in electron-volts (more natural for ion energies)."""
    return kinetic_energy(vel) / 1.602e-19


def kinetic_energy_per_axis_eV(vel):
    """Per-axis KE in eV."""
    return kinetic_energy_per_axis(vel) / 1.602e-19


def angular_momentum(pos, vel):
    """Total angular momentum vector L = m × Σ(r × v). Returns (3,)."""
    L_per_particle = np.cross(pos, vel)  # (N, 3)
    return HgIon.mass * np.sum(L_per_particle, axis=0)


def velocity_fft(vel_history, dt, axis=0):
    """FFT of velocity component over time.

    vel_history: list of (N, 3) velocity snapshots
    dt: time between snapshots
    axis: 0=x, 1=y, 2=z

    Returns (freqs, power) — frequency in Hz, power spectral density.
    """
    # Mean velocity along axis at each timestep
    v_series = np.array([np.mean(v[:, axis]) for v in vel_history])

    # Remove DC component
    v_series -= np.mean(v_series)

    N = len(v_series)
    if N < 4:
        return np.array([0.0]), np.array([0.0])

    # Hanning window to reduce spectral leakage
    window = np.hanning(N)
    v_windowed = v_series * window

    fft_vals = np.fft.rfft(v_windowed)
    power = np.abs(fft_vals)**2 / N
    freqs = np.fft.rfftfreq(N, d=dt)

    return freqs, power


def peak_frequency(vel_history, dt, axis=0):
    """Dominant frequency from FFT of velocity component. Returns Hz."""
    freqs, power = velocity_fft(vel_history, dt, axis)
    if len(freqs) < 2:
        return 0.0
    # Skip DC bin
    idx = np.argmax(power[1:]) + 1
    return float(freqs[idx])


def energy_absorption_rate(ke_history, dt):
    """Mean dKE/dt from time series of KE values. Returns Watts."""
    if len(ke_history) < 2:
        return 0.0
    ke = np.array(ke_history)
    dke_dt = np.gradient(ke, dt)
    return float(np.mean(dke_dt))


def quaternion_order_parameter(pos, vel):
    """The key metric: measures 3D rotation coherence.

    Per-particle angular momentum: L_i = r_i × v_i

    Returns dict with:
      Q_alignment (0–1): how well L vectors align (mean direction magnitude)
        1 = all particles rotating same way, 0 = random
      Q_3d (0–1): entropy-based measure of rotation dimensionality
        0 = single-axis rotation, 1 = equal across all three axes
        This is the CENTRAL HYPOTHESIS TEST.

    Physics:
      In viscous liquid, coupling forces angular momentum onto one dominant
      axis — the system self-organizes into single-axis rotation (Q_3d → 0).
      In collisionless plasma, each axis can sustain independent rotation
      patterns, enabling the quaternion-like 3D rotation (Q_3d → 1).
    """
    L_i = np.cross(pos, vel)  # (N, 3) per-particle angular momentum
    L_mag = np.linalg.norm(L_i, axis=1, keepdims=True)
    L_mag_safe = np.maximum(L_mag, 1e-20)

    # --- Q_alignment: coherence of rotation direction ---
    L_hat = L_i / L_mag_safe  # (N, 3) unit vectors
    mean_dir = np.mean(L_hat, axis=0)  # (3,)
    Q_alignment = float(np.linalg.norm(mean_dir))  # 0 to 1

    # --- Q_3d: dimensionality of rotation ---
    # Project total L onto each axis
    L_total = np.sum(L_i, axis=0)  # (3,)
    L_total_mag = np.linalg.norm(L_total)

    if L_total_mag < 1e-20:
        return {'Q_alignment': 0.0, 'Q_3d': 0.0}

    # Per-axis angular momentum magnitude (absolute, both directions count)
    # Use RMS of per-particle L components to capture rotation in each plane
    L_rms = np.sqrt(np.mean(L_i**2, axis=0))  # (3,) RMS per axis
    L_rms_total = np.sum(L_rms)

    if L_rms_total < 1e-20:
        return {'Q_alignment': Q_alignment, 'Q_3d': 0.0}

    # Normalized fractions per axis
    fracs = L_rms / L_rms_total  # (3,) sums to 1

    # Shannon entropy normalized to [0,1]
    # max entropy = log(3) when all equal, min = 0 when one axis dominates
    entropy = 0.0
    for f in fracs:
        if f > 1e-12:
            entropy -= f * np.log(f)
    Q_3d = float(entropy / np.log(3))  # Normalize: 0 = 1D, 1 = 3D

    return {'Q_alignment': Q_alignment, 'Q_3d': Q_3d}

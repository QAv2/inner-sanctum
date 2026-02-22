"""Simplified MHD using Smoothed Particle Hydrodynamics (SPH).

Mercury is represented as ~200 particles inside the ceramic sphere.
Vectorized with numpy for real-time performance.

Each particle experiences:
  - Pressure forces (keep density uniform)
  - Viscous forces
  - EM induction force (eddy-current J×B from oscillating Helmholtz field)
  - Gravity + buoyancy
  - Boundary forces (sphere wall, core surface)

EM drive model (eddy-current induction):
  Oscillating B field induces E via Faraday's law → J = σE → F = J×B.
  Field penetration attenuated by skin depth δ = √(2/(ωμ₀σ)).
  Force peaks at ω = 1/τ_d where τ_d = μ₀σR² (diffusion time).
"""

import numpy as np
from config import SPHERE_RADIUS, CORE_RADIUS, G, MU_0, B0_REFERENCE
from physics.materials import MERCURY


def sphere_penetration(r, R, delta):
    """Skin-depth attenuation factor for field inside a conducting sphere.

    Solves the diffusion equation ∇²B = μ₀σ ∂B/∂t in spherical coords.
    The penetration profile is:
        P(r, R, δ) = (R/r) × |sinh(κr)| / |sinh(κR)|
    where κ = (1+i)/δ and |sinh((1+i)x)| = √(sinh²(x) + sin²(x)).

    Parameters:
        r: array of radial distances from center (m)
        R: sphere radius (m)
        delta: skin depth (m)

    Returns:
        P: array of penetration factors in [0, 1]
    """
    r = np.asarray(r, dtype=float)
    # Avoid division by zero at r=0: set floor
    r_safe = np.maximum(r, 1e-10)

    # Arguments for |sinh((1+i)x)| = sqrt(sinh²(x) + sin²(x))
    x_r = r_safe / delta
    x_R = R / delta

    # |sinh((1+i)x)| = sqrt(sinh²(x) + sin²(x))
    # For large x, sinh(x) dominates → ~exp(x)/2, so ratio → exp(-(R-r)/δ) × R/r
    # For numerical stability, cap the argument
    x_r_capped = np.minimum(x_r, 50.0)
    x_R_capped = min(x_R, 50.0)

    sinh_r = np.sinh(x_r_capped)
    sin_r = np.sin(x_r_capped)
    mag_r = np.sqrt(sinh_r**2 + sin_r**2)

    sinh_R = np.sinh(x_R_capped)
    sin_R = np.sin(x_R_capped)
    mag_R = np.sqrt(sinh_R**2 + sin_R**2)

    # P = (R/r) × mag_r / mag_R
    P = (R / r_safe) * mag_r / max(mag_R, 1e-30)

    # Clamp to [0, 1] — should be ≤1 for r ≤ R but numerical issues possible
    return np.clip(P, 0.0, 1.0)


class SPHFluid:
    """Vectorized SPH simulation for mercury with induction-driven EM forces."""

    def __init__(self, n_particles: int = 200):
        self.n = n_particles

        # Particle state arrays
        self.pos = np.zeros((n_particles, 3))
        self.vel = np.zeros((n_particles, 3))
        self.density = np.ones(n_particles) * MERCURY.density
        self.pressure = np.zeros(n_particles)

        # SPH parameters
        self.R = SPHERE_RADIUS  # Sphere radius (can be overridden for different geometries)
        R = self.R
        sphere_vol = (4.0/3.0) * np.pi * R**3
        core_vol = (4.0/3.0) * np.pi * CORE_RADIUS**3
        fluid_vol = sphere_vol - core_vol
        total_mass = MERCURY.density * fluid_vol

        self.mass = total_mass / n_particles
        self.h = 0.015       # Smoothing length
        self.h2 = self.h**2
        self.rho0 = MERCURY.density
        self.cs = 3.0        # Artificial speed of sound
        self.visc_alpha = 0.2

        # Induction model parameters
        self.sigma = MERCURY.conductivity   # Electrical conductivity (S/m)
        self.B0 = B0_REFERENCE              # B field at center per axis at unit amp (T)
        self.max_speed = 0.5                # Max particle speed (m/s) — clamp for stability

        # Particle volume (for J×B force → per-particle force)
        self.V_particle = fluid_vol / n_particles

        # Max velocity for viz scaling
        self.max_vel = 0.01

        self._distribute_particles()

    def _distribute_particles(self):
        """Uniform random distribution inside sphere, outside core."""
        R = SPHERE_RADIUS * 0.93
        r_core = CORE_RADIUS * 1.8
        rng = np.random.RandomState(42)

        placed = 0
        while placed < self.n:
            batch = rng.uniform(-R, R, (self.n * 2, 3))
            r = np.linalg.norm(batch, axis=1)
            mask = (r < R) & (r > r_core)
            valid = batch[mask]
            take = min(len(valid), self.n - placed)
            self.pos[placed:placed+take] = valid[:take]
            placed += take

        self.vel = rng.normal(0, 0.002, (self.n, 3))

    def step(self, amplitudes: np.ndarray, core_pos: np.ndarray, dt: float,
             frequency: float = 60.0, phases: np.ndarray = None,
             sim_time: float = 0.0):
        """Advance SPH by one timestep. Fully vectorized.

        Parameters:
            amplitudes: [Ax, Ay, Az] coil amplitude multipliers
            core_pos: core sample position (3,)
            dt: timestep (s)
            frequency: driving frequency (Hz)
            phases: [phi_x, phi_y, phi_z] phase offsets (radians)
            sim_time: current simulation time (s)
        """
        if phases is None:
            phases = np.array([0.0, 2*np.pi/3, 4*np.pi/3])

        n = self.n
        h = self.h
        omega = 2.0 * np.pi * frequency

        # === Pairwise distances (vectorized) ===
        # rij[i,j] = pos[i] - pos[j], shape (n, n, 3)
        diff = self.pos[:, np.newaxis, :] - self.pos[np.newaxis, :, :]  # (n,n,3)
        dist = np.linalg.norm(diff, axis=2)  # (n,n)

        # Mask: within kernel support and not self
        mask = (dist < 2*h) & (dist > 1e-10)  # (n,n)
        q = dist / h  # (n,n)

        # === SPH kernel W(r,h) — cubic spline ===
        norm = 1.0 / (np.pi * h**3)
        W = np.zeros((n, n))
        m1 = mask & (q < 1.0)
        m2 = mask & (q >= 1.0) & (q < 2.0)
        W[m1] = norm * (1.0 - 1.5*q[m1]**2 + 0.75*q[m1]**3)
        t2 = 2.0 - q[m2]
        W[m2] = norm * 0.25 * t2**3

        # === Density ===
        self.density = self.mass * np.sum(W, axis=1)
        self.density = np.maximum(self.density, self.rho0 * 0.3)

        # === Pressure (weakly compressible) ===
        self.pressure = self.cs**2 * (self.density - self.rho0)

        # === Kernel gradient ∇W ===
        # grad_W shape: (n, n, 3)
        gnorm = 1.0 / (np.pi * h**4)
        gfactor = np.zeros((n, n))
        gfactor[m1] = gnorm * (-3.0*q[m1] + 2.25*q[m1]**2)
        gfactor[m2] = -gnorm * 0.75 * (2.0 - q[m2])**2

        # Direction: diff[i,j] / dist[i,j]
        safe_dist = np.where(mask, dist, 1.0)
        direction = diff / safe_dist[:, :, np.newaxis]  # (n,n,3)
        grad_W = gfactor[:, :, np.newaxis] * direction  # (n,n,3)

        # === Pressure force: -m * (P_i/ρ_i² + P_j/ρ_j²) ∇W ===
        rho_sq = np.maximum(self.density**2, 1e-6)
        p_term = self.pressure / rho_sq  # (n,)
        pij = p_term[:, np.newaxis] + p_term[np.newaxis, :]  # (n,n)
        f_pressure = -self.mass * np.sum(pij[:, :, np.newaxis] * grad_W, axis=1)  # (n,3)

        # === Artificial viscosity ===
        dv = self.vel[:, np.newaxis, :] - self.vel[np.newaxis, :, :]  # (n,n,3)
        vr = np.sum(dv * diff, axis=2)  # (n,n) dot product v·r
        approaching = mask & (vr < 0)

        mu = np.zeros((n, n))
        mu[approaching] = h * vr[approaching] / (dist[approaching]**2 + 0.01*h**2)
        rho_avg = 0.5 * (self.density[:, np.newaxis] + self.density[np.newaxis, :])
        safe_rho = np.maximum(rho_avg, 1e-6)
        pi_visc = np.zeros((n, n))
        pi_visc[approaching] = (-self.visc_alpha * self.cs * mu[approaching]) / safe_rho[approaching]
        f_visc = self.mass * np.sum(pi_visc[:, :, np.newaxis] * grad_W, axis=1)  # (n,3)

        # === EM induction force (time-averaged eddy-current torque) ===
        #
        # Physics: oscillating B induces eddy currents in the conducting sphere.
        # The finite diffusion time τ_d = μ₀σR² causes a phase lag between the
        # induced current J and the applied field B. This phase lag produces a
        # non-zero time-averaged torque (same principle as an induction motor).
        #
        # Time-averaged tangential force density at radius r:
        #   f_avg(r) = C × A² × η(ω) × P(r) × r_perp
        #
        # where:
        #   C = σ × B₀² / 2  (material and field constant)
        #   η(ω) = ωτ_d / (1 + (ωτ_d)²)  (induction coupling — peaks at ω = 1/τ_d)
        #   P(r) = skin-depth penetration factor
        #   r_perp = perpendicular distance from the B-field axis
        #
        # η(ω) captures the essential induction motor physics:
        #   - At ω → 0: η → 0 (no ∂B/∂t, no induction)
        #   - At ω → ∞: η → 0 (skin effect blocks field penetration)
        #   - Peak at ω = 1/τ_d: optimal balance of induction and penetration
        #
        # Classification: MODEL PREDICTION (textbook EM, not RS)

        f_em = np.zeros((n, 3))

        if omega > 0.01:  # Skip for DC (no induction at ω=0)
            # Magnetic diffusion time
            tau_d = MU_0 * self.sigma * self.R**2

            # Induction coupling efficiency — the key frequency-dependent factor
            # η(ω) = ωτ_d / (1 + (ωτ_d)²)
            omega_tau = omega * tau_d
            eta = omega_tau / (1.0 + omega_tau**2)

            # Skin depth for this frequency
            delta = np.sqrt(2.0 / (omega * MU_0 * self.sigma))

            # Particle distances from center
            r_particles = np.linalg.norm(self.pos, axis=1)  # (n,)

            # Penetration factor for each particle
            P = sphere_penetration(r_particles, self.R, delta)  # (n,)

            # Force magnitude constant: σ × B₀² / 2
            C = self.sigma * self.B0**2 / 2.0

            for axis in range(3):
                if abs(amplitudes[axis]) < 0.01:
                    continue

                A = abs(amplitudes[axis])

                # Rotation axis unit vector
                ax = np.zeros(3)
                ax[axis] = 1.0

                # Position relative to center
                rel = self.pos  # (n, 3) — relative to sphere center

                # Tangential direction = axis × position (azimuthal)
                tangent = np.cross(ax, rel)  # (n, 3)
                t_mag = np.linalg.norm(tangent, axis=1, keepdims=True)
                t_mag_flat = t_mag.flatten()
                t_mag = np.maximum(t_mag, 1e-10)
                tangent_norm = tangent / t_mag

                # Perpendicular distance from axis (= r × sin(θ))
                r_perp = t_mag_flat  # (n,)

                # Time-averaged force per particle (tangential direction):
                # f = C × A² × η(ω) × P(r) × r_perp × V_particle
                f_mag = C * A**2 * eta * P * r_perp * self.V_particle  # (n,)

                f_em += f_mag[:, np.newaxis] * tangent_norm

        # === Gravity (buoyancy is implicit — SPH density handles it) ===
        f_grav = np.zeros((n, 3))
        f_grav[:, 1] = -G * 0.1  # Reduced gravity effect (fluid is self-supporting)

        # === Total acceleration ===
        accel = f_pressure + f_visc + f_em + f_grav

        # Clamp acceleration for stability
        accel_mag = np.linalg.norm(accel, axis=1, keepdims=True)
        max_accel = 50.0
        clamp = np.minimum(1.0, max_accel / np.maximum(accel_mag, 1e-10))
        accel *= clamp

        # === Integrate (symplectic Euler) ===
        self.vel += accel * dt
        self.pos += self.vel * dt

        # Clamp velocity
        speeds = np.linalg.norm(self.vel, axis=1, keepdims=True)
        clamp_v = np.minimum(1.0, self.max_speed / np.maximum(speeds, 1e-10))
        self.vel *= clamp_v

        # === Boundaries ===
        self._enforce_boundaries(core_pos)

        # === Stats ===
        speeds_flat = np.linalg.norm(self.vel, axis=1)
        self.max_vel = max(float(np.max(speeds_flat)), 0.001)

        # Global damping
        self.vel *= 0.995

    def _enforce_boundaries(self, core_pos: np.ndarray):
        """Vectorized boundary enforcement."""
        R_wall = SPHERE_RADIUS * 0.95
        R_core = CORE_RADIUS * 1.4

        # Sphere wall
        r = np.linalg.norm(self.pos, axis=1)  # (n,)
        outside = r > R_wall
        if np.any(outside):
            normals = self.pos[outside] / r[outside, np.newaxis]
            self.pos[outside] = normals * R_wall
            # Reflect radial velocity component
            v_dot_n = np.sum(self.vel[outside] * normals, axis=1)
            reflect = v_dot_n > 0
            if np.any(reflect):
                idx = np.where(outside)[0][reflect]
                n_ref = normals[reflect]
                vdn = v_dot_n[reflect]
                self.vel[idx] -= 1.5 * vdn[:, np.newaxis] * n_ref

        # Core exclusion
        d = self.pos - core_pos
        dist_core = np.linalg.norm(d, axis=1)
        inside_core = dist_core < R_core
        if np.any(inside_core):
            safe_d = np.maximum(dist_core[inside_core], 1e-10)
            normals = d[inside_core] / safe_d[:, np.newaxis]
            self.pos[inside_core] = core_pos + normals * R_core
            v_dot_n = np.sum(self.vel[inside_core] * normals, axis=1)
            reflect = v_dot_n < 0
            if np.any(reflect):
                idx = np.where(inside_core)[0][reflect]
                n_ref = normals[reflect]
                vdn = v_dot_n[reflect]
                self.vel[idx] -= 1.5 * vdn[:, np.newaxis] * n_ref

    def set_theoretical_mode(self, enabled: bool):
        """Toggle enhanced mode — simulates enhanced conductivity (e.g. superconducting)."""
        if enabled:
            self.sigma = MERCURY.conductivity * 100.0
        else:
            self.sigma = MERCURY.conductivity

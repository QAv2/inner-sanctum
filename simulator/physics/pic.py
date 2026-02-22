"""Particle-In-Cell (PIC) plasma simulation for ionized mercury.

Boris pusher for Hg⁺ ions under DC+AC magnetic fields from three orthogonal
Helmholtz coil pairs. Each axis has independent DC offset, AC amplitude,
frequency, and phase — enabling proper cyclotron resonance studies where a
static B₀ sets ω_c and an AC perturbation at ω = ω_c drives energy in.

The Boris algorithm is exactly symplectic in a static B field (conserves
energy to machine precision). In time-varying fields, it remains stable
as long as ω_c · dt < π/10 (≥20 steps per cyclotron period).
"""

import numpy as np
from config import SPHERE_RADIUS, CORE_RADIUS, PIC_N_PARTICLES, PIC_DT, PIC_THERMAL_SPEED
from physics.materials import HgIon
from physics.fields import total_field_batch


class PICPlasma:
    """PIC simulation of Hg⁺ ions inside the ceramic sphere.

    Mirrors SPHFluid interface pattern but uses single-particle Lorentz
    force (Boris pusher) instead of fluid equations.
    """

    def __init__(self, n_particles=PIC_N_PARTICLES, thermal_speed=PIC_THERMAL_SPEED,
                 use_uniform_field=True, seed=42, sphere_radius=None, core_radius=None):
        self.n = n_particles
        self.thermal_speed = thermal_speed
        self.use_uniform_field = use_uniform_field
        self.sphere_radius = sphere_radius if sphere_radius is not None else SPHERE_RADIUS
        self.core_radius = core_radius if core_radius is not None else CORE_RADIUS

        # Particle state
        self.pos = np.zeros((n_particles, 3))
        self.vel = np.zeros((n_particles, 3))

        # Ion properties
        self.q = HgIon.charge
        self.m = HgIon.mass
        self.qm = HgIon.qm  # q/m ratio

        self._distribute_particles(seed)

    def _distribute_particles(self, seed):
        """Random positions in sphere (outside core), Maxwellian velocities."""
        rng = np.random.RandomState(seed)
        R = self.sphere_radius * 0.93
        r_core = self.core_radius * 1.5

        placed = 0
        while placed < self.n:
            batch = rng.uniform(-R, R, (self.n * 3, 3))
            r = np.linalg.norm(batch, axis=1)
            mask = (r < R) & (r > r_core)
            valid = batch[mask]
            take = min(len(valid), self.n - placed)
            self.pos[placed:placed + take] = valid[:take]
            placed += take

        # Maxwellian velocity distribution (each component is Gaussian)
        self.vel = rng.normal(0, self.thermal_speed / np.sqrt(3), (self.n, 3))

    def _compute_fields(self, B_dc, B_ac, omega, phases, t):
        """Compute instantaneous B and induced E at particle positions.

        Field model per axis:
            B_axis(t) = B_dc[axis] + B_ac[axis] * sin(omega[axis] * t + phases[axis])

        The DC component sets the cyclotron frequency ω_c = qB_dc/m.
        The AC component at ω ≈ ω_c drives resonant energy absorption.

        Faraday's law for a spatially-uniform time-varying B:
            ∇ × E = -∂B/∂t  →  E_induced = -½ (∂B/∂t) × r
        This induced E field is what transfers energy to/from ions.
        Without it, qv×B does no work (always perpendicular to v).

        Returns: (B, E) where B is (3,) or (N,3), E is (N,3)
        """
        # Instantaneous B per axis
        phase_arg = omega * t + phases
        B_inst = B_dc + B_ac * np.sin(phase_arg)  # (3,)

        # ∂B/∂t = B_ac * omega * cos(ωt + φ)
        dBdt = B_ac * omega * np.cos(phase_arg)  # (3,)

        # Induced E = -½ (∂B/∂t) × r  for each particle
        # dBdt is (3,), self.pos is (N,3), cross product broadcasts
        E_induced = -0.5 * np.cross(dBdt, self.pos)  # (N, 3)

        if self.use_uniform_field:
            return B_inst, E_induced  # B: (3,), E: (N,3)
        else:
            B_full = total_field_batch(self.pos, B_inst)  # (N, 3)
            return B_full, E_induced

    def _boris_push(self, B, E, dt):
        """Vectorized Boris algorithm with E and B fields.

        The Boris method is the standard for PIC codes because:
        1. It exactly conserves energy in a static B field (symplectic)
        2. It correctly resolves cyclotron orbits
        3. It's second-order accurate in time

        Algorithm with E field:
            v⁻ = v^n + (q/m) E dt/2          (first half E-kick)
            t = (q/m) B dt/2
            s = 2t / (1 + |t|²)
            v' = v⁻ + v⁻ × t                 (B rotation)
            v⁺ = v⁻ + v' × s
            v^(n+1) = v⁺ + (q/m) E dt/2      (second half E-kick)

        The E half-kicks bracket the B rotation. In pure DC (E=0),
        this reduces to the energy-conserving rotation-only form.

        B: (3,) for uniform field, or (N,3) for per-particle field
        E: (N,3) induced electric field at each particle
        dt: timestep in seconds
        """
        # Half E-kick
        E_half = self.qm * E * (dt / 2.0)  # (N, 3)

        if B.ndim == 1:
            # Uniform B field: broadcast to all particles
            v_minus = self.vel + E_half  # (N, 3) — first half E-kick

            t_vec = self.qm * B * (dt / 2.0)  # (3,)
            t_mag_sq = np.dot(t_vec, t_vec)     # scalar
            s_vec = 2.0 * t_vec / (1.0 + t_mag_sq)  # (3,)

            v_prime = v_minus + np.cross(v_minus, t_vec)  # (N, 3)
            v_plus = v_minus + np.cross(v_prime, s_vec)   # (N, 3)

            self.vel = v_plus + E_half  # second half E-kick
        else:
            # Per-particle B field
            v_minus = self.vel + E_half

            t_vec = self.qm * B * (dt / 2.0)  # (N, 3)
            t_mag_sq = np.sum(t_vec**2, axis=1, keepdims=True)  # (N, 1)
            s_vec = 2.0 * t_vec / (1.0 + t_mag_sq)  # (N, 3)

            v_prime = v_minus + np.cross(v_minus, t_vec)
            v_plus = v_minus + np.cross(v_prime, s_vec)

            self.vel = v_plus + E_half

    def _enforce_boundaries(self, core_pos):
        """Specular (elastic) reflection at sphere wall and core surface.

        Unlike SPH which uses inelastic reflection (energy loss at walls),
        PIC uses perfectly elastic reflection — energy should only change
        from AC driving, not from boundary interactions.
        """
        R_wall = self.sphere_radius * 0.95
        R_core = self.core_radius * 1.5

        # Sphere wall — reflect outward-moving particles
        r = np.linalg.norm(self.pos, axis=1)
        outside = r > R_wall
        if np.any(outside):
            normals = self.pos[outside] / r[outside, np.newaxis]
            self.pos[outside] = normals * R_wall
            v_dot_n = np.sum(self.vel[outside] * normals, axis=1)
            reflect = v_dot_n > 0
            if np.any(reflect):
                idx = np.where(outside)[0][reflect]
                n_ref = normals[reflect]
                vdn = v_dot_n[reflect]
                # Specular: reverse normal component, keep tangential
                self.vel[idx] -= 2.0 * vdn[:, np.newaxis] * n_ref

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
                self.vel[idx] -= 2.0 * vdn[:, np.newaxis] * n_ref

    def step(self, B_dc, B_ac, omega, phases, dt, core_pos, n_substeps=1):
        """Main integration loop.

        B_dc: (3,) DC field per axis (Tesla)
        B_ac: (3,) AC amplitude per axis (Tesla)
        omega: (3,) angular frequency per axis (rad/s)
        phases: (3,) phase offset per axis (radians)
        dt: total timestep (will be divided by n_substeps)
        core_pos: (3,) core position for boundary
        n_substeps: subdivisions for accuracy

        Returns current simulation time offset (for tracking).
        """
        sub_dt = dt / n_substeps
        t_offset = 0.0

        for _ in range(n_substeps):
            # Compute B and induced E at current time
            B, E = self._compute_fields(B_dc, B_ac, omega, phases, self._t + t_offset)
            # Boris velocity update (E half-kicks bracket B rotation)
            self._boris_push(B, E, sub_dt)
            # Position update (leapfrog)
            self.pos += self.vel * sub_dt
            # Boundary enforcement
            self._enforce_boundaries(core_pos)
            t_offset += sub_dt

        self._t += dt

    # Internal time tracker (set by run_pic_simulation)
    _t = 0.0

    def reset_time(self, t=0.0):
        """Reset internal time tracker."""
        self._t = t


def make_field_config(B_dc=(0, 0, 0), B_ac=(0, 0, 0),
                      freq_hz=(50, 50, 50), phases_deg=(0, 0, 0),
                      per_axis_freq=False):
    """Convenience builder for PIC field parameters.

    Converts user-friendly units to internal representation:
    - B in Tesla (typically 0.1–10 mT range → 1e-4 to 1e-2)
    - freq in Hz → omega in rad/s
    - phases in degrees → radians

    per_axis_freq: if True, each axis has its own frequency.
                   if False, all axes share freq_hz[0].

    Returns dict with B_dc, B_ac, omega, phases as numpy arrays.
    """
    B_dc = np.array(B_dc, dtype=float)
    B_ac = np.array(B_ac, dtype=float)
    phases = np.radians(np.array(phases_deg, dtype=float))

    freq = np.array(freq_hz, dtype=float)
    if not per_axis_freq:
        freq[:] = freq[0]
    omega = 2.0 * np.pi * freq

    return {
        'B_dc': B_dc,
        'B_ac': B_ac,
        'omega': omega,
        'phases': phases,
        'freq_hz': freq,
    }

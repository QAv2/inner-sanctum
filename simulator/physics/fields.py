"""Electromagnetic field computation for three orthogonal Helmholtz coil pairs.

Each pair consists of two circular current loops separated by their radius (Helmholtz
condition for maximum uniformity at center). The B field from a single loop is computed
analytically using complete elliptic integrals.

Three pairs oriented along X, Y, Z axes provide full 3D field coverage.
"""

import numpy as np
from scipy.special import ellipk, ellipe
from config import (
    MU_0, COIL_RADIUS, COIL_SEPARATION_RATIO, COIL_TURNS, COIL_CURRENT,
    SPHERE_RADIUS, FIELD_GRID_N
)


def _single_loop_field(pos: np.ndarray, loop_center: np.ndarray,
                       loop_normal: np.ndarray, radius: float,
                       current: float) -> np.ndarray:
    """
    Compute B field at position `pos` from a single circular current loop.

    Uses the exact analytical solution with complete elliptic integrals K(k) and E(k).
    The loop is centered at `loop_center` with axis along `loop_normal`.

    Returns B vector in Tesla.
    """
    # Vector from loop center to point
    r_vec = pos - loop_center

    # Decompose into axial (along normal) and radial components
    axial = np.dot(r_vec, loop_normal)
    radial_vec = r_vec - axial * loop_normal
    rho = np.linalg.norm(radial_vec)

    # Handle on-axis case
    if rho < 1e-12:
        # On-axis formula: B = μ₀IR²/[2(R²+z²)^(3/2)]
        denom = (radius**2 + axial**2)**1.5
        if denom < 1e-20:
            return np.zeros(3)
        B_mag = MU_0 * current * radius**2 / (2.0 * denom)
        return B_mag * loop_normal

    # General off-axis formula using elliptic integrals
    alpha2 = radius**2 + rho**2 + axial**2 - 2.0 * radius * rho
    beta2 = radius**2 + rho**2 + axial**2 + 2.0 * radius * rho
    beta = np.sqrt(max(beta2, 1e-20))

    k2 = 1.0 - alpha2 / beta2
    k2 = np.clip(k2, 0.0, 1.0 - 1e-12)

    K = ellipk(k2)
    E = ellipe(k2)

    # Common factor
    C = MU_0 * current / (2.0 * np.pi)

    # Axial component
    B_axial = (C / beta) * (K + E * (radius**2 - rho**2 - axial**2) / alpha2)

    # Radial component
    B_radial = (C * axial / (rho * beta)) * (-K + E * (radius**2 + rho**2 + axial**2) / alpha2)

    # Convert back to Cartesian
    radial_unit = radial_vec / rho
    return B_axial * loop_normal + B_radial * radial_unit


def helmholtz_pair_field(pos: np.ndarray, axis: int,
                         amplitude: float = 1.0) -> np.ndarray:
    """
    Compute B field from a Helmholtz coil pair along the given axis.

    axis: 0=X, 1=Y, 2=Z
    amplitude: current multiplier (can be time-varying)

    Returns B vector in Tesla.
    """
    normal = np.zeros(3)
    normal[axis] = 1.0

    R = COIL_RADIUS
    d = R * COIL_SEPARATION_RATIO / 2.0  # Half-separation
    I = COIL_CURRENT * COIL_TURNS * amplitude

    center1 = normal * d
    center2 = -normal * d

    B = _single_loop_field(pos, center1, normal, R, I)
    B += _single_loop_field(pos, center2, normal, R, I)

    return B


def total_field(pos: np.ndarray, amplitudes: np.ndarray) -> np.ndarray:
    """
    Compute total B field from all three coil pairs.

    amplitudes: array of [ax, ay, az] current multipliers
    """
    B = np.zeros(3)
    for axis in range(3):
        if abs(amplitudes[axis]) > 1e-10:
            B += helmholtz_pair_field(pos, axis, amplitudes[axis])
    return B


def field_gradient(pos: np.ndarray, amplitudes: np.ndarray,
                   delta: float = 1e-4) -> np.ndarray:
    """
    Compute ∇(B²/2) at position using central differences.

    This is the quantity that appears in the magnetic gradient force:
    F = (χ·V/μ₀) · ∇(B²/2)

    Returns gradient vector.
    """
    grad = np.zeros(3)
    for i in range(3):
        pos_plus = pos.copy()
        pos_minus = pos.copy()
        pos_plus[i] += delta
        pos_minus[i] -= delta

        B_plus = total_field(pos_plus, amplitudes)
        B_minus = total_field(pos_minus, amplitudes)

        B2_plus = np.dot(B_plus, B_plus) / 2.0
        B2_minus = np.dot(B_minus, B_minus) / 2.0

        grad[i] = (B2_plus - B2_minus) / (2.0 * delta)

    return grad


class FieldCache:
    """Pre-computed B field on a 3D grid for fast interpolation."""

    def __init__(self, n: int = FIELD_GRID_N, extent: float = SPHERE_RADIUS * 1.5):
        self.n = n
        self.extent = extent
        self.grid = np.zeros((n, n, n, 3))
        self.spacing = 2.0 * extent / (n - 1)
        self.origin = -extent

    def compute(self, amplitudes: np.ndarray):
        """Recompute the full grid for given coil amplitudes."""
        for ix in range(self.n):
            for iy in range(self.n):
                for iz in range(self.n):
                    pos = np.array([
                        self.origin + ix * self.spacing,
                        self.origin + iy * self.spacing,
                        self.origin + iz * self.spacing,
                    ])
                    self.grid[ix, iy, iz] = total_field(pos, amplitudes)

    def interpolate(self, pos: np.ndarray) -> np.ndarray:
        """Trilinear interpolation of cached B field at arbitrary position."""
        # Convert to grid coordinates
        fx = (pos[0] - self.origin) / self.spacing
        fy = (pos[1] - self.origin) / self.spacing
        fz = (pos[2] - self.origin) / self.spacing

        # Clamp to grid bounds
        fx = np.clip(fx, 0, self.n - 1.001)
        fy = np.clip(fy, 0, self.n - 1.001)
        fz = np.clip(fz, 0, self.n - 1.001)

        ix, iy, iz = int(fx), int(fy), int(fz)
        dx, dy, dz = fx - ix, fy - iy, fz - iz

        # Trilinear interpolation
        c000 = self.grid[ix, iy, iz]
        c100 = self.grid[min(ix+1, self.n-1), iy, iz]
        c010 = self.grid[ix, min(iy+1, self.n-1), iz]
        c001 = self.grid[ix, iy, min(iz+1, self.n-1)]
        c110 = self.grid[min(ix+1, self.n-1), min(iy+1, self.n-1), iz]
        c101 = self.grid[min(ix+1, self.n-1), iy, min(iz+1, self.n-1)]
        c011 = self.grid[ix, min(iy+1, self.n-1), min(iz+1, self.n-1)]
        c111 = self.grid[min(ix+1, self.n-1), min(iy+1, self.n-1), min(iz+1, self.n-1)]

        return (c000 * (1-dx)*(1-dy)*(1-dz) +
                c100 * dx*(1-dy)*(1-dz) +
                c010 * (1-dx)*dy*(1-dz) +
                c001 * (1-dx)*(1-dy)*dz +
                c110 * dx*dy*(1-dz) +
                c101 * dx*(1-dy)*dz +
                c011 * (1-dx)*dy*dz +
                c111 * dx*dy*dz)


def total_field_batch(positions: np.ndarray, amplitudes: np.ndarray) -> np.ndarray:
    """
    Compute total B field from all three coil pairs at N positions.

    Vectorized over the particle dimension — evaluates the same elliptic
    integral math as _single_loop_field but for an (N,3) array of positions.

    positions: (N, 3) array of points in meters
    amplitudes: (3,) array of [ax, ay, az] current multipliers
    Returns: (N, 3) array of B vectors in Tesla
    """
    N = positions.shape[0]
    B_total = np.zeros((N, 3))

    R = COIL_RADIUS
    d = R * COIL_SEPARATION_RATIO / 2.0

    for axis in range(3):
        if abs(amplitudes[axis]) < 1e-10:
            continue

        normal = np.zeros(3)
        normal[axis] = 1.0
        I = COIL_CURRENT * COIL_TURNS * amplitudes[axis]

        for sign in [1.0, -1.0]:
            center = normal * d * sign

            r_vec = positions - center  # (N, 3)
            axial = r_vec @ normal      # (N,)
            radial_vec = r_vec - np.outer(axial, normal)  # (N, 3)
            rho = np.linalg.norm(radial_vec, axis=1)      # (N,)

            # On-axis mask
            on_axis = rho < 1e-12

            # --- Off-axis particles ---
            off = ~on_axis
            if np.any(off):
                rho_off = rho[off]
                axial_off = axial[off]

                alpha2 = R**2 + rho_off**2 + axial_off**2 - 2.0 * R * rho_off
                beta2 = R**2 + rho_off**2 + axial_off**2 + 2.0 * R * rho_off
                beta = np.sqrt(np.maximum(beta2, 1e-20))

                k2 = 1.0 - alpha2 / beta2
                k2 = np.clip(k2, 0.0, 1.0 - 1e-12)

                K = ellipk(k2)
                E = ellipe(k2)

                C = MU_0 * I / (2.0 * np.pi)

                B_ax = (C / beta) * (K + E * (R**2 - rho_off**2 - axial_off**2) / alpha2)
                B_rad = (C * axial_off / (rho_off * beta)) * (-K + E * (R**2 + rho_off**2 + axial_off**2) / alpha2)

                radial_unit = radial_vec[off] / rho_off[:, np.newaxis]
                B_total[off] += B_ax[:, np.newaxis] * normal + B_rad[:, np.newaxis] * radial_unit

            # --- On-axis particles ---
            if np.any(on_axis):
                axial_on = axial[on_axis]
                denom = (R**2 + axial_on**2)**1.5
                denom = np.maximum(denom, 1e-20)
                B_mag = MU_0 * I * R**2 / (2.0 * denom)
                B_total[on_axis] += B_mag[:, np.newaxis] * normal

    return B_total


def generate_field_lines(amplitudes: np.ndarray, n_lines: int = 12,
                         steps: int = 80, ds: float = 0.002) -> list:
    """
    Generate field line curves by integrating through the B field.

    Returns list of arrays, each shape (steps, 3) — the 3D points of each line.
    """
    lines = []
    R = SPHERE_RADIUS * 0.9

    for i in range(n_lines):
        # Start points distributed around the sphere
        theta = 2.0 * np.pi * i / n_lines
        # Alternate between different starting planes
        if i % 3 == 0:
            start = np.array([R * 0.3 * np.cos(theta), R * 0.3 * np.sin(theta), R * 0.4])
        elif i % 3 == 1:
            start = np.array([R * 0.4, R * 0.3 * np.cos(theta), R * 0.3 * np.sin(theta)])
        else:
            start = np.array([R * 0.3 * np.cos(theta), R * 0.4, R * 0.3 * np.sin(theta)])

        points = [start.copy()]
        pos = start.copy()

        for _ in range(steps):
            B = total_field(pos, amplitudes)
            B_mag = np.linalg.norm(B)
            if B_mag < 1e-12:
                break
            pos = pos + ds * B / B_mag
            # Stop if outside sphere
            if np.linalg.norm(pos) > SPHERE_RADIUS * 1.3:
                break
            points.append(pos.copy())

        if len(points) > 2:
            lines.append(np.array(points))

    return lines

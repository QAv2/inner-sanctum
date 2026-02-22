"""3D renderer using pygame — wireframes, particles, field lines.

All 3D geometry is projected to 2D via the Camera, then drawn with
pygame.draw primitives. Z-sorting via painter's algorithm for correct
overlap.
"""

import numpy as np
import pygame
from viz.camera import Camera
from config import (
    SPHERE_RADIUS, COIL_RADIUS, COIL_SEPARATION_RATIO, CORE_RADIUS,
    SPHERE_COLOR, COIL_COLORS, CORE_COLOR, FIELD_LINE_COLOR,
    MERCURY_COLOR, WORLD_SCALE, VIEWPORT_WIDTH, WINDOW_HEIGHT,
)


class Renderer:
    """3D renderer for the device simulation."""

    def __init__(self, surface: pygame.Surface, camera: Camera):
        self.surface = surface
        self.camera = camera

    def draw_wireframe_sphere(self, center: np.ndarray, radius: float,
                               color: tuple, n_rings: int = 8,
                               n_segments: int = 24, alpha: float = 0.5):
        """Draw a wireframe sphere as latitude/longitude lines."""
        # Latitude rings
        for i in range(1, n_rings):
            phi = np.pi * i / n_rings - np.pi / 2
            r_ring = radius * np.cos(phi)
            y = radius * np.sin(phi) + center[1]

            points_2d = []
            for j in range(n_segments + 1):
                theta = 2.0 * np.pi * j / n_segments
                p = np.array([
                    r_ring * np.cos(theta) + center[0],
                    y,
                    r_ring * np.sin(theta) + center[2],
                ])
                proj = self.camera.project(p)
                if proj:
                    points_2d.append((proj[0], proj[1]))

            if len(points_2d) > 1:
                c = tuple(int(v * alpha) for v in color)
                pygame.draw.lines(self.surface, c, False, points_2d, 1)

        # Longitude lines
        for j in range(0, n_segments, 3):
            theta = 2.0 * np.pi * j / n_segments
            points_2d = []
            for i in range(n_rings * 2 + 1):
                phi = np.pi * i / (n_rings * 2) - np.pi / 2
                p = np.array([
                    radius * np.cos(phi) * np.cos(theta) + center[0],
                    radius * np.sin(phi) + center[1],
                    radius * np.cos(phi) * np.sin(theta) + center[2],
                ])
                proj = self.camera.project(p)
                if proj:
                    points_2d.append((proj[0], proj[1]))

            if len(points_2d) > 1:
                c = tuple(int(v * alpha) for v in color)
                pygame.draw.lines(self.surface, c, False, points_2d, 1)

    def draw_coil(self, axis: int, color: tuple, amplitude: float = 1.0,
                  n_segments: int = 32):
        """Draw a Helmholtz coil pair as two circles."""
        R = COIL_RADIUS
        d = R * COIL_SEPARATION_RATIO / 2.0

        # Brightness scales with amplitude
        bright = max(0.2, min(1.0, abs(amplitude)))
        c = tuple(int(v * bright) for v in color)

        for sign in [-1, 1]:
            points_2d = []
            for i in range(n_segments + 1):
                theta = 2.0 * np.pi * i / n_segments
                if axis == 0:  # X-axis coils: rings in YZ plane
                    p = np.array([sign * d, R * np.cos(theta), R * np.sin(theta)])
                elif axis == 1:  # Y-axis coils: rings in XZ plane
                    p = np.array([R * np.cos(theta), sign * d, R * np.sin(theta)])
                else:  # Z-axis coils: rings in XY plane
                    p = np.array([R * np.cos(theta), R * np.sin(theta), sign * d])

                proj = self.camera.project(p)
                if proj:
                    points_2d.append((proj[0], proj[1]))

            if len(points_2d) > 1:
                pygame.draw.lines(self.surface, c, False, points_2d, 2)

    def draw_core(self, pos: np.ndarray, material_color: tuple):
        """Draw the solid core as a filled circle with shading."""
        proj = self.camera.project(pos)
        if not proj:
            return

        sx, sy, depth = proj
        screen_r = self.camera.project_size(CORE_RADIUS, depth)
        screen_r = max(3, screen_r)

        # Main sphere
        pygame.draw.circle(self.surface, material_color, (sx, sy), screen_r)

        # Highlight (simple specular approximation)
        highlight_color = tuple(min(255, v + 60) for v in material_color)
        hr = max(1, screen_r // 3)
        pygame.draw.circle(self.surface, highlight_color,
                          (sx - screen_r // 3, sy - screen_r // 3), hr)

        # Outline
        pygame.draw.circle(self.surface, (255, 255, 255), (sx, sy), screen_r, 1)

    def draw_field_lines(self, lines: list, color: tuple = FIELD_LINE_COLOR):
        """Draw field lines as 3D curves projected to 2D."""
        for line in lines:
            points_2d = []
            for point in line:
                proj = self.camera.project(point)
                if proj:
                    points_2d.append((proj[0], proj[1]))

            if len(points_2d) > 1:
                pygame.draw.lines(self.surface, color, False, points_2d, 1)

    def draw_force_vector(self, origin: np.ndarray, force: np.ndarray,
                          color: tuple, scale: float = 0.005, label: str = ""):
        """Draw a force vector as an arrow from origin."""
        mag = np.linalg.norm(force)
        if mag < 1e-10:
            return

        endpoint = origin + force * scale
        proj_start = self.camera.project(origin)
        proj_end = self.camera.project(endpoint)

        if proj_start and proj_end:
            pygame.draw.line(self.surface, color,
                           (proj_start[0], proj_start[1]),
                           (proj_end[0], proj_end[1]), 2)
            # Arrowhead
            pygame.draw.circle(self.surface, color,
                             (proj_end[0], proj_end[1]), 3)

    def draw_axes_indicator(self, x: int = 60, y: int = None):
        """Draw small XYZ axes in corner for orientation."""
        if y is None:
            y = WINDOW_HEIGHT - 60

        length = 30
        origin = np.zeros(3)
        axes = [
            (np.array([0.01, 0, 0]), COIL_COLORS[0], "X"),
            (np.array([0, 0.01, 0]), COIL_COLORS[1], "Y"),
            (np.array([0, 0, 0.01]), COIL_COLORS[2], "Z"),
        ]

        for axis_vec, color, label in axes:
            proj_o = self.camera.project(origin)
            proj_e = self.camera.project(axis_vec)
            if proj_o and proj_e:
                # Normalize to fixed screen length
                dx = proj_e[0] - proj_o[0]
                dy = proj_e[1] - proj_o[1]
                d = np.sqrt(dx*dx + dy*dy)
                if d > 0.1:
                    dx, dy = dx/d * length, dy/d * length
                    pygame.draw.line(self.surface, color,
                                   (x, y), (int(x + dx), int(y + dy)), 2)
                    # Label
                    font = pygame.font.SysFont("monospace", 12)
                    text = font.render(label, True, color)
                    self.surface.blit(text, (int(x + dx * 1.3) - 4, int(y + dy * 1.3) - 6))

    def draw_mercury_particles(self, positions: np.ndarray, velocities: np.ndarray = None,
                                max_vel: float = 1.0):
        """Draw mercury SPH particles as colored dots."""
        if positions is None or len(positions) == 0:
            return

        # Collect projected points with depth for z-sorting
        projected = []
        for i in range(len(positions)):
            proj = self.camera.project(positions[i])
            if proj:
                vel_mag = 0.0
                if velocities is not None:
                    vel_mag = np.linalg.norm(velocities[i])
                projected.append((proj[0], proj[1], proj[2], vel_mag))

        # Z-sort (far to near)
        projected.sort(key=lambda p: -p[2])

        for sx, sy, depth, vel_mag in projected:
            # Color: blue (slow) → white (fast)
            t = min(1.0, vel_mag / max(max_vel, 0.01))
            r = int(100 + 155 * t)
            g = int(130 + 125 * t)
            b = int(180 + 75 * t)
            color = (r, g, b)

            size = max(2, self.camera.project_size(0.002, depth))
            pygame.draw.circle(self.surface, color, (sx, sy), size)

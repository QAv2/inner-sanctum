"""Orbital camera for 3D viewport.

Mouse drag to orbit, scroll to zoom. Projects 3D world coordinates
to 2D screen coordinates via perspective projection.
"""

import numpy as np
from config import VIEWPORT_WIDTH, WINDOW_HEIGHT, WORLD_SCALE


class Camera:
    """Orbital camera with perspective projection."""

    def __init__(self):
        self.azimuth = 0.3        # Horizontal angle (radians)
        self.elevation = 0.4      # Vertical angle (radians)
        self.distance = 0.25      # Distance from origin (meters)
        self.fov = 60.0           # Field of view (degrees)

        # Viewport center on screen
        self.cx = VIEWPORT_WIDTH // 2
        self.cy = WINDOW_HEIGHT // 2

        # Mouse state
        self._dragging = False
        self._last_mouse = (0, 0)

        self._update_matrices()

    def _update_matrices(self):
        """Recompute view matrix from angles."""
        ca, sa = np.cos(self.azimuth), np.sin(self.azimuth)
        ce, se = np.cos(self.elevation), np.sin(self.elevation)

        # Camera position in world space
        self.eye = self.distance * np.array([
            sa * ce,
            se,
            ca * ce,
        ])

        # View direction
        forward = -self.eye / np.linalg.norm(self.eye)
        world_up = np.array([0.0, 1.0, 0.0])

        self.right = np.cross(forward, world_up)
        rn = np.linalg.norm(self.right)
        if rn < 1e-6:
            self.right = np.array([1.0, 0.0, 0.0])
        else:
            self.right /= rn
        self.up = np.cross(self.right, forward)

        # Perspective scale
        fov_rad = np.radians(self.fov)
        self.persp_scale = WINDOW_HEIGHT / (2.0 * np.tan(fov_rad / 2.0))

    def handle_event(self, event):
        """Process pygame events for camera control."""
        import pygame
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self._dragging = True
                self._last_mouse = event.pos
            elif event.button == 4:  # Scroll up
                self.distance = max(0.05, self.distance * 0.9)
                self._update_matrices()
            elif event.button == 5:  # Scroll down
                self.distance = min(2.0, self.distance * 1.1)
                self._update_matrices()
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self._dragging = False
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            dx = event.pos[0] - self._last_mouse[0]
            dy = event.pos[1] - self._last_mouse[1]
            self.azimuth -= dx * 0.005
            self.elevation = np.clip(self.elevation + dy * 0.005,
                                     -np.pi/2 + 0.1, np.pi/2 - 0.1)
            self._last_mouse = event.pos
            self._update_matrices()

    def project(self, point_3d: np.ndarray) -> tuple:
        """
        Project a 3D world point to 2D screen coordinates.

        Returns (screen_x, screen_y, depth) or None if behind camera.
        """
        # Vector from camera to point
        rel = point_3d - self.eye

        # Camera-space coordinates
        z = -np.dot(rel, self.eye / self.distance)  # Depth (along view axis)
        if z < 0.001:
            return None

        x = np.dot(rel, self.right)
        y = np.dot(rel, self.up)

        # Perspective division
        scale = self.persp_scale / z
        sx = int(self.cx + x * scale)
        sy = int(self.cy - y * scale)  # Screen Y is inverted

        return (sx, sy, z)

    def project_size(self, world_size: float, depth: float) -> int:
        """Project a world-space size to screen pixels at given depth."""
        if depth < 0.001:
            return 1
        return max(1, int(world_size * self.persp_scale / depth))

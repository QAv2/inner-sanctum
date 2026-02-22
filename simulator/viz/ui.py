"""UI panel — right side of the screen with controls and readouts."""

import numpy as np
import pygame
from config import (
    VIEWPORT_WIDTH, PANEL_WIDTH, WINDOW_HEIGHT, PANEL_BG,
    TEXT_COLOR, DIM_TEXT, ACCENT_COLOR, WARN_COLOR, COIL_COLORS,
)


class UIPanel:
    """Right-side panel with simulation controls and readouts."""

    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.x = VIEWPORT_WIDTH
        self.width = PANEL_WIDTH
        self.font = None
        self.font_sm = None
        self.font_lg = None
        self._initialized = False

    def _init_fonts(self):
        if not self._initialized:
            self.font = pygame.font.SysFont("monospace", 14)
            self.font_sm = pygame.font.SysFont("monospace", 11)
            self.font_lg = pygame.font.SysFont("monospace", 18, bold=True)
            self._initialized = True

    def draw(self, state: dict):
        """Draw the full UI panel. `state` is a dict of simulation values."""
        self._init_fonts()

        # Background
        panel_rect = pygame.Rect(self.x, 0, self.width, WINDOW_HEIGHT)
        pygame.draw.rect(self.surface, PANEL_BG, panel_rect)
        pygame.draw.line(self.surface, (40, 45, 60),
                        (self.x, 0), (self.x, WINDOW_HEIGHT), 1)

        y = 15
        y = self._draw_title(y)
        y = self._draw_separator(y)
        y = self._draw_material_info(y, state)
        y = self._draw_separator(y)
        y = self._draw_coil_status(y, state)
        y = self._draw_separator(y)
        y = self._draw_forces(y, state)
        y = self._draw_separator(y)
        y = self._draw_field_info(y, state)
        y = self._draw_separator(y)
        y = self._draw_controls_help(y, state)

    def _text(self, text: str, x: int, y: int, color=TEXT_COLOR, font=None):
        if font is None:
            font = self.font
        surf = font.render(text, True, color)
        self.surface.blit(surf, (x, y))
        return y + font.get_linesize()

    def _draw_title(self, y):
        y = self._text("REFERENCE FRAME ENGINE", self.x + 15, y, ACCENT_COLOR, self.font_lg)
        y = self._text("MHD Simulator v0.1", self.x + 15, y, DIM_TEXT, self.font_sm)
        return y + 5

    def _draw_separator(self, y):
        pygame.draw.line(self.surface, (40, 45, 60),
                        (self.x + 10, y + 5), (self.x + self.width - 10, y + 5), 1)
        return y + 12

    def _draw_material_info(self, y, state):
        mat = state.get("material_name", "?")
        sym = state.get("material_symbol", "?")
        rho = state.get("material_density", 0)
        chi = state.get("material_chi", 0)
        sigma = state.get("material_sigma", 0)
        rs_disp = state.get("rs_displacement", "?")

        y = self._text(f"CORE: {mat} ({sym})", self.x + 15, y, ACCENT_COLOR)
        y = self._text(f"  density:  {rho:.0f} kg/m3", self.x + 15, y, DIM_TEXT, self.font_sm)
        y = self._text(f"  chi:      {chi:.2e}", self.x + 15, y, DIM_TEXT, self.font_sm)
        y = self._text(f"  sigma:    {sigma:.2e} S/m", self.x + 15, y, DIM_TEXT, self.font_sm)
        y = self._text(f"  RS disp:  {rs_disp}", self.x + 15, y, DIM_TEXT, self.font_sm)

        buoyant = state.get("buoyant", False)
        label = "FLOATS in Hg" if buoyant else "SINKS in Hg"
        color = (100, 200, 100) if buoyant else (200, 100, 100)
        y = self._text(f"  {label}", self.x + 15, y, color, self.font_sm)
        return y + 3

    def _draw_coil_status(self, y, state):
        y = self._text("COIL PAIRS", self.x + 15, y, TEXT_COLOR)
        amps = state.get("amplitudes", [0, 0, 0])
        active = state.get("coils_active", [True, True, True])
        labels = ["X", "Y", "Z"]

        for i in range(3):
            status = "ON " if active[i] else "OFF"
            amp_str = f"{amps[i]:+.2f}"
            color = COIL_COLORS[i] if active[i] else DIM_TEXT
            y = self._text(f"  {labels[i]}: {status}  amp={amp_str}", self.x + 15, y, color, self.font_sm)

        mode = state.get("mode", "idle")
        if mode == "pulse":
            y = self._text("  >>> PULSE ACTIVE <<<", self.x + 15, y, WARN_COLOR)

        # Coupling state
        coupling = state.get("coupling_state", "DORMANT")
        strength = state.get("coupling_strength", 0.0)
        coupling_colors = {
            "DORMANT": DIM_TEXT,
            "COUPLING": WARN_COLOR,
            "COUPLED": (80, 255, 120),
            "DECOUPLING": (255, 120, 80),
        }
        c = coupling_colors.get(coupling, DIM_TEXT)
        y = self._text(f"  Core: {coupling} ({strength:.0%})", self.x + 15, y, c, self.font_sm)

        # Draw coupling bar
        bar_x = self.x + 25
        bar_w = self.width - 50
        bar_h = 6
        pygame.draw.rect(self.surface, (30, 35, 45), (bar_x, y, bar_w, bar_h))
        fill_w = int(bar_w * strength)
        if fill_w > 0:
            pygame.draw.rect(self.surface, c, (bar_x, y, fill_w, bar_h))
        y += bar_h + 5

        return y + 3

    def _draw_forces(self, y, state):
        y = self._text("FORCES ON CORE", self.x + 15, y, TEXT_COLOR)

        def fmt_force(name, f, color=DIM_TEXT):
            mag = np.linalg.norm(f) if f is not None else 0
            return self._text(f"  {name:10s} {mag:>10.4f} N", self.x + 15, y, color, self.font_sm)

        y = fmt_force("magnetic", state.get("f_magnetic"))
        y = fmt_force("buoyancy", state.get("f_buoyancy"))
        y = fmt_force("drag", state.get("f_drag"))
        y = fmt_force("TOTAL", state.get("f_total"), TEXT_COLOR)

        pos = state.get("core_pos", np.zeros(3))
        dist = np.linalg.norm(pos)
        y = self._text(f"  core dist from center: {dist*1000:.2f} mm", self.x + 15, y, DIM_TEXT, self.font_sm)
        return y + 3

    def _draw_field_info(self, y, state):
        y = self._text("FIELD", self.x + 15, y, TEXT_COLOR)
        B = state.get("B_at_core", np.zeros(3))
        B_mag = np.linalg.norm(B)
        y = self._text(f"  |B| at core: {B_mag*1000:.3f} mT", self.x + 15, y, DIM_TEXT, self.font_sm)
        y = self._text(f"  Bx={B[0]*1000:.2f}  By={B[1]*1000:.2f}  Bz={B[2]*1000:.2f} mT",
                       self.x + 15, y, DIM_TEXT, self.font_sm)

        B_center = state.get("B_at_center", np.zeros(3))
        B_c_mag = np.linalg.norm(B_center)
        y = self._text(f"  |B| at center: {B_c_mag*1000:.3f} mT", self.x + 15, y, DIM_TEXT, self.font_sm)
        return y + 3

    def _draw_controls_help(self, y, state):
        # Fluid info
        n_particles = state.get("n_particles", 0)
        max_vel = state.get("fluid_max_vel", 0)
        if n_particles > 0:
            y = self._text("MERCURY (SPH)", self.x + 15, y, TEXT_COLOR)
            y = self._text(f"  particles: {n_particles}", self.x + 15, y, DIM_TEXT, self.font_sm)
            y = self._text(f"  max vel:   {max_vel:.4f} m/s", self.x + 15, y, DIM_TEXT, self.font_sm)
            theo = state.get("theoretical_mode", False)
            if theo:
                y = self._text("  [THEORETICAL MODE: 100x sigma]", self.x + 15, y, WARN_COLOR, self.font_sm)
            y = self._draw_separator(y)

        y = self._text("CONTROLS", self.x + 15, y, TEXT_COLOR)
        controls = [
            ("1/2/3", "Toggle X/Y/Z coils"),
            ("+/-", "Adjust amplitude"),
            ("M", "Cycle material"),
            ("P", "Fire pulse"),
            ("F", "Toggle field lines"),
            ("H", "Toggle mercury viz"),
            ("T", "Theoretical mode"),
            ("Space", "Pause / Resume"),
            ("R", "Reset"),
            ("Mouse", "Orbit camera"),
            ("Scroll", "Zoom"),
        ]
        for key, desc in controls:
            y = self._text(f"  {key:8s} {desc}", self.x + 15, y, DIM_TEXT, self.font_sm)

        paused = state.get("paused", False)
        if paused:
            y += 10
            y = self._text("  [ PAUSED ]", self.x + 15, y, WARN_COLOR, self.font_lg)

        sim_time = state.get("sim_time", 0.0)
        fps = state.get("fps", 0)
        y += 5
        y = self._text(f"  t = {sim_time:.3f} s   FPS: {fps:.0f}", self.x + 15, y, DIM_TEXT, self.font_sm)
        return y

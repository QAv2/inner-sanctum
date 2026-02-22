#!/usr/bin/env python3
"""
Reference Frame Engine — MHD Simulator
=======================================
Real-time 3D simulation of the device: ceramic sphere, Pb/Al core,
mercury fluid, three orthogonal Helmholtz coil pairs.

Run: python3 main.py

Controls:
  Mouse drag   — Orbit camera
  Scroll       — Zoom in/out
  1/2/3        — Toggle X/Y/Z coil pairs
  +/- (or =/-)  — Adjust amplitude of all active coils
  [ / ]        — Adjust frequency
  M            — Cycle core material (Pb → Al → Cu → Fe → Bi)
  P            — Fire capacitor pulse
  F            — Toggle field lines
  Space        — Pause / Resume
  R            — Reset simulation
  Escape       — Quit
"""

import sys
import os
import numpy as np

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, BG_COLOR,
    VIEWPORT_WIDTH, SPHERE_RADIUS, COIL_COLORS,
    SPHERE_COLOR, CORE_COLOR, FIELD_LINE_COLOR,
    DT, SUBSTEPS, DEFAULT_AMPLITUDE, DEFAULT_FREQUENCY,
)
from physics.fields import total_field, generate_field_lines
from physics.core_dynamics import CoreState
from physics.mhd import SPHFluid
from physics.materials import CORE_MATERIALS, MERCURY
from viz.renderer import Renderer
from viz.camera import Camera
from viz.ui import UIPanel


class Simulation:
    """Main simulation state and loop."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Reference Frame Engine — MHD Simulator")
        self.clock = pygame.time.Clock()

        # Camera and rendering
        self.camera = Camera()
        self.renderer = Renderer(self.screen, self.camera)
        self.ui = UIPanel(self.screen)

        # Core material (start with Lead)
        self.material_index = 0
        self.core = CoreState(CORE_MATERIALS[self.material_index])

        # Coil state
        self.amplitudes = np.array(DEFAULT_AMPLITUDE, dtype=float)
        self.coils_active = [True, True, True]
        self.frequency = DEFAULT_FREQUENCY
        self.base_amplitude = 1.0

        # Simulation state
        self.sim_time = 0.0
        self.paused = True  # Start paused — coils off
        self.coils_energized = False
        self.show_field_lines = True
        self.field_lines = []

        # Mercury SPH
        self.fluid = SPHFluid(n_particles=120)
        self.show_mercury = True
        self.theoretical_mode = False

        # Pulse mode
        self.pulse_active = False
        self.pulse_start_time = 0.0
        self.pulse_duration = 0.8    # Pulse envelope duration (sim seconds)
        self.pulse_amplitude = 3.0   # Peak amplitude multiplier during pulse

        # SPH runs once per frame (every SUBSTEPS'th physics call)
        self.sph_counter = 0

        # Pre-compute field lines
        self._update_field_lines()

    def _update_field_lines(self):
        """Recompute field lines for current coil state."""
        amps = self._effective_amplitudes()
        if np.any(np.abs(amps) > 0.01):
            self.field_lines = generate_field_lines(amps, n_lines=9, steps=50)
        else:
            self.field_lines = []

    def _effective_amplitudes(self) -> np.ndarray:
        """Get current coil amplitudes accounting for active state and pulse."""
        amps = np.zeros(3)
        for i in range(3):
            if self.coils_active[i] and self.coils_energized:
                amps[i] = self.amplitudes[i]

        # Pulse envelope — sharp rise, sustained plateau, gradual decay
        if self.pulse_active:
            t_pulse = self.sim_time - self.pulse_start_time
            if t_pulse < 0:
                pass
            elif t_pulse < 0.03:
                # Sharp rise (30ms — capacitor discharge)
                envelope = self.pulse_amplitude * (t_pulse / 0.03)
                amps *= max(1.0, envelope)
            elif t_pulse < 0.3:
                # Sustained plateau
                amps *= self.pulse_amplitude
            elif t_pulse < self.pulse_duration:
                # Exponential decay to steady-state
                decay = np.exp(-(t_pulse - 0.3) / 0.2)
                amps *= 1.0 + (self.pulse_amplitude - 1.0) * decay
            else:
                self.pulse_active = False

        return amps

    def handle_events(self):
        """Process all pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                    if not self.paused and not self.coils_energized:
                        self.coils_energized = True
                        self.core.begin_coupling()
                        self._update_field_lines()
                elif event.key == pygame.K_1:
                    self.coils_active[0] = not self.coils_active[0]
                    self._update_field_lines()
                elif event.key == pygame.K_2:
                    self.coils_active[1] = not self.coils_active[1]
                    self._update_field_lines()
                elif event.key == pygame.K_3:
                    self.coils_active[2] = not self.coils_active[2]
                    self._update_field_lines()
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    self.base_amplitude = min(5.0, self.base_amplitude + 0.1)
                    for i in range(3):
                        if self.coils_active[i]:
                            self.amplitudes[i] = self.base_amplitude
                    self._update_field_lines()
                elif event.key == pygame.K_MINUS:
                    self.base_amplitude = max(0.1, self.base_amplitude - 0.1)
                    for i in range(3):
                        if self.coils_active[i]:
                            self.amplitudes[i] = self.base_amplitude
                    self._update_field_lines()
                elif event.key == pygame.K_m:
                    self.material_index = (self.material_index + 1) % len(CORE_MATERIALS)
                    self.core.set_material(CORE_MATERIALS[self.material_index])
                elif event.key == pygame.K_p:
                    # Fire pulse
                    self.pulse_active = True
                    self.pulse_start_time = self.sim_time
                    if not self.coils_energized:
                        self.coils_energized = True
                    self.core.begin_coupling()
                    if self.paused:
                        self.paused = False
                    self._update_field_lines()
                elif event.key == pygame.K_f:
                    self.show_field_lines = not self.show_field_lines
                elif event.key == pygame.K_t:
                    self.theoretical_mode = not self.theoretical_mode
                    self.fluid.set_theoretical_mode(self.theoretical_mode)
                elif event.key == pygame.K_h:
                    self.show_mercury = not self.show_mercury
                elif event.key == pygame.K_r:
                    self._reset()
                elif event.key == pygame.K_LEFTBRACKET:
                    self.frequency = max(1.0, self.frequency * 0.8)
                elif event.key == pygame.K_RIGHTBRACKET:
                    self.frequency = min(10000.0, self.frequency * 1.25)

            # Camera events
            self.camera.handle_event(event)

        return True

    def _reset(self):
        """Reset simulation to initial state."""
        self.core = CoreState(CORE_MATERIALS[self.material_index])
        self.fluid = SPHFluid(n_particles=120)
        self.fluid.set_theoretical_mode(self.theoretical_mode)
        self.sim_time = 0.0
        self.paused = True
        self.coils_energized = False
        self.pulse_active = False
        self.field_lines = []

    def step_physics(self):
        """Advance physics by one frame (multiple substeps)."""
        if self.paused:
            return

        for sub in range(SUBSTEPS):
            amps = self._effective_amplitudes()

            # Time-varying field: modulate with frequency
            t = self.sim_time
            time_mod = np.array([
                np.sin(2 * np.pi * self.frequency * t),
                np.sin(2 * np.pi * self.frequency * t + 2*np.pi/3),
                np.sin(2 * np.pi * self.frequency * t + 4*np.pi/3),
            ])

            # For DC mode (freq=0 or very low), just use static field
            if self.frequency < 0.5:
                effective = amps
            else:
                # AC mode: DC offset + oscillation (field doesn't average to zero)
                effective = amps * (0.7 + 0.3 * time_mod)

            # Core physics every substep
            self.core.step(effective, DT)
            self.sim_time += DT

        # SPH: once per frame with accumulated dt (performance)
        if self.coils_energized:
            sph_dt = DT * SUBSTEPS
            effective = self._effective_amplitudes()
            self.fluid.step(effective, self.core.pos, sph_dt,
                            frequency=self.frequency, sim_time=self.sim_time)

    def render(self):
        """Draw everything."""
        # Clear viewport area
        self.screen.fill(BG_COLOR, (0, 0, VIEWPORT_WIDTH, WINDOW_HEIGHT))

        amps = self._effective_amplitudes()

        # Draw field lines (behind everything)
        if self.show_field_lines and self.coils_energized:
            self.renderer.draw_field_lines(self.field_lines, FIELD_LINE_COLOR)

        # Draw ceramic sphere wireframe
        self.renderer.draw_wireframe_sphere(
            np.zeros(3), SPHERE_RADIUS, SPHERE_COLOR, n_rings=5, n_segments=16
        )

        # Draw coil pairs
        for i in range(3):
            amp = amps[i] if self.coils_energized else 0.0
            self.renderer.draw_coil(i, COIL_COLORS[i], amp)

        # Draw mercury particles (behind core for z-sorting)
        if self.show_mercury and self.coils_energized:
            self.renderer.draw_mercury_particles(
                self.fluid.pos, self.fluid.vel, self.fluid.max_vel
            )

        # Draw core
        mat = CORE_MATERIALS[self.material_index]
        self.renderer.draw_core(self.core.pos, mat.color)

        # Draw force vectors on core (scaled for visibility)
        if self.coils_energized:
            # Scale factor: make forces visible at screen scale
            f_mag = np.linalg.norm(self.core.f_magnetic)
            f_scale = 0.002 / max(f_mag, 0.001) if f_mag > 1e-6 else 0.003
            f_scale = min(f_scale, 0.01)  # Cap scale

            self.renderer.draw_force_vector(
                self.core.pos, self.core.f_magnetic, (255, 200, 50),
                scale=f_scale, label="pin"
            )
            self.renderer.draw_force_vector(
                self.core.pos, self.core.f_buoyancy, (50, 200, 255),
                scale=f_scale, label="buoy"
            )

        # Draw axes indicator
        self.renderer.draw_axes_indicator()

        # Draw UI panel
        mat = CORE_MATERIALS[self.material_index]
        B_center = total_field(np.zeros(3), amps)
        ui_state = {
            "material_name": mat.name,
            "material_symbol": mat.symbol,
            "material_density": mat.density,
            "material_chi": mat.susceptibility,
            "material_sigma": mat.conductivity,
            "rs_displacement": f"({mat.rs_magnetic[0]},{mat.rs_magnetic[1]})-{mat.rs_electric}",
            "buoyant": mat.density < MERCURY.density,
            "amplitudes": [self.amplitudes[i] if self.coils_active[i] else 0.0 for i in range(3)],
            "coils_active": self.coils_active,
            "mode": "pulse" if self.pulse_active else ("running" if self.coils_energized else "idle"),
            "coupling_state": self.core.state_name,
            "coupling_strength": self.core.coupling_strength,
            "f_magnetic": self.core.f_magnetic,
            "f_buoyancy": self.core.f_buoyancy,
            "f_drag": self.core.f_drag,
            "f_total": self.core.f_total,
            "core_pos": self.core.pos,
            "B_at_core": self.core.B_at_core,
            "B_at_center": B_center,
            "paused": self.paused,
            "sim_time": self.sim_time,
            "fps": self.clock.get_fps(),
            "theoretical_mode": self.theoretical_mode,
            "fluid_max_vel": self.fluid.max_vel,
            "n_particles": self.fluid.n,
        }
        self.ui.draw(ui_state)

        pygame.display.flip()

    def run(self):
        """Main loop."""
        running = True
        while running:
            running = self.handle_events()
            self.step_physics()
            self.render()
            self.clock.tick(FPS)

        pygame.quit()


def main():
    print("=" * 60)
    print("  REFERENCE FRAME ENGINE — MHD Simulator")
    print("=" * 60)
    print()
    print("  Press SPACE or P to start the simulation.")
    print("  SPACE = energize coils + begin coupling")
    print("  P     = fire capacitor pulse (sharp onset)")
    print("  M     = cycle core material")
    print("  1/2/3 = toggle X/Y/Z coil pairs")
    print("  +/-   = adjust coil amplitude")
    print("  F     = toggle field lines")
    print("  H     = toggle mercury particles")
    print("  T     = toggle theoretical mode (enhanced Rm)")
    print("  R     = reset")
    print("  ESC   = quit")
    print()

    sim = Simulation()
    sim.run()


if __name__ == "__main__":
    main()

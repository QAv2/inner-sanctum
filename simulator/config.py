"""Global configuration for the Reference Frame Engine simulator."""

import numpy as np

# === Display ===
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
VIEWPORT_WIDTH = 1000  # 3D viewport (left side)
PANEL_WIDTH = 400      # UI panel (right side)
FPS = 30
BG_COLOR = (10, 10, 18)
PANEL_BG = (20, 20, 30)

# === Physics Constants ===
MU_0 = 4 * np.pi * 1e-7       # Vacuum permeability (T·m/A)
G = 9.81                       # Gravitational acceleration (m/s²)

# === Device Geometry (meters) ===
SPHERE_RADIUS = 0.05           # 5 cm ceramic sphere
CORE_RADIUS = 0.008            # 8 mm core sample
COIL_RADIUS = 0.06             # Coil pair radius (slightly larger than sphere)
COIL_SEPARATION_RATIO = 1.0    # Helmholtz: separation = radius

# === Coil Parameters (defaults) ===
COIL_CURRENT = 100.0           # Amps (base current)
COIL_TURNS = 50                # Turns per coil
DEFAULT_FREQUENCY = 60.0       # Hz
DEFAULT_PHASE = [0.0, 0.0, 0.0]  # Phase offset per axis (radians)
DEFAULT_AMPLITUDE = [1.0, 1.0, 1.0]  # Amplitude multiplier per axis

# === Simulation ===
DT = 1.0 / 120                 # Physics timestep (120 Hz internal, render at 60)
SUBSTEPS = 2                   # Physics substeps per frame
FIELD_GRID_N = 15              # Grid resolution for field caching (15³)
FIELD_LINE_COUNT = 12          # Number of field lines to render
FIELD_LINE_STEPS = 80          # Integration steps per field line

# === Pulse Mode ===
PULSE_VOLTAGE = 500e3          # 500 kV default pulse
PULSE_DURATION = 100e-6        # 100 μs
PULSE_RISE_TIME = 10e-6        # 10 μs rise

# === Visualization Scale ===
# Maps physical meters to screen pixels (at default zoom)
WORLD_SCALE = 3000.0           # 1 meter = 3000 pixels (so 5cm sphere = 150px radius)

# === Colors ===
SPHERE_COLOR = (60, 70, 90)
COIL_COLORS = [
    (220, 60, 60),    # X-axis: red
    (60, 220, 60),    # Y-axis: green
    (60, 100, 220),   # Z-axis: blue
]
CORE_COLOR = (180, 180, 200)
FIELD_LINE_COLOR = (40, 80, 120)
MERCURY_COLOR = (180, 195, 210)
TEXT_COLOR = (200, 210, 220)
DIM_TEXT = (100, 110, 120)
ACCENT_COLOR = (80, 160, 255)
WARN_COLOR = (255, 180, 60)

# === Helmholtz B₀ Reference ===
# B field at sphere center from one Helmholtz pair at unit amplitude
# Formula: B₀ = (8 μ₀ N I) / (5√5 R)
B0_REFERENCE = (8 * MU_0 * COIL_TURNS * COIL_CURRENT) / (5 * np.sqrt(5) * COIL_RADIUS)

# === PIC Plasma Constants ===
HG_ION_MASS = 200.59 * 1.6605e-27   # Hg⁺ mass in kg (200.59 amu)
HG_ION_CHARGE = 1.602e-19            # Single ionization (Coulombs)
HG_CYCLOTRON_COEFF = HG_ION_CHARGE / HG_ION_MASS  # q/m ≈ 4.81e5 rad/s/T
PIC_N_PARTICLES = 2000
PIC_DT = 0.0002                      # 0.2 ms — ~100 steps per cyclotron period at 50 Hz
PIC_THERMAL_SPEED = 500.0            # m/s — typical Hg⁺ thermal speed in low-T plasma

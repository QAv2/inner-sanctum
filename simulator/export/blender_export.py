"""
Blender Export — Bench-Scale Reference Frame Engine Prototype
(v2: Realistic procedural materials via Cycles node trees)

Generates a 3D model of the device with all verified dimensions from
prototype-spec.md and simulator config.py. Run headless:

    ~/blender/blender --background --python simulator/export/blender_export.py

Output: device-design/prototype-model.blend  (editable Blender file)
        device-design/prototype-render.png   (preview render)
"""

import bpy
import math
import os
import sys

# ---------------------------------------------------------------------------
# PARAMETERS — all from prototype-spec.md (VERIFIED or design choice)
# ---------------------------------------------------------------------------

# Device geometry (meters)
SPHERE_RADIUS = 0.05          # 5 cm ceramic sphere
SPHERE_WALL = 0.003           # 3 mm wall thickness (ceramic)
CORE_RADIUS = 0.008           # 8 mm Pb core
CORE_EQUILIBRIUM_Y = -0.0105  # 10.5 mm below center (VERIFIED, clean rerun exp 1)

# Coil geometry — Helmholtz pairs (wire-bundle toroids), nested at decreasing radii
COIL_Z_RADIUS = 0.225         # 22.5 cm — outermost pair
COIL_Y_RADIUS = 0.18          # 18 cm — middle pair
COIL_X_RADIUS = 0.14          # 14 cm — innermost pair
WIRE_BUNDLE_RADIUS = 0.01     # 1 cm wire bundle cross-section radius

# Mercury fills interior (sphere minus core)
MERCURY_RADIUS = SPHERE_RADIUS - SPHERE_WALL  # Inner cavity

# Energy glow sphere (between mercury and core)
GLOW_RADIUS = 0.025           # 2.5 cm — centered at origin

SCALE = 1.0

# Axis-identifying tint colors (for coil enamel differentiation)
TINT_X = (0.86, 0.23, 0.23)  # Red
TINT_Y = (0.23, 0.86, 0.23)  # Green
TINT_Z = (0.23, 0.39, 0.86)  # Blue


# ---------------------------------------------------------------------------
# UTILITY FUNCTIONS
# ---------------------------------------------------------------------------

def clear_scene():
    """Remove all default objects."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


def move_to_collection(obj, target_col):
    """Move object from all current collections into target_col."""
    for col in obj.users_collection:
        col.objects.unlink(obj)
    target_col.objects.link(obj)


def new_node_tree(name):
    """Create a new material with clean node tree."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    return mat, nodes, links


# ---------------------------------------------------------------------------
# MATERIALS — Procedural node-based (Cycles-optimized, Blender 4.x API)
# ---------------------------------------------------------------------------

def create_mercury_material():
    """Liquid mercury — mirror-like liquid metal with subtle surface ripples.

    Metallic=1.0, very low roughness (0.02–0.05), dual noise bump for liquid
    surface tension, noise-driven roughness variation for subtle imperfection.
    """
    mat, nodes, links = new_node_tree("Mercury")

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (800, 0)

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (400, 0)
    bsdf.inputs['Base Color'].default_value = (0.85, 0.85, 0.88, 1.0)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.03
    bsdf.inputs['IOR'].default_value = 1.6
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    # Fine liquid ripples (surface tension scale)
    noise_fine = nodes.new('ShaderNodeTexNoise')
    noise_fine.location = (-400, 0)
    noise_fine.inputs['Scale'].default_value = 25.0
    noise_fine.inputs['Detail'].default_value = 8.0
    noise_fine.inputs['Roughness'].default_value = 0.6
    noise_fine.inputs['Distortion'].default_value = 1.5

    # Larger undulations (gravity/vibration scale)
    noise_large = nodes.new('ShaderNodeTexNoise')
    noise_large.location = (-400, -250)
    noise_large.inputs['Scale'].default_value = 5.0
    noise_large.inputs['Detail'].default_value = 4.0
    noise_large.inputs['Roughness'].default_value = 0.5
    noise_large.inputs['Distortion'].default_value = 2.0

    # Weighted sum: 70% fine + 30% large
    scale_large = nodes.new('ShaderNodeMath')
    scale_large.location = (-150, -250)
    scale_large.operation = 'MULTIPLY'
    scale_large.inputs[1].default_value = 0.3
    links.new(noise_large.outputs['Fac'], scale_large.inputs[0])

    add_noises = nodes.new('ShaderNodeMath')
    add_noises.location = (-10, -100)
    add_noises.operation = 'ADD'
    links.new(noise_fine.outputs['Fac'], add_noises.inputs[0])
    links.new(scale_large.outputs['Value'], add_noises.inputs[1])

    # Bump — very subtle, mercury is smooth but alive
    bump = nodes.new('ShaderNodeBump')
    bump.location = (200, -200)
    bump.inputs['Strength'].default_value = 0.08
    bump.inputs['Distance'].default_value = 0.02
    links.new(add_noises.outputs['Value'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    # Roughness micro-variation (0.02–0.05 range)
    ramp_rough = nodes.new('ShaderNodeValToRGB')
    ramp_rough.location = (-100, 200)
    ramp_rough.color_ramp.elements[0].position = 0.45
    ramp_rough.color_ramp.elements[0].color = (0.02, 0.02, 0.02, 1.0)
    ramp_rough.color_ramp.elements[1].position = 0.55
    ramp_rough.color_ramp.elements[1].color = (0.05, 0.05, 0.05, 1.0)
    links.new(noise_fine.outputs['Fac'], ramp_rough.inputs['Fac'])
    links.new(ramp_rough.outputs['Color'], bsdf.inputs['Roughness'])

    return mat


def create_acrylic_material():
    """Semi-transparent acrylic sphere — glass-like with refraction and coat.

    Full transmission, IOR=1.49 (PMMA), clear coat for polished surface gloss,
    Voronoi-driven micro-imperfections for realism.
    """
    mat, nodes, links = new_node_tree("Acrylic_Shell")
    mat.surface_render_method = 'BLENDED'

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (800, 0)

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (400, 0)
    bsdf.inputs['Base Color'].default_value = (0.95, 0.97, 1.0, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.02
    bsdf.inputs['IOR'].default_value = 1.49
    bsdf.inputs['Transmission Weight'].default_value = 1.0
    bsdf.inputs['Alpha'].default_value = 1.0
    # Clear coat — extra polished surface gloss
    bsdf.inputs['Coat Weight'].default_value = 0.3
    bsdf.inputs['Coat Roughness'].default_value = 0.01
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    # Subtle internal imperfections (barely visible micro-flaws)
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-600, 0)

    voronoi = nodes.new('ShaderNodeTexVoronoi')
    voronoi.location = (-350, 0)
    voronoi.voronoi_dimensions = '3D'
    voronoi.feature = 'F1'
    voronoi.inputs['Scale'].default_value = 50.0
    voronoi.inputs['Randomness'].default_value = 1.0
    links.new(tex_coord.outputs['Object'], voronoi.inputs['Vector'])

    bump = nodes.new('ShaderNodeBump')
    bump.location = (200, -200)
    bump.inputs['Strength'].default_value = 0.02
    bump.inputs['Distance'].default_value = 0.01
    links.new(voronoi.outputs['Distance'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    return mat


def create_lead_material():
    """Lead core — oxidized dull grey metal with surface grain and pitting.

    Noise-driven oxidation patches vary color (bluish-grey ↔ dark brown-grey)
    and roughness (shinier fresh lead ↔ rougher oxidized). Voronoi + fine noise
    provide grain texture and corrosion pitting via bump.
    """
    mat, nodes, links = new_node_tree("Lead")

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (1000, 0)

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (600, 0)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.55
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-1000, 0)

    # Large-scale oxidation patches
    noise_oxide = nodes.new('ShaderNodeTexNoise')
    noise_oxide.location = (-600, 200)
    noise_oxide.inputs['Scale'].default_value = 3.0
    noise_oxide.inputs['Detail'].default_value = 6.0
    noise_oxide.inputs['Roughness'].default_value = 0.7
    noise_oxide.inputs['Distortion'].default_value = 0.5
    links.new(tex_coord.outputs['Object'], noise_oxide.inputs['Vector'])

    # Color: fresh lead (lighter bluish-grey) vs oxidized (darker brown-grey)
    ramp_color = nodes.new('ShaderNodeValToRGB')
    ramp_color.location = (-300, 200)
    ramp_color.color_ramp.elements[0].position = 0.35
    ramp_color.color_ramp.elements[0].color = (0.22, 0.22, 0.25, 1.0)
    ramp_color.color_ramp.elements[1].position = 0.65
    ramp_color.color_ramp.elements[1].color = (0.12, 0.11, 0.10, 1.0)
    links.new(noise_oxide.outputs['Fac'], ramp_color.inputs['Fac'])
    links.new(ramp_color.outputs['Color'], bsdf.inputs['Base Color'])

    # Roughness correlates with oxidation (darker = rougher)
    ramp_rough = nodes.new('ShaderNodeValToRGB')
    ramp_rough.location = (-300, -100)
    ramp_rough.color_ramp.elements[0].position = 0.3
    ramp_rough.color_ramp.elements[0].color = (0.45, 0.45, 0.45, 1.0)
    ramp_rough.color_ramp.elements[1].position = 0.7
    ramp_rough.color_ramp.elements[1].color = (0.7, 0.7, 0.7, 1.0)
    links.new(noise_oxide.outputs['Fac'], ramp_rough.inputs['Fac'])
    links.new(ramp_rough.outputs['Color'], bsdf.inputs['Roughness'])

    # Fine surface grain
    noise_grain = nodes.new('ShaderNodeTexNoise')
    noise_grain.location = (-600, -300)
    noise_grain.inputs['Scale'].default_value = 80.0
    noise_grain.inputs['Detail'].default_value = 12.0
    noise_grain.inputs['Roughness'].default_value = 0.5
    links.new(tex_coord.outputs['Object'], noise_grain.inputs['Vector'])

    # Voronoi pitting (corrosion spots)
    voronoi = nodes.new('ShaderNodeTexVoronoi')
    voronoi.location = (-600, -550)
    voronoi.voronoi_dimensions = '3D'
    voronoi.feature = 'F2'
    voronoi.inputs['Scale'].default_value = 15.0
    voronoi.inputs['Randomness'].default_value = 1.0
    links.new(tex_coord.outputs['Object'], voronoi.inputs['Vector'])

    # Combined bump: grain + pitting
    math_add = nodes.new('ShaderNodeMath')
    math_add.location = (-200, -400)
    math_add.operation = 'ADD'
    links.new(noise_grain.outputs['Fac'], math_add.inputs[0])
    links.new(voronoi.outputs['Distance'], math_add.inputs[1])

    math_scale = nodes.new('ShaderNodeMath')
    math_scale.location = (-50, -400)
    math_scale.operation = 'MULTIPLY'
    math_scale.inputs[1].default_value = 0.5
    links.new(math_add.outputs['Value'], math_scale.inputs[0])

    bump = nodes.new('ShaderNodeBump')
    bump.location = (250, -400)
    bump.inputs['Strength'].default_value = 0.4
    bump.inputs['Distance'].default_value = 0.05
    links.new(math_scale.outputs['Value'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    return mat


def create_copper_coil_material(name, tint):
    """Enameled copper coil with visible wire-winding bumps.

    UV-mapped Wave Texture (BANDS) creates wire turn ridges via bump map.
    Chained micro-scratch bump adds surface detail. Coat layer tinted with
    axis color simulates colored enamel insulation.

    tint: (r, g, b) axis-identifying enamel color.
    """
    mat, nodes, links = new_node_tree(name)

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (1000, 0)

    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (600, 0)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.25
    # Copper base blended with axis tint (60% copper, 40% tint)
    base_r = 0.85 * 0.6 + tint[0] * 0.4
    base_g = 0.45 * 0.6 + tint[1] * 0.4
    base_b = 0.15 * 0.6 + tint[2] * 0.4
    bsdf.inputs['Base Color'].default_value = (base_r, base_g, base_b, 1.0)
    # Colored enamel coat
    bsdf.inputs['Coat Weight'].default_value = 0.6
    bsdf.inputs['Coat Roughness'].default_value = 0.1
    bsdf.inputs['Coat Tint'].default_value = (*tint, 1.0)
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    # UV-mapped wave texture for wire winding pattern
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-800, 0)

    wave = nodes.new('ShaderNodeTexWave')
    wave.location = (-450, 100)
    wave.wave_type = 'BANDS'
    wave.bands_direction = 'X'   # Along torus major axis in UV space
    wave.wave_profile = 'SIN'
    wave.inputs['Scale'].default_value = 60.0     # ~60 wire turns visible
    wave.inputs['Distortion'].default_value = 0.5
    wave.inputs['Detail'].default_value = 2.0
    wave.inputs['Detail Scale'].default_value = 1.0
    wave.inputs['Detail Roughness'].default_value = 0.5
    links.new(tex_coord.outputs['UV'], wave.inputs['Vector'])

    # Wire winding bump (primary)
    bump_wire = nodes.new('ShaderNodeBump')
    bump_wire.location = (300, -100)
    bump_wire.inputs['Strength'].default_value = 0.5
    bump_wire.inputs['Distance'].default_value = 0.05
    links.new(wave.outputs['Fac'], bump_wire.inputs['Height'])

    # Fine micro-scratches (secondary)
    noise_micro = nodes.new('ShaderNodeTexNoise')
    noise_micro.location = (-450, -200)
    noise_micro.inputs['Scale'].default_value = 200.0
    noise_micro.inputs['Detail'].default_value = 10.0
    noise_micro.inputs['Roughness'].default_value = 0.4
    links.new(tex_coord.outputs['Object'], noise_micro.inputs['Vector'])

    bump_micro = nodes.new('ShaderNodeBump')
    bump_micro.location = (300, -300)
    bump_micro.inputs['Strength'].default_value = 0.1
    bump_micro.inputs['Distance'].default_value = 0.01
    links.new(noise_micro.outputs['Fac'], bump_micro.inputs['Height'])

    # Chain bumps: micro → wire → BSDF (stacks detail correctly)
    links.new(bump_micro.outputs['Normal'], bump_wire.inputs['Normal'])
    links.new(bump_wire.outputs['Normal'], bsdf.inputs['Normal'])

    # Color variation: ridges (brighter copper) vs grooves (darker)
    ramp_color = nodes.new('ShaderNodeValToRGB')
    ramp_color.location = (-150, 200)
    groove_r, groove_g, groove_b = base_r * 0.75, base_g * 0.75, base_b * 0.75
    ramp_color.color_ramp.elements[0].position = 0.4
    ramp_color.color_ramp.elements[0].color = (groove_r, groove_g, groove_b, 1.0)
    ramp_color.color_ramp.elements[1].position = 0.6
    ramp_color.color_ramp.elements[1].color = (base_r, base_g, base_b, 1.0)
    links.new(wave.outputs['Fac'], ramp_color.inputs['Fac'])
    links.new(ramp_color.outputs['Color'], bsdf.inputs['Base Color'])

    return mat


def create_energy_glow_material():
    """Field energy glow — noise-driven emission around the lead core.

    Mix of transparent + emission driven by 4D noise creates visible energy
    tendrils. Blue-to-cyan color ramp for plasma/field appearance.
    Animatable via W input on the noise node.
    """
    mat, nodes, links = new_node_tree("EnergyGlow")
    mat.surface_render_method = 'BLENDED'

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (800, 0)

    # Mix transparent + emission based on noise pattern
    mix = nodes.new('ShaderNodeMixShader')
    mix.location = (500, 0)
    links.new(mix.outputs['Shader'], output.inputs['Surface'])

    transparent = nodes.new('ShaderNodeBsdfTransparent')
    transparent.location = (250, 100)
    links.new(transparent.outputs['BSDF'], mix.inputs[1])

    emission = nodes.new('ShaderNodeEmission')
    emission.location = (250, -100)
    emission.inputs['Strength'].default_value = 8.0
    links.new(emission.outputs['Emission'], mix.inputs[2])

    # 4D noise for evolving energy patterns (keyframe W for animation)
    tex_coord = nodes.new('ShaderNodeTexCoord')
    tex_coord.location = (-700, 0)

    noise = nodes.new('ShaderNodeTexNoise')
    noise.location = (-400, 0)
    noise.noise_dimensions = '4D'
    noise.inputs['Scale'].default_value = 4.0
    noise.inputs['Detail'].default_value = 8.0
    noise.inputs['Roughness'].default_value = 0.6
    noise.inputs['Distortion'].default_value = 3.0
    noise.inputs['W'].default_value = 0.0
    links.new(tex_coord.outputs['Object'], noise.inputs['Vector'])

    # Density ramp — where energy is visible vs transparent
    ramp_density = nodes.new('ShaderNodeValToRGB')
    ramp_density.location = (-100, 100)
    ramp_density.color_ramp.elements[0].position = 0.4
    ramp_density.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp_density.color_ramp.elements[1].position = 0.7
    ramp_density.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    links.new(noise.outputs['Fac'], ramp_density.inputs['Fac'])
    links.new(ramp_density.outputs['Color'], mix.inputs['Fac'])

    # Color: deep blue → cyan-white (plasma/field appearance)
    ramp_color = nodes.new('ShaderNodeValToRGB')
    ramp_color.location = (-100, -200)
    ramp_color.color_ramp.elements[0].position = 0.0
    ramp_color.color_ramp.elements[0].color = (0.02, 0.05, 0.4, 1.0)
    ramp_color.color_ramp.elements[1].position = 1.0
    ramp_color.color_ramp.elements[1].color = (0.5, 0.8, 1.0, 1.0)
    links.new(noise.outputs['Fac'], ramp_color.inputs['Fac'])
    links.new(ramp_color.outputs['Color'], emission.inputs['Color'])

    return mat


def create_simple_material(name, color, metallic=0.0, roughness=0.5):
    """Basic Principled BSDF for axis lines, labels, support structure."""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    if color[3] < 1.0:
        mat.surface_render_method = 'BLENDED'
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
        bsdf.inputs['Alpha'].default_value = color[3]
    return mat


# ---------------------------------------------------------------------------
# GEOMETRY
# ---------------------------------------------------------------------------

def create_helmholtz_pair(name, coil_radius, wire_radius, axis, material, coils_col):
    """Create a Helmholtz pair: two torus coils at +/-R/2 along the specified axis."""
    half_sep = coil_radius / 2.0
    coils = []

    for sign, label in [(+1, "A"), (-1, "B")]:
        offset = sign * half_sep

        if axis == 'Z':
            loc = (0, 0, offset)
            rot = (0, 0, 0)
        elif axis == 'Y':
            loc = (0, offset, 0)
            rot = (math.pi / 2, 0, 0)
        elif axis == 'X':
            loc = (offset, 0, 0)
            rot = (0, math.pi / 2, 0)

        bpy.ops.mesh.primitive_torus_add(
            major_radius=coil_radius,
            minor_radius=wire_radius,
            major_segments=64,
            minor_segments=24,
            location=loc,
            rotation=rot,
        )
        torus = bpy.context.active_object
        torus.name = f"{name}_{label}"
        torus.data.materials.append(material)

        for face in torus.data.polygons:
            face.use_smooth = True

        move_to_collection(torus, coils_col)
        coils.append(torus)

    return coils


def build_device():
    """Construct the full device assembly with realistic materials."""

    clear_scene()

    # -- Collections --
    device_col = bpy.data.collections.new("Device Assembly")
    bpy.context.scene.collection.children.link(device_col)

    coils_col = bpy.data.collections.new("Coils")
    device_col.children.link(coils_col)

    internals_col = bpy.data.collections.new("Internals")
    device_col.children.link(internals_col)

    # ===================================================================
    # CERAMIC / ACRYLIC SPHERE (outer shell) — transparent with refraction
    # ===================================================================
    mat_acrylic = create_acrylic_material()

    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=SPHERE_RADIUS,
        segments=64, ring_count=32,
        location=(0, 0, 0),
    )
    sphere = bpy.context.active_object
    sphere.name = "Acrylic_Sphere"
    sphere.data.materials.append(mat_acrylic)
    bpy.ops.object.shade_smooth()
    move_to_collection(sphere, device_col)

    # ===================================================================
    # MERCURY (inner volume) — liquid metal mirror
    # ===================================================================
    mat_mercury = create_mercury_material()

    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=MERCURY_RADIUS,
        segments=48, ring_count=24,
        location=(0, 0, 0),
    )
    mercury = bpy.context.active_object
    mercury.name = "Mercury"
    mercury.data.materials.append(mat_mercury)
    bpy.ops.object.shade_smooth()
    move_to_collection(mercury, internals_col)

    # ===================================================================
    # ENERGY GLOW (field visualization around core)
    # ===================================================================
    mat_glow = create_energy_glow_material()

    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=GLOW_RADIUS,
        segments=32, ring_count=16,
        location=(0, 0, 0),
    )
    glow = bpy.context.active_object
    glow.name = "Energy_Field"
    glow.data.materials.append(mat_glow)
    bpy.ops.object.shade_smooth()
    move_to_collection(glow, internals_col)

    # ===================================================================
    # LEAD CORE — at verified equilibrium position (10.5mm below center)
    # ===================================================================
    mat_lead = create_lead_material()

    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=CORE_RADIUS,
        segments=32, ring_count=16,
        location=(0, 0, CORE_EQUILIBRIUM_Y),
    )
    core = bpy.context.active_object
    core.name = "Pb_Core"
    core.data.materials.append(mat_lead)
    bpy.ops.object.shade_smooth()
    move_to_collection(core, internals_col)

    # ===================================================================
    # HELMHOLTZ COIL PAIRS — copper with colored enamel insulation
    # Z (outermost, blue), Y (middle, green), X (innermost, red)
    # ===================================================================
    mat_coil_x = create_copper_coil_material("Coil_X", TINT_X)
    mat_coil_y = create_copper_coil_material("Coil_Y", TINT_Y)
    mat_coil_z = create_copper_coil_material("Coil_Z", TINT_Z)

    create_helmholtz_pair("Coil_Z", COIL_Z_RADIUS, WIRE_BUNDLE_RADIUS, 'Z', mat_coil_z, coils_col)
    create_helmholtz_pair("Coil_Y", COIL_Y_RADIUS, WIRE_BUNDLE_RADIUS, 'Y', mat_coil_y, coils_col)
    create_helmholtz_pair("Coil_X", COIL_X_RADIUS, WIRE_BUNDLE_RADIUS, 'X', mat_coil_x, coils_col)

    # ===================================================================
    # AXIS INDICATORS — thin cylinders
    # ===================================================================
    axis_length = COIL_Z_RADIUS * 1.3
    axis_radius = 0.001
    axis_configs = [
        ("Axis_X", (axis_length / 2, 0, 0), (0, math.pi / 2, 0), (*TINT_X, 0.5)),
        ("Axis_Y", (0, axis_length / 2, 0), (math.pi / 2, 0, 0), (*TINT_Y, 0.5)),
        ("Axis_Z", (0, 0, axis_length / 2), (0, 0, 0), (*TINT_Z, 0.5)),
    ]
    for name, loc, rot, color in axis_configs:
        mat = create_simple_material(f"Mat_{name}", color, roughness=0.8)
        bpy.ops.mesh.primitive_cylinder_add(
            radius=axis_radius,
            depth=axis_length,
            location=loc,
            rotation=rot,
        )
        ax = bpy.context.active_object
        ax.name = name
        ax.data.materials.append(mat)
        move_to_collection(ax, device_col)

    # ===================================================================
    # ANNOTATIONS — empties marking key positions
    # ===================================================================
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, CORE_EQUILIBRIUM_Y), radius=0.015)
    eq_marker = bpy.context.active_object
    eq_marker.name = "Pb_Equilibrium_10.5mm"
    move_to_collection(eq_marker, internals_col)

    bpy.ops.object.empty_add(type='SPHERE', location=(0, 0, 0), radius=0.005)
    center_marker = bpy.context.active_object
    center_marker.name = "Sphere_Center"
    move_to_collection(center_marker, internals_col)

    # ===================================================================
    # INTERIOR POINT LIGHT — illuminate mercury from inside
    # ===================================================================
    bpy.ops.object.light_add(type='POINT', location=(0, 0, 0))
    inner_light = bpy.context.active_object
    inner_light.name = "Inner_Glow_Light"
    inner_light.data.energy = 2.0
    inner_light.data.color = (0.4, 0.7, 1.0)  # Cool blue
    inner_light.data.shadow_soft_size = 0.02
    move_to_collection(inner_light, internals_col)

    return device_col


# ---------------------------------------------------------------------------
# CAMERA & LIGHTING
# ---------------------------------------------------------------------------

def setup_camera_and_lights():
    """Set up camera for a good 3/4 view and studio-style lighting."""

    # Camera — 3/4 view, slightly above
    bpy.ops.object.camera_add(
        location=(0.45, -0.45, 0.30),
        rotation=(math.radians(65), 0, math.radians(45)),
    )
    camera = bpy.context.active_object
    camera.name = "Camera"
    camera.data.lens = 50
    camera.data.clip_end = 10
    bpy.context.scene.camera = camera

    # Key light — warm, from upper right
    bpy.ops.object.light_add(type='AREA', location=(0.5, -0.3, 0.5))
    key = bpy.context.active_object
    key.name = "Key_Light"
    key.data.energy = 50
    key.data.size = 0.5
    key.data.color = (1.0, 0.95, 0.9)

    # Fill light — cooler, from left
    bpy.ops.object.light_add(type='AREA', location=(-0.4, -0.2, 0.3))
    fill = bpy.context.active_object
    fill.name = "Fill_Light"
    fill.data.energy = 20
    fill.data.size = 0.8
    fill.data.color = (0.9, 0.92, 1.0)

    # Rim light — from behind
    bpy.ops.object.light_add(type='AREA', location=(-0.1, 0.5, 0.2))
    rim = bpy.context.active_object
    rim.name = "Rim_Light"
    rim.data.energy = 30
    rim.data.size = 0.3

    # World background — dark with slight ambient
    world = bpy.data.worlds.get("World")
    if world and world.use_nodes:
        bg = world.node_tree.nodes.get("Background")
        if bg:
            bg.inputs['Color'].default_value = (0.02, 0.02, 0.04, 1.0)
            bg.inputs['Strength'].default_value = 0.5


# ---------------------------------------------------------------------------
# RENDER SETTINGS
# ---------------------------------------------------------------------------

def setup_render(output_path, engine='CYCLES'):
    """Configure render for glass/metal/volumetric materials."""
    scene = bpy.context.scene

    scene.render.engine = engine
    if engine == 'CYCLES':
        scene.cycles.device = 'CPU'
        scene.cycles.samples = 32         # Fast preview — open .blend for quality
        scene.cycles.use_denoising = False

        # Light path bounces — critical for glass refraction + metal reflection
        scene.cycles.max_bounces = 16
        scene.cycles.transparent_max_bounces = 16
        scene.cycles.transmission_bounces = 12
        scene.cycles.glossy_bounces = 8
        scene.cycles.volume_bounces = 4

        # Caustics for glass sphere
        scene.cycles.caustics_reflective = True
        scene.cycles.caustics_refractive = True
    else:
        scene.eevee.taa_render_samples = 64

    # Resolution
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100

    # Output
    scene.render.filepath = output_path
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'

    # Transparent background
    scene.render.film_transparent = True


# ---------------------------------------------------------------------------
# TEXT LABELS
# ---------------------------------------------------------------------------

def add_labels():
    """Add dimension labels as text objects."""
    labels = [
        ("R = 5 cm", (0.06, 0, 0), 0.008),
        ("Pb core (r=8mm)", (0.02, 0, CORE_EQUILIBRIUM_Y - 0.015), 0.005),
        ("10.5 mm below center", (-0.06, 0, CORE_EQUILIBRIUM_Y), 0.004),
        ("Z pair: R=22.5cm", (0, 0, COIL_Z_RADIUS / 2 + 0.02), 0.005),
        ("Y pair: R=18cm", (0, COIL_Y_RADIUS / 2 + 0.02, 0), 0.004),
        ("X pair: R=14cm", (COIL_X_RADIUS / 2 + 0.02, 0, 0), 0.004),
    ]
    for text, loc, size in labels:
        bpy.ops.object.text_add(location=loc)
        txt = bpy.context.active_object
        txt.name = f"Label_{text[:15]}"
        txt.data.body = text
        txt.data.size = size
        txt.data.align_x = 'LEFT'
        txt.rotation_euler = (math.radians(90), 0, 0)
        mat = create_simple_material(f"Mat_Label_{text[:10]}", (0.9, 0.9, 0.9, 1.0), roughness=0.9)
        txt.data.materials.append(mat)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    design_dir = os.path.join(project_root, "device-design")
    os.makedirs(design_dir, exist_ok=True)

    blend_path = os.path.join(design_dir, "prototype-model.blend")
    render_path = os.path.join(design_dir, "prototype-render.png")

    print(f"Building device model (v2: realistic materials)...")
    print(f"  .blend → {blend_path}")
    print(f"  render → {render_path}")

    build_device()
    add_labels()
    setup_camera_and_lights()
    setup_render(render_path)

    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Saved: {blend_path}")

    print("Rendering preview (Cycles, 32 samples, caustics on)...")
    bpy.ops.render.render(write_still=True)
    print(f"Saved: {render_path}")

    # ---------------------------------------------------------------
    # GLB EXPORT — geometry only for Three.js interactive viewer
    # Materials recreated in Three.js (Blender procedural nodes don't
    # export to glTF). Skip labels, lights, empties.
    # ---------------------------------------------------------------
    docs_dir = os.path.join(project_root, "docs", "models")
    os.makedirs(docs_dir, exist_ok=True)
    glb_path = os.path.join(docs_dir, "device.glb")

    # Deselect all, then select only mesh objects (skip text, lights, empties)
    bpy.ops.object.select_all(action='DESELECT')
    mesh_names_to_export = [
        "Acrylic_Sphere", "Mercury", "Energy_Field", "Pb_Core",
        "Coil_Z_A", "Coil_Z_B", "Coil_Y_A", "Coil_Y_B",
        "Coil_X_A", "Coil_X_B", "Axis_X", "Axis_Y", "Axis_Z",
    ]
    for obj in bpy.data.objects:
        if obj.name in mesh_names_to_export and obj.type == 'MESH':
            obj.select_set(True)

    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        use_selection=True,
        export_apply=True,
        export_materials='NONE',   # Materials recreated in Three.js
        export_colors=False,
        export_normals=True,
        export_extras=False,
    )
    print(f"Saved GLB (geometry only): {glb_path}")

    print("Done. Open .blend for high-quality re-render.")


if __name__ == "__main__":
    main()

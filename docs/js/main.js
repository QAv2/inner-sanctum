// ===========================================================
// main.js — Three.js viewer for the Reference Frame Engine
// Procedural geometry + GLB fallback, PBR materials, intro sequence
// ===========================================================

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { initLayerPanel } from './layers.js';
import { DOC_SECTIONS } from './content.js';

// ---------------------------------------------------------------------------
// PARAMETERS — from prototype-spec.md (all VERIFIED or design choice)
// ---------------------------------------------------------------------------

const SPHERE_RADIUS = 0.05;
const SPHERE_WALL   = 0.003;
const CORE_RADIUS   = 0.008;
const CORE_EQ_Y     = -0.0105;   // 10.5 mm below center
const MERCURY_RADIUS = SPHERE_RADIUS - SPHERE_WALL;
const GLOW_RADIUS    = 0.025;

const COIL_Z_RADIUS = 0.225;
const COIL_Y_RADIUS = 0.18;
const COIL_X_RADIUS = 0.14;
const WIRE_RADIUS   = 0.01;

const TINT_X = [0.86, 0.23, 0.23];
const TINT_Y = [0.23, 0.86, 0.23];
const TINT_Z = [0.23, 0.39, 0.86];

// ---------------------------------------------------------------------------
// SCENE SETUP
// ---------------------------------------------------------------------------

const canvas = document.getElementById('viewer-canvas');
const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  alpha: false,
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x06060c);

const camera = new THREE.PerspectiveCamera(45, 1, 0.01, 10);
camera.position.set(0.35, 0.25, 0.35);

// ---------------------------------------------------------------------------
// ENVIRONMENT MAP — procedural dark studio (no HDR file needed)
// ---------------------------------------------------------------------------

function createEnvMap() {
  const size = 256;
  const data = new Float32Array(size * size * 4);

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const i = (y * size + x) * 4;
      const ny = y / size;

      // Gradient: dark floor → slightly lit horizon → dark ceiling
      const horizon = Math.exp(-((ny - 0.5) ** 2) * 12);
      const base = 0.005;
      const v = base + horizon * 0.06;

      data[i]     = v * 0.8;   // R (slightly warm)
      data[i + 1] = v * 0.85;  // G
      data[i + 2] = v * 1.0;   // B (slightly cool)
      data[i + 3] = 1.0;
    }
  }

  const tex = new THREE.DataTexture(data, size, size, THREE.RGBAFormat, THREE.FloatType);
  tex.mapping = THREE.EquirectangularReflectionMapping;
  tex.needsUpdate = true;
  return tex;
}

const envMap = createEnvMap();
scene.environment = envMap;

// ---------------------------------------------------------------------------
// ORBIT CONTROLS
// ---------------------------------------------------------------------------

const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.5;
controls.minDistance = 0.08;
controls.maxDistance = 1.5;
controls.target.set(0, 0, 0);
controls.update();

// ---------------------------------------------------------------------------
// MATERIALS — recreated from Blender node trees as Three.js PBR
// ---------------------------------------------------------------------------

function createMercuryMaterial() {
  return new THREE.MeshPhysicalMaterial({
    color: 0xd8d8dc,
    metalness: 1.0,
    roughness: 0.03,
    envMapIntensity: 2.0,
  });
}

function createAcrylicMaterial() {
  return new THREE.MeshPhysicalMaterial({
    color: 0xf0f2ff,
    metalness: 0.0,
    roughness: 0.02,
    transmission: 0.95,
    ior: 1.49,
    thickness: 0.003,
    clearcoat: 0.3,
    clearcoatRoughness: 0.01,
    transparent: true,
    opacity: 0.3,
    side: THREE.DoubleSide,
    depthWrite: false,
  });
}

function createLeadMaterial() {
  return new THREE.MeshPhysicalMaterial({
    color: 0x2a2a2e,
    metalness: 1.0,
    roughness: 0.55,
    envMapIntensity: 0.6,
  });
}

function createEnergyMaterial() {
  return new THREE.MeshPhysicalMaterial({
    color: 0x0a1530,
    emissive: 0x3388ff,
    emissiveIntensity: 0.8,
    transparent: true,
    opacity: 0.25,
    side: THREE.DoubleSide,
    depthWrite: false,
    metalness: 0.0,
    roughness: 0.5,
  });
}

function createCoilMaterial(tint) {
  const r = 0.85 * 0.6 + tint[0] * 0.4;
  const g = 0.45 * 0.6 + tint[1] * 0.4;
  const b = 0.15 * 0.6 + tint[2] * 0.4;

  return new THREE.MeshPhysicalMaterial({
    color: new THREE.Color(r, g, b),
    metalness: 1.0,
    roughness: 0.25,
    clearcoat: 0.6,
    clearcoatRoughness: 0.1,
    sheen: 0.3,
    sheenColor: new THREE.Color(...tint),
    envMapIntensity: 1.2,
  });
}

function createAxisMaterial(color) {
  return new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: 0.5,
    depthWrite: false,
  });
}

// ---------------------------------------------------------------------------
// GEOMETRY — procedural (matches blender_export.py exactly)
// ---------------------------------------------------------------------------

const meshMap = {};

function buildDevice() {
  const group = new THREE.Group();

  // Acrylic Shell
  const shellGeo = new THREE.SphereGeometry(SPHERE_RADIUS, 64, 32);
  const shell = new THREE.Mesh(shellGeo, createAcrylicMaterial());
  shell.name = 'Acrylic_Sphere';
  shell.renderOrder = 10;
  group.add(shell);
  meshMap[shell.name] = shell;

  // Mercury
  const mercGeo = new THREE.SphereGeometry(MERCURY_RADIUS, 48, 24);
  const mercury = new THREE.Mesh(mercGeo, createMercuryMaterial());
  mercury.name = 'Mercury';
  group.add(mercury);
  meshMap[mercury.name] = mercury;

  // Energy Field
  const glowGeo = new THREE.SphereGeometry(GLOW_RADIUS, 32, 16);
  const energy = new THREE.Mesh(glowGeo, createEnergyMaterial());
  energy.name = 'Energy_Field';
  energy.renderOrder = 5;
  group.add(energy);
  meshMap[energy.name] = energy;

  // Lead Core
  const coreGeo = new THREE.SphereGeometry(CORE_RADIUS, 32, 16);
  const core = new THREE.Mesh(coreGeo, createLeadMaterial());
  core.name = 'Pb_Core';
  core.position.set(0, CORE_EQ_Y, 0);
  group.add(core);
  meshMap[core.name] = core;

  // Coil pairs
  const coilConfigs = [
    { prefix: 'Coil_Z', radius: COIL_Z_RADIUS, tint: TINT_Z, axis: 'z' },
    { prefix: 'Coil_Y', radius: COIL_Y_RADIUS, tint: TINT_Y, axis: 'y' },
    { prefix: 'Coil_X', radius: COIL_X_RADIUS, tint: TINT_X, axis: 'x' },
  ];

  coilConfigs.forEach(cfg => {
    const mat = createCoilMaterial(cfg.tint);
    const geo = new THREE.TorusGeometry(cfg.radius, WIRE_RADIUS, 24, 64);
    const halfSep = cfg.radius / 2;

    ['A', 'B'].forEach((label, i) => {
      const sign = i === 0 ? 1 : -1;
      const coil = new THREE.Mesh(geo, mat);
      coil.name = `${cfg.prefix}_${label}`;

      if (cfg.axis === 'z') {
        coil.position.set(0, sign * halfSep, 0);
        // Torus default is in XY plane — rotate to XZ plane (horizontal)
        coil.rotation.x = Math.PI / 2;
      } else if (cfg.axis === 'y') {
        coil.position.set(0, 0, sign * halfSep);
        // no extra rotation needed for Y-axis pair in XY plane
      } else {
        coil.position.set(sign * halfSep, 0, 0);
        coil.rotation.y = Math.PI / 2;
      }

      group.add(coil);
      meshMap[coil.name] = coil;
    });
  });

  // Axis indicators
  const axisLength = COIL_Z_RADIUS * 1.3;
  const axisGeo = new THREE.CylinderGeometry(0.001, 0.001, axisLength, 8);
  const axisConfigs = [
    { name: 'Axis_X', color: 0xff5555, rot: [0, 0, Math.PI / 2], pos: [0, 0, 0] },
    { name: 'Axis_Y', color: 0x55ff55, rot: [0, 0, 0],           pos: [0, 0, 0] },
    { name: 'Axis_Z', color: 0x5588ff, rot: [Math.PI / 2, 0, 0], pos: [0, 0, 0] },
  ];

  axisConfigs.forEach(cfg => {
    const axis = new THREE.Mesh(axisGeo, createAxisMaterial(cfg.color));
    axis.name = cfg.name;
    axis.position.set(...cfg.pos);
    axis.rotation.set(...cfg.rot);
    group.add(axis);
    meshMap[axis.name] = axis;
  });

  // Swap Y/Z for Three.js coordinate system (Blender Z-up → Three.js Y-up)
  // Actually, keep as-is since we built directly in Three.js coords

  scene.add(group);
  return group;
}

// ---------------------------------------------------------------------------
// LIGHTING
// ---------------------------------------------------------------------------

function setupLighting() {
  // Key light — warm, from upper right
  const key = new THREE.DirectionalLight(0xfff0e0, 2.0);
  key.position.set(2, 3, 1);
  scene.add(key);

  // Fill light — cooler, from left
  const fill = new THREE.DirectionalLight(0xe0e8ff, 0.8);
  fill.position.set(-2, 1, -1);
  scene.add(fill);

  // Rim light — from behind-below
  const rim = new THREE.DirectionalLight(0xffffff, 0.5);
  rim.position.set(0, -1, -2);
  scene.add(rim);

  // Ambient — very subtle
  const ambient = new THREE.AmbientLight(0x101020, 0.3);
  scene.add(ambient);

  // Inner glow point light (inside sphere)
  const inner = new THREE.PointLight(0x4488ff, 1.0, 0.15);
  inner.position.set(0, 0, 0);
  scene.add(inner);
}

// ---------------------------------------------------------------------------
// ANIMATION — energy field pulse
// ---------------------------------------------------------------------------

let clock = new THREE.Clock();

function animate() {
  requestAnimationFrame(animate);

  const t = clock.getElapsedTime();

  // Pulse energy field
  const energyMesh = meshMap['Energy_Field'];
  if (energyMesh && energyMesh.visible) {
    const pulse = 0.15 + Math.sin(t * 2.0) * 0.1;
    energyMesh.material.opacity = pulse;
    energyMesh.material.emissiveIntensity = 0.5 + Math.sin(t * 1.5) * 0.3;
    energyMesh.scale.setScalar(1.0 + Math.sin(t * 0.8) * 0.03);
  }

  controls.update();
  renderer.render(scene, camera);
}

// ---------------------------------------------------------------------------
// RESIZE
// ---------------------------------------------------------------------------

function onResize() {
  const container = document.getElementById('viewport-container');
  const w = container.clientWidth;
  const h = container.clientHeight;

  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}

const resizeObserver = new ResizeObserver(onResize);

// ---------------------------------------------------------------------------
// DOCS SIDEBAR
// ---------------------------------------------------------------------------

function renderDocs() {
  const container = document.getElementById('docs-content');

  container.innerHTML = `
    <h1>Reference Frame Engine</h1>
    <div class="subtitle">Bench-Scale Prototype \u2014 Spec v1.0 \u2014 2026-02-22</div>
  `;

  DOC_SECTIONS.forEach(section => {
    const details = document.createElement('details');
    if (section.open) details.open = true;

    const summary = document.createElement('summary');
    summary.textContent = section.title;
    details.appendChild(summary);

    const body = document.createElement('div');
    body.className = 'section-body';
    body.innerHTML = section.body;
    details.appendChild(body);

    container.appendChild(details);
  });
}

// ---------------------------------------------------------------------------
// INTRO SEQUENCE
// ---------------------------------------------------------------------------

async function playIntro() {
  const overlay = document.getElementById('intro-overlay');
  const textEl = document.getElementById('intro-text');
  const app = document.getElementById('app');

  const lines = [
    { text: 'ACCESSING SEALED ARCHIVE...', cls: '' },
    { text: '', cls: '' },
    { text: `CAPSULE DATE: 2026-02-22`, cls: 'dim' },
    { text: `ACCESSED: ${new Date().toISOString().split('T')[0]}`, cls: 'dim' },
    { text: '', cls: '' },
    { text: 'If you found this, you looked up.', cls: 'amber' },
  ];

  for (const line of lines) {
    if (line.text === '') {
      textEl.innerHTML += '\n';
      await sleep(300);
      continue;
    }

    const span = document.createElement('span');
    if (line.cls) span.className = line.cls;

    for (let i = 0; i < line.text.length; i++) {
      span.textContent += line.text[i];
      textEl.appendChild(span.cloneNode(true));
      // Replace the last appended span with updated content
      textEl.removeChild(textEl.lastChild);
      textEl.appendChild(span);
      await sleep(35);
    }
    textEl.innerHTML += '\n';
    await sleep(400);
  }

  await sleep(1200);

  // Fade out overlay, reveal app
  overlay.classList.add('fade-out');
  app.classList.add('visible');

  await sleep(1500);
  overlay.classList.add('hidden');
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

// ---------------------------------------------------------------------------
// INIT
// ---------------------------------------------------------------------------

async function init() {
  // Build scene immediately (renders behind intro)
  buildDevice();
  setupLighting();
  renderDocs();

  const viewportContainer = document.getElementById('viewport-container');
  resizeObserver.observe(viewportContainer);
  onResize();

  // Init layer panel
  initLayerPanel(scene, camera, meshMap);

  // Start render loop
  animate();

  // Skip intro with ?skip param
  const params = new URLSearchParams(window.location.search);
  if (params.has('skip')) {
    document.getElementById('intro-overlay').classList.add('hidden');
    document.getElementById('app').classList.add('visible');
  } else {
    await playIntro();
  }
}

init();

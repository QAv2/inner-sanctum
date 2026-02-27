// ===========================================================
// layers.js — Toggle controls + raycaster interaction
// 8 toggle groups, floating panel, click-to-inspect
// ===========================================================

import * as THREE from 'three';
import { COMPONENT_INFO } from './content.js';

// --- Layer definitions ---

const LAYERS = [
  { id: 'shell',  label: 'Shell',   color: '#8090a0', meshNames: ['Acrylic_Sphere'] },
  { id: 'mercury', label: 'Mercury', color: '#c0c8d0', meshNames: ['Mercury'] },
  { id: 'core',   label: 'Core',    color: '#4a4a50', meshNames: ['Pb_Core'] },
  { id: 'energy', label: 'Energy',  color: '#3388ff', meshNames: ['Energy_Field'] },
  { id: 'coil_z', label: 'Z Coils', color: '#3b64dd', meshNames: ['Coil_Z_A', 'Coil_Z_B'] },
  { id: 'coil_y', label: 'Y Coils', color: '#3bdd3b', meshNames: ['Coil_Y_A', 'Coil_Y_B'] },
  { id: 'coil_x', label: 'X Coils', color: '#dd3b3b', meshNames: ['Coil_X_A', 'Coil_X_B'] },
  { id: 'axes',   label: 'Axes',    color: '#888888', meshNames: ['Axis_X', 'Axis_Y', 'Axis_Z'] },
];

// --- State ---

const layerState = {};
LAYERS.forEach(l => { layerState[l.id] = true; });

let meshMap = {};      // meshName → THREE.Mesh
let raycaster = null;
let mouse = new THREE.Vector2();
let camera = null;
let scene = null;
let selectedMesh = null;
let highlightTimeout = null;

// --- Build the layer panel UI ---

export function initLayerPanel(sceneRef, cameraRef, meshMapRef) {
  scene = sceneRef;
  camera = cameraRef;
  meshMap = meshMapRef;
  raycaster = new THREE.Raycaster();

  const panel = document.getElementById('layer-panel');
  panel.innerHTML = '<h3>Layers</h3>';

  LAYERS.forEach(layer => {
    const row = document.createElement('div');
    row.className = 'layer-row';
    row.dataset.layer = layer.id;

    const check = document.createElement('input');
    check.type = 'checkbox';
    check.className = 'layer-check';
    check.checked = true;

    const dot = document.createElement('span');
    dot.className = 'layer-dot';
    dot.style.background = layer.color;

    const label = document.createElement('span');
    label.className = 'layer-label';
    label.textContent = layer.label;

    row.append(check, dot, label);
    panel.appendChild(row);

    // Toggle handler
    const toggle = () => {
      layerState[layer.id] = !layerState[layer.id];
      check.checked = layerState[layer.id];
      row.classList.toggle('off', !layerState[layer.id]);
      layer.meshNames.forEach(name => {
        const mesh = meshMap[name];
        if (mesh) mesh.visible = layerState[layer.id];
      });
    };

    check.addEventListener('change', toggle);
    row.addEventListener('click', (e) => {
      if (e.target !== check) toggle();
    });
  });

  // Click-to-inspect on canvas
  const canvas = document.getElementById('viewer-canvas');
  canvas.addEventListener('click', onCanvasClick);
  canvas.addEventListener('touchend', onCanvasTouch);
}

// --- Raycaster: click to inspect component ---

function onCanvasClick(e) {
  const rect = e.target.getBoundingClientRect();
  mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  castRay();
}

function onCanvasTouch(e) {
  if (e.changedTouches.length === 0) return;
  const t = e.changedTouches[0];
  const rect = e.target.getBoundingClientRect();
  mouse.x = ((t.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((t.clientY - rect.top) / rect.height) * 2 + 1;
  castRay();
}

function castRay() {
  if (!raycaster || !camera || !scene) return;

  raycaster.setFromCamera(mouse, camera);
  const allMeshes = [];
  scene.traverse(obj => {
    if (obj.isMesh && obj.visible) allMeshes.push(obj);
  });

  const hits = raycaster.intersectObjects(allMeshes, false);
  if (hits.length === 0) {
    hideInfo();
    return;
  }

  const hit = hits[0].object;
  const layerId = getLayerIdForMesh(hit.name);
  if (!layerId) {
    hideInfo();
    return;
  }

  showInfo(layerId, hit);
}

function getLayerIdForMesh(meshName) {
  for (const layer of LAYERS) {
    if (layer.meshNames.includes(meshName)) return layer.id;
  }
  return null;
}

// --- Info panel ---

function showInfo(layerId, mesh) {
  const info = COMPONENT_INFO[layerId];
  if (!info) return;

  const panel = document.getElementById('component-info');

  const rigorClass = `rigor-${info.rigor}`;
  const rigorLabel = info.rigor === 'model' ? 'Model Prediction' :
                     info.rigor.charAt(0).toUpperCase() + info.rigor.slice(1);

  panel.innerHTML = `
    <div class="info-name">${info.name}</div>
    <div class="info-role">${info.role}</div>
    <div class="info-params">${info.params.map(p => `<span>${p}</span>`).join('')}</div>
    <span class="rigor-tag ${rigorClass}">${rigorLabel}</span>
    <span style="font-size:10px; color: #6a7080; margin-left: 8px;">${info.rigorNote}</span>
  `;
  panel.classList.add('visible');

  // Highlight mesh briefly
  highlightMesh(mesh);
}

function hideInfo() {
  document.getElementById('component-info').classList.remove('visible');
  clearHighlight();
}

// --- Highlight on selection ---

function highlightMesh(mesh) {
  clearHighlight();
  selectedMesh = mesh;

  if (mesh.material && mesh.material.emissive) {
    mesh._origEmissive = mesh.material.emissive.clone();
    mesh._origEmissiveIntensity = mesh.material.emissiveIntensity;
    mesh.material.emissive.set(0x3388ff);
    mesh.material.emissiveIntensity = 0.4;

    highlightTimeout = setTimeout(() => {
      if (mesh._origEmissive) {
        mesh.material.emissive.copy(mesh._origEmissive);
        mesh.material.emissiveIntensity = mesh._origEmissiveIntensity;
        delete mesh._origEmissive;
        delete mesh._origEmissiveIntensity;
      }
    }, 800);
  }
}

function clearHighlight() {
  if (highlightTimeout) clearTimeout(highlightTimeout);
  if (selectedMesh && selectedMesh._origEmissive) {
    selectedMesh.material.emissive.copy(selectedMesh._origEmissive);
    selectedMesh.material.emissiveIntensity = selectedMesh._origEmissiveIntensity;
    delete selectedMesh._origEmissive;
    delete selectedMesh._origEmissiveIntensity;
  }
  selectedMesh = null;
}

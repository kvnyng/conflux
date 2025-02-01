import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { GUI } from 'dat.gui';

const SERVER_URL = "http://api.cosmicimprint.org";
const ENDPOINT_STL = SERVER_URL + "/landscape/latest/";

const canvas = document.getElementById('middleColumnCanvas');
const container = document.getElementById('middleColumn');

const loader = new STLLoader();
const scene = new THREE.Scene();

// Create camera with correct aspect ratio
const camera = new THREE.PerspectiveCamera(
    75,
    canvas.clientWidth / canvas.clientHeight,
    0.1,
    1000
);
const renderer = new THREE.WebGLRenderer({ canvas, alpha: true });
renderer.setClearColor(0x000000, 0);
renderer.setSize(canvas.clientWidth, canvas.clientHeight);

let planet;
let pointLight;
let controls;

// Orbit properties
let orbitRadius = 10;
let orbitSpeed = 0.001;
let orbitAngle = 0;
let zoomScale = 1;
let orbitHeight = 50; // Initial height above model
const scale = 10;

// Lighting
const LIGHT_INTENSITY = 20;
let modelCenter = new THREE.Vector3(0, 0, 0);

// Helper function to compute optimal orbit distance
function calculateOptimalOrbitRadius(bbox) {
    const modelWidth = bbox.max.x - bbox.min.x;
    const modelDepth = bbox.max.y - bbox.min.y;
    const modelHeight = bbox.max.z - bbox.min.z;

    const maxDimension = Math.max(modelWidth, modelDepth, modelHeight);
    const aspectRatio = canvas.clientWidth / canvas.clientHeight;
    return (maxDimension * 1.5) / Math.tan((camera.fov * Math.PI) / 360) / aspectRatio;
}

async function fetchSTLFile(endpoint) {
    try {
        const response = await fetch(endpoint);
        if (!response.ok) {
            throw new Error(`Failed to fetch STL file: ${response.statusText}`);
        }
        return await response.blob(); // Return the STL file as a blob
    } catch (error) {
        console.error("Error loading STL file:", error);
        return null;
    }
}

function loadSTLIntoScene(blob, scene) {
    if (!blob) return;

    const stl_url = URL.createObjectURL(blob);

    loader.load(stl_url, function (geometry) {
        geometry.computeBoundingBox();
        geometry.center();

        const bbox = geometry.boundingBox;
        modelCenter = new THREE.Vector3(
            (bbox.max.x + bbox.min.x) / 2,
            (bbox.max.y + bbox.min.y) / 2,
            (bbox.max.z + bbox.min.z) / 2
        );

        const modelHeight = bbox.max.z - bbox.min.z;
        orbitHeight = modelHeight * 1.5;

        const material = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.5, metalness: 0.2 });
        planet = new THREE.Mesh(geometry, material);
        planet.scale.set(scale, scale, scale);
        scene.add(planet);

        orbitRadius = calculateOptimalOrbitRadius(bbox);

        pointLight = new THREE.PointLight(0xffffff, LIGHT_INTENSITY);
        pointLight.position.set(50, 50, 50);
        scene.add(pointLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(-50, 60, 150);
        scene.add(directionalLight);

        planet.add(pointLight);

        // Set initial camera position
        camera.position.set(modelCenter.x + orbitRadius, modelCenter.y + orbitHeight, modelCenter.z);
        camera.lookAt(modelCenter);

        // // Initialize OrbitControls
        // controls = new OrbitControls(camera, renderer.domElement);
        // controls.enableDamping = true;
        // controls.dampingFactor = 0.05;
        // controls.enableZoom = true; // Allow zooming
        // controls.enablePan = false; // Disable panning
        // controls.rotateSpeed = 0.8;

        // controls.target.set(modelCenter.x, modelCenter.y, modelCenter.z);
        // controls.update();
    });
}

fetchSTLFile(ENDPOINT_STL).then(blob => loadSTLIntoScene(blob, scene));

// Ambient light
const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
scene.add(ambientLight);

// Animation loop (Camera Orbits & Zooms Into Model)
function animate() {
    requestAnimationFrame(animate);

    if (planet) {
        if (!controls || !controls.mouseButtons.LEFT) {
            // Only auto-orbit when mouse is not dragging
            orbitAngle += orbitSpeed;
            const adjustedRadius = orbitRadius / zoomScale;
            camera.position.x = modelCenter.x + adjustedRadius * Math.cos(orbitAngle);
            camera.position.z = modelCenter.z + adjustedRadius * Math.sin(orbitAngle);
            camera.position.y = modelCenter.y + orbitHeight;

            camera.lookAt(modelCenter);
        }
    }

    if (controls) controls.update();
    renderer.render(scene, camera);
}
animate();

// Resize event listener to adjust canvas and camera
function onWindowResize() {
    const width = container.clientWidth;
    const height = container.clientHeight;

    renderer.setSize(width, height);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();

    if (planet) {
        const bbox = planet.geometry.boundingBox;
        orbitRadius = calculateOptimalOrbitRadius(bbox);
    }
}

window.addEventListener("resize", onWindowResize);

// // GUI for adjusting camera orbit and zoom
// const gui = new GUI();
// const settings = {
//     orbitRadius: orbitRadius,
//     orbitSpeed: orbitSpeed,
//     zoomScale: zoomScale,
//     orbitHeight: orbitHeight
// };

// gui.add(settings, 'orbitRadius', 10, 50).onChange(value => {
//     orbitRadius = value;
// });

// gui.add(settings, 'orbitSpeed', 0.0001, 0.01).onChange(value => {
//     orbitSpeed = value;
// });

// gui.add(settings, 'zoomScale', 0.5, 5).onChange(value => {
//     zoomScale = value;
// });

// gui.add(settings, 'orbitHeight', 10, 200).onChange(value => {
//     orbitHeight = value;
// });

console.log("Loaded second column landscape script");

const eventSource = new EventSource(SERVER_URL + "/notifications/");

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Push Notification:", data.message);
    alert(`New Notification: ${data.message}`);
    reloadSTLModel();
};

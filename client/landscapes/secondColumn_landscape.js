import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { GUI } from 'dat.gui';

const SERVER_URL = "http://api.cosmicimprint.org";
const ENDPOINT_LANDSCAPE = SERVER_URL + "/landscape/latest/";

const canvas = document.getElementById('middleColumnCanvas');
const container = document.getElementById('middleColumn');

const loader = new STLLoader();
const scene = new THREE.Scene();

// Camera setup
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

// Orbit properties
let orbitRadius = 100;
let zoomScale = 1;
let orbitHeight = 50;
const scale = 10;

const LIGHT_INTENSITY = 20;
let modelCenter = new THREE.Vector3(0, 0, 0);

// Orbit Controls: Allow Rotation Around Model's Center
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.enableZoom = false; // Lock zooming (we use manual zoom control)
controls.enablePan = false;  // Lock panning
controls.rotateSpeed = 0.8;
controls.minPolarAngle = Math.PI / 3;  // Prevent extreme overhead rotation
controls.maxPolarAngle = (2 * Math.PI) / 3;

// Calculate optimal orbit radius for visibility
function calculateOptimalOrbitRadius(bbox) {
    const modelWidth = bbox.max.x - bbox.min.x;
    const modelDepth = bbox.max.y - bbox.min.y;
    const modelHeight = bbox.max.z - bbox.min.z;

    const maxDimension = Math.max(modelWidth, modelDepth, modelHeight);
    const aspectRatio = canvas.clientWidth / canvas.clientHeight;
    return (maxDimension * 1.5) / Math.tan((camera.fov * Math.PI) / 360) / aspectRatio;
}

// Load STL model
fetch(ENDPOINT_LANDSCAPE)
    .then(response => {
        if (!response.ok) throw new Error(`Failed to fetch STL file: ${response.statusText}`);
        return response.blob();
    })
    .then(blob => {
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
            orbitHeight = modelHeight * 1.5; // Adjust height dynamically

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

            controls.target.set(modelCenter.x, modelCenter.y, modelCenter.z);
            controls.update();
        });
    })
    .catch(error => console.error("Error loading STL file:", error));

const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
scene.add(ambientLight);

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    controls.update();  // Update orbit controls
    renderer.render(scene, camera);
}
animate();

// Handle window resize
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

// GUI Controls
const gui = new GUI();
const settings = {
    orbitRadius: orbitRadius,
    zoomScale: zoomScale,
    orbitHeight: orbitHeight
};

gui.add(settings, 'orbitRadius', 50, 300).onChange(value => orbitRadius = value);
gui.add(settings, 'zoomScale', 0.5, 5).onChange(value => zoomScale = value);
gui.add(settings, 'orbitHeight', 10, 200).onChange(value => {
    orbitHeight = value;
    camera.position.y = modelCenter.y + orbitHeight;
    camera.lookAt(modelCenter);
});

console.log("hi");
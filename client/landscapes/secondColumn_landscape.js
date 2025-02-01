import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { GUI } from 'dat.gui';

const SERVER_URL = "http://api.cosmicimprint.org";
const ENDPOINT_STL = SERVER_URL + "/landscape/latest";

// Get the correct canvas and container
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
renderer.setClearColor(0x000000, 0); // Fully transparent
renderer.setSize(canvas.clientWidth, canvas.clientHeight);

let planet;
let pointLight;

// Orbit properties
let orbitRadius = 100; // Initial camera distance
let orbitSpeed = 0.001; // Speed of rotation
let orbitAngle = 0; // Angle in radians
let zoomScale = 1; // Adjustable zoom scale
const scale = 10;

// Lighting
const LIGHT_INTENSITY = 20;

// Variable to store the model center position
let modelCenter = new THREE.Vector3(0, 0, 0);

// Fetch and load STL model
fetch(ENDPOINT_STL)
    .then(response => {
        if (!response.ok) {
            throw new Error(`Failed to fetch STL file: ${response.statusText}`);
        }
        return response.blob();
    })
    .then(blob => {
        const stl_url = URL.createObjectURL(blob);

        loader.load(stl_url, function (geometry) {
            geometry.computeBoundingBox();
            geometry.center(); // Centers the model at (0,0,0)

            // Compute model center based on bounding box
            const bbox = geometry.boundingBox;
            modelCenter = new THREE.Vector3(
                (bbox.max.x + bbox.min.x) / 2,
                (bbox.max.y + bbox.min.y) / 2,
                (bbox.max.z + bbox.min.z) / 2
            );

            const material = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.5, metalness: 0.2 });
            planet = new THREE.Mesh(geometry, material);
            planet.scale.set(scale, scale, scale);
            scene.add(planet);

            // Adjust camera distance based on model size
            orbitRadius = Math.max(bbox.max.x - bbox.min.x, bbox.max.y - bbox.min.y, bbox.max.z - bbox.min.z) * 2;

            // Add lights
            pointLight = new THREE.PointLight(0xffffff, LIGHT_INTENSITY);
            pointLight.position.set(50, 50, 50);
            scene.add(pointLight);

            const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
            directionalLight.position.set(-50, 60, 150);
            scene.add(directionalLight);

            planet.add(pointLight);
        });
    })
    .catch(error => {
        console.error("Error loading STL file:", error);
    });

// Ambient light
const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
scene.add(ambientLight);

// Orbit Controls (for user interaction)
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.enableZoom = false; // Disable default zoom, we'll use our own

// Animation loop (Camera Orbits & Zooms Into Model)
function animate() {
    requestAnimationFrame(animate);

    if (planet) {
        // Increment angle for smooth rotation
        orbitAngle += orbitSpeed;

        // Update camera position to orbit around the model center
        const adjustedRadius = orbitRadius / zoomScale;
        camera.position.x = modelCenter.x + adjustedRadius * Math.cos(orbitAngle);
        camera.position.z = modelCenter.z + adjustedRadius * Math.sin(orbitAngle);
        camera.position.y = modelCenter.y + adjustedRadius * 0.2; // Slight vertical offset for better view

        camera.lookAt(modelCenter);
    }

    controls.update();
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
}

window.addEventListener("resize", onWindowResize);

// GUI for adjusting camera orbit and zoom
const gui = new GUI();
const settings = {
    orbitRadius: orbitRadius,
    orbitSpeed: orbitSpeed,
    zoomScale: zoomScale
};

gui.add(settings, 'orbitRadius', 50, 200).onChange(value => {
    orbitRadius = value;
});

gui.add(settings, 'orbitSpeed', 0.0001, 0.01).onChange(value => {
    orbitSpeed = value;
});

gui.add(settings, 'zoomScale', 0.5, 5).onChange(value => {
    zoomScale = value;
});
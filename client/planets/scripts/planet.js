// Import necessary modules from three.js
import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer';
import { GUI } from 'dat.gui';

const SERVER_URL = "http://api.cosmicimprint.org"
const ENDPOINT_STL = SERVER_URL + "/planet/stl/latest";

// Initialize the scene, camera, and renderer
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Handle window resizing
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    updateFloatingTextPositions();
});

const starGeometry = new THREE.BufferGeometry();
const starMaterial = new THREE.PointsMaterial({
    size: 2.5, // Base size of the stars
    vertexColors: true, // Enable vertex coloring
    sizeAttenuation: true, // Allow size to scale with perspective
    map: new THREE.TextureLoader().load('https://threejs.org/examples/textures/sprites/circle.png'), // Use a circular texture
    alphaTest: 0.5, // Discard pixels with low alpha
    transparent: true, // Enable transparency
});

const starCount = 200000; // Increase the number of stars
const starPositions = new Float32Array(starCount * 3);
const starColors = new Float32Array(starCount * 3); // Array to store RGB values for each star
const starBrightness = new Float32Array(starCount); // Track brightness for twinkling

// Populate star positions and colors
for (let i = 0; i < starCount; i++) {
    // Random positions
    starPositions[i * 3] = (Math.random() - 0.5) * 3000; // X-axis
    starPositions[i * 3 + 1] = (Math.random() - 0.5) * 3000; // Y-axis
    starPositions[i * 3 + 2] = (Math.random() - 0.5) * 3000; // Z-axis

    // Random colors (varying shades of white, blue, and yellow)
    const color = new THREE.Color(255, 255, 255);
    starColors[i * 3] = color.r;
    starColors[i * 3 + 1] = color.g;
    starColors[i * 3 + 2] = color.b;

    // Initial brightness for each star
    starBrightness[i] = 1.0; // Start fully bright
}

// Add attributes to the geometry
starGeometry.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
starGeometry.setAttribute('color', new THREE.BufferAttribute(starColors, 3));

// Create Points object
const stars = new THREE.Points(starGeometry, starMaterial);
scene.add(stars);

// Load the STL model
const STL_PATH = "./assets/KevinYang_fe5e59a6d3699fd1af0470b1fa5773611_planet.stl"
// const STL_PATH = "./assets/tiled_sphere_hannah.stl";
const loader = new STLLoader();
let planet;
let pointLight;
let isMousePressed = false;
let prevMousePosition = { x: 0, y: 0 };
let rotationVelocity = { x: 0, y: 0 };

const LIGHT_INTENSITY = 20;
const LIGHT_DIR_X = -50;
const LIGHT_DIR_Y = 60;
const LIGHT_DIR_Z = 150;

// Fetch the latest STL file from the API and load it
fetch(ENDPOINT_STL)
    .then(response => {
        if (!response.ok) {
            throw new Error(`Failed to fetch STL file: ${response.statusText}`);
        }
        return response.blob();
    })
    .then(blob => {
        const stl_url = URL.createObjectURL(blob); // Create an object URL for the STL file

        loader.load(stl_url, function (geometry) {
            const material = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.5, metalness: 0.2 });
            planet = new THREE.Mesh(geometry, material);
            planet.rotation.x = Math.PI / 2; // Adjust initial orientation if needed
            scene.add(planet);

            // Add a point light targeting the STL model
            pointLight = new THREE.PointLight(0xffffff, LIGHT_INTENSITY);
            pointLight.position.set(50, 50, 50); // Position the light
            scene.add(pointLight);

            // Add another light for better visibility
            const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
            directionalLight.position.set(LIGHT_DIR_X, LIGHT_DIR_Y, LIGHT_DIR_Z);
            scene.add(directionalLight);

            // Attach the point light to the planet for consistent lighting
            planet.add(pointLight);

            planet.scale.set(20, 20, 20); // Set initial scale
        });
    })
    .catch(error => {
        console.error("Error loading STL file:", error);
    });

// Mouse rotation event listeners
document.addEventListener('mousedown', (event) => {
    isMousePressed = true;
    prevMousePosition.x = event.clientX;
    prevMousePosition.y = event.clientY;
});

document.addEventListener('mouseup', () => {
    isMousePressed = false;
});

document.addEventListener('mousemove', (event) => {
    if (isMousePressed && planet) {
        const deltaX = event.clientX - prevMousePosition.x;
        const deltaY = event.clientY - prevMousePosition.y;

        rotationVelocity.x = deltaY * 0.01; // Adjust rotation speed
        rotationVelocity.y = deltaX * 0.01; // Adjust rotation speed

        prevMousePosition.x = event.clientX;
        prevMousePosition.y = event.clientY;
    }
});

// Lighting
const ambientLight = new THREE.AmbientLight(0xffffff, 0.2);
scene.add(ambientLight);

// Camera position and floating animation
camera.position.set(0, 0, 100);
const cameraMotion = {
    x: 0,
    y: 0,
    z: 0
};

const CAM_X_MOVE_RATE = 0.0005;
const CAM_Y_MOVE_RATE = 0.00075;

function animateCamera() {
    cameraMotion.x = Math.sin(Date.now() * CAM_X_MOVE_RATE) * 5; // Slow sine wave motion
    cameraMotion.y = Math.sin(Date.now() * CAM_Y_MOVE_RATE) * 3; // Slightly slower sine wave motion

    camera.position.x = cameraMotion.x;
    camera.position.y = cameraMotion.y;
    camera.lookAt(0, 0, 0); // Always look at the center
}

// Orbit Controls
const controls = new OrbitControls(camera, renderer.domElement);

const X_AXIS_ROTATION_RATE = 0.005;
const Y_AXIS_ROTATION_RATE = 0.0075;

// Animation loop
function animate() {
    requestAnimationFrame(animate);

    if (planet) {
        // Apply rotation inertia and natural spin
        planet.rotation.x += rotationVelocity.x + X_AXIS_ROTATION_RATE; // Slow natural spin on x-axis
        planet.rotation.y += rotationVelocity.y + Y_AXIS_ROTATION_RATE; // Slow natural spin on y-axis

        // Gradually reduce rotation velocity for inertia effect
        rotationVelocity.x *= 0.95;
        rotationVelocity.y *= 0.95;
    }

    animateCamera(); // Add camera floating animation
    renderer.render(scene, camera);
}
animate();

// GUI for adjusting size, lighting, and light position
const MAX_SCALE_VALUE = 50;
const MIN_SCALE_VALUE = 20;
const MAX_LIGHT_INTENSITY = 100;
const MIN_LIGHT_INTENSITY = 50;
const MIN_LIGHT_POSITION = -500;
const MAX_LIGHT_POSITION = 500;

const LIGHT_X_POSITION = 50;
const LIGHT_Y_POSITION = 50;
const LIGHT_Z_POSITION = 50;

const gui = new GUI();
const settings = {
    scale: MIN_SCALE_VALUE,
    lightIntensity: MIN_LIGHT_INTENSITY,
    lightX: LIGHT_X_POSITION,
    lightY: LIGHT_Y_POSITION,
    lightZ: LIGHT_Z_POSITION
};

// gui.add(settings, 'scale', MIN_SCALE_VALUE, MAX_SCALE_VALUE).onChange((value) => {
//     if (planet) {
//         planet.scale.set(value, value, value);
//     }
// });
// gui.add(settings, 'lightIntensity', MIN_LIGHT_INTENSITY, MAX_LIGHT_INTENSITY).onChange((value) => {
//     if (pointLight) {
//         pointLight.intensity = value;
//     }
// });

const eventSource = new EventSource(SERVER_URL + "/notifications/");

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Push Notification:", data.message);
    alert(`New Notification: ${data.message}`);
};

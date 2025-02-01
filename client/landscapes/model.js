
import * as THREE from 'three';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { GUI } from 'dat.gui';

const SERVER_URL = "http://api.cosmicimprint.org"
const ENDPOINT_STL = SERVER_URL + "/planets/stl/latest";

// STL Models
const canvas = document.getElementById('leftColumnCanvas');
const loader = new STLLoader();
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / 2 / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas, alpha: true });
renderer.setClearColor(0x000000, 0); // Fully transparent


renderer.setSize(window.innerWidth / 2, window.innerHeight);
camera.position.z = 5;

// const controls = new OrbitControls(mainCamera, mainRenderer.domElement);

// Load the STL model
// const STL_PATH = "./assets/tiled_sphere_hannah.stl";
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

gui.add(settings, 'scale', MIN_SCALE_VALUE, MAX_SCALE_VALUE).onChange((value) => {
    if (planet) {
        planet.scale.set(value, value, value);
    }
});
gui.add(settings, 'lightIntensity', MIN_LIGHT_INTENSITY, MAX_LIGHT_INTENSITY).onChange((value) => {
    if (pointLight) {
        pointLight.intensity = value;
    }
});

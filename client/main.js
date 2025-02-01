import * as THREE from 'three';

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
});

// Add stars
const starGeometry = new THREE.BufferGeometry();
const starMaterial = new THREE.PointsMaterial({
    size: 2.5,
    vertexColors: true,
    map: new THREE.TextureLoader().load('https://threejs.org/examples/textures/sprites/circle.png'),
    alphaTest: 0.5,
    transparent: true,
});
const starCount = 50000;
const starPositions = [];
const starColors = [];
for (let i = 0; i < starCount; i++) {
    starPositions.push(
        (Math.random() - 0.5) * 2000, // X-axis
        (Math.random() - 0.5) * 2000, // Y-axis
        (Math.random() - 0.5) * 2000  // Z-axis
    );

    const color = new THREE.Color().setHSL(Math.random(), 1.0, 0.9); // Bright random color
    starColors.push(color.r, color.g, color.b);
}
starGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starPositions, 3));
starGeometry.setAttribute('color', new THREE.Float32BufferAttribute(starColors, 3));

const stars = new THREE.Points(starGeometry, starMaterial);
scene.add(stars);

// Animate the stars
camera.position.set(0, 0, 300);
const cameraMotion = {
    x: 0,
    y: 0,
    z: 0
};
const CAM_X_MOVE_RATE = 0.0005;
const CAM_Y_MOVE_RATE = 0.00075;

function animateCamera() {
    cameraMotion.x = Math.sin(Date.now() * CAM_X_MOVE_RATE) * 20; // Sine wave motion for the camera
    cameraMotion.y = Math.sin(Date.now() * CAM_Y_MOVE_RATE) * 15;

    camera.position.x = cameraMotion.x;
    camera.position.y = cameraMotion.y;
    camera.lookAt(0, 0, 0); // Always look at the center
}

// Render loop
function animate() {
    requestAnimationFrame(animate);

    // Rotate the stars for a dynamic background
    stars.rotation.y += 0.0005;
    animateCamera();
    renderer.render(scene, camera);
}
animate();
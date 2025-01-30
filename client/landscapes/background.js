import * as THREE from 'three';
// Background stars
const bgCanvas = document.getElementById('bg');
const bgScene = new THREE.Scene();
const bgCamera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const bgRenderer = new THREE.WebGLRenderer({ canvas: bgCanvas });

bgRenderer.setPixelRatio(window.devicePixelRatio);
bgRenderer.setSize(window.innerWidth, window.innerHeight);
bgCamera.position.setZ(1);

const starGeometry = new THREE.BufferGeometry();
const starMaterial = new THREE.PointsMaterial({ color: 0xffffff });

const stars = 10000;
const positions = new Float32Array(stars * 3);

for (let i = 0; i < stars; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 2000;
    positions[i * 3 + 1] = (Math.random() - 0.5) * 2000;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 2000;
}

starGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
const starMesh = new THREE.Points(starGeometry, starMaterial);
bgScene.add(starMesh);

function animateStars() {
    requestAnimationFrame(animateStars);
    starMesh.rotation.y += 0.0005;
    bgRenderer.render(bgScene, bgCamera);
}
animateStars();
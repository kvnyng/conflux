
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader';
// STL Models
const loader = new STLLoader();
const mainScene = new THREE.Scene();
const mainCamera = new THREE.PerspectiveCamera(75, window.innerWidth / 2 / window.innerHeight, 0.1, 1000);
const mainRenderer = new THREE.WebGLRenderer();

document.getElementById('largeModel').appendChild(mainRenderer.domElement);
mainRenderer.setSize(window.innerWidth / 2, window.innerHeight);
mainCamera.position.z = 5;

const controls = new OrbitControls(mainCamera, mainRenderer.domElement);

loader.load('largeModel.stl', function (geometry) {
    const material = new THREE.MeshStandardMaterial({ color: 0xff5533 });
    const mesh = new THREE.Mesh(geometry, material);
    mainScene.add(mesh);

    function animateLargeModel() {
        requestAnimationFrame(animateLargeModel);
        mesh.rotation.x += 0.01;
        mesh.rotation.y += 0.01;
        mainRenderer.render(mainScene, mainCamera);
    }
    animateLargeModel();
});

const smallScene = new THREE.Scene();
const smallCamera = new THREE.PerspectiveCamera(75, window.innerWidth / 4 / window.innerHeight, 0.1, 1000);
const smallRenderer = new THREE.WebGLRenderer();

document.getElementById('smallModel').appendChild(smallRenderer.domElement);
smallRenderer.setSize(window.innerWidth / 4, window.innerHeight / 2);
smallCamera.position.z = 5;

loader.load('smallModel.stl', function (geometry) {
    const material = new THREE.MeshStandardMaterial({ color: 0x33ff55 });
    const mesh = new THREE.Mesh(geometry, material);
    smallScene.add(mesh);

    function animateSmallModel() {
        requestAnimationFrame(animateSmallModel);
        mesh.rotation.x += 0.02;
        mesh.rotation.y += 0.02;
        smallRenderer.render(smallScene, smallCamera);
    }
    animateSmallModel();
});
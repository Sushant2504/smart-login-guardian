/**
 * 3D Globe Visualization using Three.js
 * Shows real-time login attempts on an interactive 3D Earth globe
 */

let scene, camera, renderer, globe, controls;
let loginMarkers = [];
let autoRotate = true;

function initGlobe() {
    const container = document.getElementById('globeContainer');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Create scene
    scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0x0a0e1a, 100, 300);

    // Create camera
    camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 150;

    // Create renderer
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setClearColor(0x0a0e1a, 0);
    container.appendChild(renderer.domElement);

    // Add controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.autoRotate = autoRotate;
    controls.autoRotateSpeed = 0.5;
    controls.minDistance = 80;
    controls.maxDistance = 200;

    // Create globe
    createGlobe();

    // Add lights
    addLights();

    // Add stars background
    addStars();

    // Add ambient particles
    addParticles();

    // Start animation
    animate();

    // Handle window resize
    window.addEventListener('resize', onWindowResize, false);
}

function createGlobe() {
    const geometry = new THREE.SphereGeometry(50, 64, 64);

    // Create Earth-like material with cybersecurity theme
    const material = new THREE.MeshPhongMaterial({
        color: 0x1a4d6f,
        emissive: 0x001122,
        specular: 0x00d4ff,
        shininess: 25,
        wireframe: false,
        transparent: true,
        opacity: 0.9
    });

    globe = new THREE.Mesh(geometry, material);
    scene.add(globe);

    // Add wireframe overlay
    const wireframeGeometry = new THREE.SphereGeometry(50.5, 32, 32);
    const wireframeMaterial = new THREE.MeshBasicMaterial({
        color: 0x00d4ff,
        wireframe: true,
        transparent: true,
        opacity: 0.15
    });
    const wireframe = new THREE.Mesh(wireframeGeometry, wireframeMaterial);
    globe.add(wireframe);

    // Add atmosphere glow
    const glowGeometry = new THREE.SphereGeometry(55, 32, 32);
    const glowMaterial = new THREE.ShaderMaterial({
        uniforms: {
            c: { type: "f", value: 0.3 },
            p: { type: "f", value: 4.0 },
            glowColor: { type: "c", value: new THREE.Color(0x00d4ff) },
            viewVector: { type: "v3", value: camera.position }
        },
        vertexShader: `
            uniform vec3 viewVector;
            varying float intensity;
            void main() {
                vec3 vNormal = normalize(normalMatrix * normal);
                vec3 vNormel = normalize(normalMatrix * viewVector);
                intensity = pow(0.7 - dot(vNormal, vNormel), 4.0);
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            uniform vec3 glowColor;
            varying float intensity;
            void main() {
                vec3 glow = glowColor * intensity;
                gl_FragColor = vec4(glow, intensity);
            }
        `,
        side: THREE.BackSide,
        blending: THREE.AdditiveBlending,
        transparent: true
    });
    const glow = new THREE.Mesh(glowGeometry, glowMaterial);
    scene.add(glow);
}

function addLights() {
    // Ambient light
    const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
    scene.add(ambientLight);

    // Point light (sun-like)
    const pointLight = new THREE.PointLight(0xffffff, 1, 300);
    pointLight.position.set(100, 50, 100);
    scene.add(pointLight);

    // Hemisphere light
    const hemiLight = new THREE.HemisphereLight(0x00d4ff, 0x0a0e1a, 0.3);
    scene.add(hemiLight);
}

function addStars() {
    const starGeometry = new THREE.BufferGeometry();
    const starMaterial = new THREE.PointsMaterial({
        color: 0xffffff,
        size: 0.7,
        transparent: true,
        opacity: 0.8
    });

    const starVertices = [];
    for (let i = 0; i < 3000; i++) {
        const x = (Math.random() - 0.5) * 400;
        const y = (Math.random() - 0.5) * 400;
        const z = (Math.random() - 0.5) * 400;
        starVertices.push(x, y, z);
    }

    starGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starVertices, 3));
    const stars = new THREE.Points(starGeometry, starMaterial);
    scene.add(stars);
}

function addParticles() {
    const particleGeometry = new THREE.BufferGeometry();
    const particleMaterial = new THREE.PointsMaterial({
        color: 0x00d4ff,
        size: 1,
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending
    });

    const particleVertices = [];
    for (let i = 0; i < 500; i++) {
        const radius = 60 + Math.random() * 30;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.random() * Math.PI;

        const x = radius * Math.sin(phi) * Math.cos(theta);
        const y = radius * Math.sin(phi) * Math.sin(theta);
        const z = radius * Math.cos(phi);

        particleVertices.push(x, y, z);
    }

    particleGeometry.setAttribute('position', new THREE.Float32BufferAttribute(particleVertices, 3));
    const particles = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particles);
}

function addLoginMarker(lat, lon, riskLevel) {
    // Convert lat/lon to 3D coordinates
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);

    const radius = 51;
    const x = -radius * Math.sin(phi) * Math.cos(theta);
    const y = radius * Math.cos(phi);
    const z = radius * Math.sin(phi) * Math.sin(theta);

    // Color based on risk level
    const colors = {
        'safe': 0x10b981,
        'low': 0x3b82f6,
        'medium': 0xf59e0b,
        'high': 0xfb923c,
        'critical': 0xdc2626
    };

    const color = colors[riskLevel] || 0x00d4ff;

    // Create marker (pulsing sphere)
    const geometry = new THREE.SphereGeometry(0.8, 16, 16);
    const material = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.8
    });

    const marker = new THREE.Mesh(geometry, material);
    marker.position.set(x, y, z);

    // Add pulse animation
    marker.userData = {
        scale: 1,
        scaleSpeed: 0.02,
        riskLevel: riskLevel
    };

    globe.add(marker);
    loginMarkers.push(marker);

    // Create expanding ring effect
    const ringGeometry = new THREE.RingGeometry(0.5, 1, 32);
    const ringMaterial = new THREE.MeshBasicMaterial({
        color: color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.6
    });

    const ring = new THREE.Mesh(ringGeometry, ringMaterial);
    ring.position.set(x, y, z);
    ring.lookAt(0, 0, 0);

    ring.userData = {
        opacity: 0.6,
        scale: 1,
        fadeSpeed: 0.02
    };

    globe.add(ring);
    loginMarkers.push(ring);

    // Clean up old markers (keep last 100)
    if (loginMarkers.length > 100) {
        const removed = loginMarkers.shift();
        globe.remove(removed);
        if (removed.geometry) removed.geometry.dispose();
        if (removed.material) removed.material.dispose();
    }
}

function animate() {
    requestAnimationFrame(animate);

    // Update controls
    controls.update();

    // Animate markers
    loginMarkers.forEach(marker => {
        if (marker.userData.scale !== undefined) {
            // Pulse animation
            marker.userData.scale += marker.userData.scaleSpeed;
            if (marker.userData.scale > 1.3 || marker.userData.scale < 0.7) {
                marker.userData.scaleSpeed *= -1;
            }
            marker.scale.set(marker.userData.scale, marker.userData.scale, marker.userData.scale);
        }

        if (marker.userData.opacity !== undefined) {
            // Fade out rings
            marker.userData.opacity -= marker.userData.fadeSpeed;
            marker.userData.scale += 0.05;
            marker.material.opacity = marker.userData.opacity;
            marker.scale.set(marker.userData.scale, marker.userData.scale, 1);

            if (marker.userData.opacity <= 0) {
                globe.remove(marker);
                loginMarkers.splice(loginMarkers.indexOf(marker), 1);
            }
        }
    });

    renderer.render(scene, camera);
}

function onWindowResize() {
    const container = document.getElementById('globeContainer');
    const width = container.clientWidth;
    const height = container.clientHeight;

    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
}

function toggleAutoRotate() {
    autoRotate = !autoRotate;
    controls.autoRotate = autoRotate;
}

// Initialize globe when page loads
window.addEventListener('DOMContentLoaded', initGlobe);

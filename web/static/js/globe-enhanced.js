/**
 * Enhanced 3D Globe Visualization with Advanced Animations
 * Multiple layers of visual effects for cybersecurity monitoring
 */

let scene, camera, renderer, globe, controls;
let loginMarkers = [];
let autoRotate = true;
let threatConnections = [];
let pulseRings = [];
let dataStreams = [];
let satellites = [];
let attackWaves = [];

// Colors for different threat levels
const THREAT_COLORS = {
    'safe': 0x10b981,
    'low': 0x3b82f6,
    'medium': 0xf59e0b,
    'high': 0xfb923c,
    'critical': 0xdc2626
};

function initGlobe() {
    const container = document.getElementById('globeContainer');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Create scene with fog
    scene = new THREE.Scene();
    scene.fog = new THREE.Fog(0x0a0e1a, 100, 400);

    // Create camera
    camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 150;

    // Create renderer with better settings
    renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "high-performance"
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setClearColor(0x0a0e1a, 0);
    container.appendChild(renderer.domElement);

    // Add controls
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.autoRotate = autoRotate;
    controls.autoRotateSpeed = 0.5;
    controls.minDistance = 80;
    controls.maxDistance = 300;

    // Create multi-layered globe
    createEnhancedGlobe();

    // Add enhanced lighting
    addEnhancedLights();

    // Add stars background
    addEnhancedStars();

    // Add orbital satellites
    addSatellites();

    // Add data stream particles
    addDataStreams();

    // Add atmospheric effects
    addAtmosphere();

    // Start animation
    animate();

    // Handle window resize
    window.addEventListener('resize', onWindowResize, false);
}

function createEnhancedGlobe() {
    const globeGroup = new THREE.Group();

    // Main globe with gradient
    const geometry = new THREE.SphereGeometry(50, 128, 128);

    // Custom shader material for animated globe
    const material = new THREE.ShaderMaterial({
        uniforms: {
            time: { value: 0 },
            color1: { value: new THREE.Color(0x1a4d6f) },
            color2: { value: new THREE.Color(0x0a2332) }
        },
        vertexShader: `
            varying vec2 vUv;
            varying vec3 vPosition;
            void main() {
                vUv = uv;
                vPosition = position;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            uniform float time;
            uniform vec3 color1;
            uniform vec3 color2;
            varying vec2 vUv;
            varying vec3 vPosition;

            void main() {
                float gradient = vPosition.y / 50.0 * 0.5 + 0.5;
                vec3 color = mix(color2, color1, gradient);

                // Animated scan lines
                float scanline = sin(vUv.y * 50.0 + time) * 0.05;
                color += scanline;

                gl_FragColor = vec4(color, 0.95);
            }
        `,
        transparent: true
    });

    globe = new THREE.Mesh(geometry, material);
    globeGroup.add(globe);

    // Hexagonal grid overlay
    const hexGeometry = new THREE.SphereGeometry(50.5, 32, 32);
    const hexMaterial = new THREE.MeshBasicMaterial({
        color: 0x00d4ff,
        wireframe: true,
        transparent: true,
        opacity: 0.15
    });
    const hexMesh = new THREE.Mesh(hexGeometry, hexMaterial);
    globeGroup.add(hexMesh);

    // Animated wireframe
    const wireGeometry = new THREE.SphereGeometry(51, 24, 24);
    const wireMaterial = new THREE.MeshBasicMaterial({
        color: 0x00d4ff,
        wireframe: true,
        transparent: true,
        opacity: 0.1
    });
    const wireMesh = new THREE.Mesh(wireGeometry, wireMaterial);
    wireMesh.userData = { rotationSpeed: 0.001 };
    globeGroup.add(wireMesh);

    // Energy field layer
    const fieldGeometry = new THREE.SphereGeometry(52, 32, 32);
    const fieldMaterial = new THREE.ShaderMaterial({
        uniforms: {
            time: { value: 0 }
        },
        vertexShader: `
            varying vec3 vNormal;
            void main() {
                vNormal = normalize(normalMatrix * normal);
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            uniform float time;
            varying vec3 vNormal;
            void main() {
                float intensity = pow(0.6 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 2.0);
                vec3 glow = vec3(0.0, 0.8, 1.0) * intensity;
                float pulse = sin(time * 2.0) * 0.3 + 0.7;
                gl_FragColor = vec4(glow * pulse, intensity * 0.5);
            }
        `,
        side: THREE.BackSide,
        blending: THREE.AdditiveBlending,
        transparent: true
    });
    const fieldMesh = new THREE.Mesh(fieldGeometry, fieldMaterial);
    globeGroup.add(fieldMesh);

    scene.add(globeGroup);

    // Store for animation
    globe.userData = {
        material: material,
        fieldMaterial: fieldMaterial,
        wireMesh: wireMesh
    };
}

function addEnhancedLights() {
    // Ambient light
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    scene.add(ambientLight);

    // Directional lights from multiple angles
    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight1.position.set(100, 50, 100);
    scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x00d4ff, 0.4);
    dirLight2.position.set(-100, -50, -100);
    scene.add(dirLight2);

    // Point lights for dramatic effect
    const pointLight1 = new THREE.PointLight(0x00d4ff, 1, 200);
    pointLight1.position.set(0, 100, 0);
    scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0xa855f7, 0.8, 200);
    pointLight2.position.set(0, -100, 0);
    scene.add(pointLight2);

    // Hemisphere light
    const hemiLight = new THREE.HemisphereLight(0x00d4ff, 0x0a0e1a, 0.5);
    scene.add(hemiLight);
}

function addEnhancedStars() {
    // Create multiple star layers for depth
    for (let layer = 0; layer < 3; layer++) {
        const starGeometry = new THREE.BufferGeometry();
        const starMaterial = new THREE.PointsMaterial({
            color: 0xffffff,
            size: 0.5 + layer * 0.3,
            transparent: true,
            opacity: 0.8 - layer * 0.2,
            blending: THREE.AdditiveBlending
        });

        const starVertices = [];
        const starCount = 2000 - layer * 500;

        for (let i = 0; i < starCount; i++) {
            const radius = 200 + layer * 50;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.random() * Math.PI;

            const x = radius * Math.sin(phi) * Math.cos(theta);
            const y = radius * Math.sin(phi) * Math.sin(theta);
            const z = radius * Math.cos(phi);

            starVertices.push(x, y, z);
        }

        starGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starVertices, 3));
        const stars = new THREE.Points(starGeometry, starMaterial);
        stars.userData = { rotationSpeed: 0.0001 * (layer + 1) };
        scene.add(stars);
    }
}

function addSatellites() {
    // Create orbital satellites
    for (let i = 0; i < 5; i++) {
        const satGeometry = new THREE.OctahedronGeometry(1.5);
        const satMaterial = new THREE.MeshPhongMaterial({
            color: 0x00d4ff,
            emissive: 0x00d4ff,
            emissiveIntensity: 0.5,
            shininess: 100
        });

        const satellite = new THREE.Mesh(satGeometry, satMaterial);

        // Random orbital parameters
        const distance = 70 + Math.random() * 30;
        const speed = 0.001 + Math.random() * 0.002;
        const angle = Math.random() * Math.PI * 2;
        const inclination = (Math.random() - 0.5) * Math.PI * 0.5;

        satellite.userData = {
            distance: distance,
            speed: speed,
            angle: angle,
            inclination: inclination
        };

        // Add glow
        const glowGeometry = new THREE.OctahedronGeometry(2);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: 0x00d4ff,
            transparent: true,
            opacity: 0.3,
            blending: THREE.AdditiveBlending
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        satellite.add(glow);

        satellites.push(satellite);
        scene.add(satellite);
    }
}

function addDataStreams() {
    // Flowing data particles around globe
    for (let i = 0; i < 100; i++) {
        const particleGeometry = new THREE.SphereGeometry(0.3);
        const particleMaterial = new THREE.MeshBasicMaterial({
            color: Math.random() > 0.5 ? 0x00d4ff : 0xa855f7,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending
        });

        const particle = new THREE.Mesh(particleGeometry, particleMaterial);

        // Random stream path
        const radius = 55 + Math.random() * 25;
        const angle = Math.random() * Math.PI * 2;
        const height = (Math.random() - 0.5) * 100;

        particle.userData = {
            radius: radius,
            angle: angle,
            height: height,
            speed: 0.01 + Math.random() * 0.02
        };

        dataStreams.push(particle);
        scene.add(particle);
    }
}

function addAtmosphere() {
    // Multi-layer atmosphere
    const atmosphereGeometry = new THREE.SphereGeometry(56, 64, 64);
    const atmosphereMaterial = new THREE.ShaderMaterial({
        uniforms: {
            c: { type: "f", value: 0.4 },
            p: { type: "f", value: 3.5 },
            glowColor: { type: "c", value: new THREE.Color(0x00d4ff) },
            viewVector: { type: "v3", value: camera.position }
        },
        vertexShader: `
            uniform vec3 viewVector;
            varying float intensity;
            void main() {
                vec3 vNormal = normalize(normalMatrix * normal);
                vec3 vNormel = normalize(normalMatrix * viewVector);
                intensity = pow(c - dot(vNormal, vNormel), p);
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            uniform vec3 glowColor;
            varying float intensity;
            void main() {
                vec3 glow = glowColor * intensity;
                gl_FragColor = vec4(glow, intensity * 0.8);
            }
        `,
        side: THREE.BackSide,
        blending: THREE.AdditiveBlending,
        transparent: true
    });

    const atmosphere = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
    scene.add(atmosphere);
}

function addLoginMarker(lat, lon, riskLevel) {
    // Convert lat/lon to 3D coordinates
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);
    const radius = 51;

    const x = -radius * Math.sin(phi) * Math.cos(theta);
    const y = radius * Math.cos(phi);
    const z = radius * Math.sin(phi) * Math.sin(theta);

    const color = THREAT_COLORS[riskLevel] || 0x00d4ff;

    // Create threat spike (vertical pillar)
    const severity = riskLevel === 'critical' ? 15 : riskLevel === 'high' ? 10 : 5;
    const spikeGeometry = new THREE.CylinderGeometry(0.5, 1, severity, 8);
    const spikeMaterial = new THREE.MeshPhongMaterial({
        color: color,
        emissive: color,
        emissiveIntensity: 0.5,
        transparent: true,
        opacity: 0.8
    });

    const spike = new THREE.Mesh(spikeGeometry, spikeMaterial);
    spike.position.set(x, y, z);
    spike.lookAt(0, 0, 0);
    spike.rotateX(Math.PI / 2);

    spike.userData = {
        growSpeed: 0.1,
        targetScale: 1,
        currentScale: 0
    };

    globe.add(spike);
    loginMarkers.push(spike);

    // Create pulsing marker at base
    const markerGeometry = new THREE.SphereGeometry(1, 16, 16);
    const markerMaterial = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending
    });

    const marker = new THREE.Mesh(markerGeometry, markerMaterial);
    marker.position.set(x, y, z);
    marker.userData = {
        scale: 1,
        scaleSpeed: 0.03,
        riskLevel: riskLevel
    };

    globe.add(marker);
    loginMarkers.push(marker);

    // Create expanding pulse rings
    for (let i = 0; i < 3; i++) {
        setTimeout(() => {
            createPulseRing(x, y, z, color);
        }, i * 300);
    }

    // Create attack wave for high risk
    if (riskLevel === 'critical' || riskLevel === 'high') {
        createAttackWave(x, y, z, color);
    }

    // Create threat connection lines
    if (Math.random() > 0.5) {
        createThreatConnection(x, y, z, color);
    }

    // Cleanup old markers
    if (loginMarkers.length > 150) {
        const removed = loginMarkers.shift();
        globe.remove(removed);
        if (removed.geometry) removed.geometry.dispose();
        if (removed.material) removed.material.dispose();
    }
}

function createPulseRing(x, y, z, color) {
    const ringGeometry = new THREE.RingGeometry(0.5, 1.5, 32);
    const ringMaterial = new THREE.MeshBasicMaterial({
        color: color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending
    });

    const ring = new THREE.Mesh(ringGeometry, ringMaterial);
    ring.position.set(x, y, z);
    ring.lookAt(0, 0, 0);

    ring.userData = {
        opacity: 0.8,
        scale: 1,
        fadeSpeed: 0.02,
        expandSpeed: 0.08
    };

    globe.add(ring);
    pulseRings.push(ring);
}

function createAttackWave(x, y, z, color) {
    const waveGeometry = new THREE.SphereGeometry(2, 32, 32, 0, Math.PI * 2, 0, Math.PI / 2);
    const waveMaterial = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.6,
        side: THREE.DoubleSide,
        blending: THREE.AdditiveBlending
    });

    const wave = new THREE.Mesh(waveGeometry, waveMaterial);
    wave.position.set(x, y, z);
    wave.lookAt(0, 0, 0);

    wave.userData = {
        opacity: 0.6,
        scale: 0.1,
        maxScale: 3,
        expandSpeed: 0.05,
        fadeSpeed: 0.015
    };

    globe.add(wave);
    attackWaves.push(wave);
}

function createThreatConnection(x, y, z, color) {
    // Random target point
    const targetAngle = Math.random() * Math.PI * 2;
    const targetPhi = Math.random() * Math.PI;
    const radius = 51;

    const tx = -radius * Math.sin(targetPhi) * Math.cos(targetAngle);
    const ty = radius * Math.cos(targetPhi);
    const tz = radius * Math.sin(targetPhi) * Math.sin(targetAngle);

    // Create curved line between points
    const curve = new THREE.QuadraticBezierCurve3(
        new THREE.Vector3(x, y, z),
        new THREE.Vector3((x + tx) / 2 * 1.2, (y + ty) / 2 * 1.2, (z + tz) / 2 * 1.2),
        new THREE.Vector3(tx, ty, tz)
    );

    const points = curve.getPoints(50);
    const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
    const lineMaterial = new THREE.LineBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.4,
        blending: THREE.AdditiveBlending
    });

    const line = new THREE.Line(lineGeometry, lineMaterial);
    line.userData = {
        opacity: 0.4,
        fadeSpeed: 0.01,
        lifetime: 200
    };

    globe.add(line);
    threatConnections.push(line);
}

function animate() {
    requestAnimationFrame(animate);

    const time = Date.now() * 0.001;

    // Update controls
    controls.update();

    // Animate globe shader
    if (globe.userData.material) {
        globe.userData.material.uniforms.time.value = time;
        globe.userData.fieldMaterial.uniforms.time.value = time;
    }

    // Rotate wireframe
    if (globe.userData.wireMesh) {
        globe.userData.wireMesh.rotation.y += globe.userData.wireMesh.userData.rotationSpeed;
    }

    // Animate satellites
    satellites.forEach(sat => {
        sat.userData.angle += sat.userData.speed;
        sat.position.x = Math.cos(sat.userData.angle) * sat.userData.distance;
        sat.position.z = Math.sin(sat.userData.angle) * sat.userData.distance;
        sat.position.y = Math.sin(sat.userData.angle) * sat.userData.distance * Math.sin(sat.userData.inclination);
        sat.rotation.y += 0.02;
    });

    // Animate data streams
    dataStreams.forEach(particle => {
        particle.userData.angle += particle.userData.speed;
        particle.position.x = Math.cos(particle.userData.angle) * particle.userData.radius;
        particle.position.z = Math.sin(particle.userData.angle) * particle.userData.radius;
        particle.position.y = particle.userData.height + Math.sin(particle.userData.angle * 3) * 10;
    });

    // Animate markers
    loginMarkers.forEach(marker => {
        if (marker.geometry.type === 'CylinderGeometry') {
            // Grow spike
            if (marker.userData.currentScale < marker.userData.targetScale) {
                marker.userData.currentScale += marker.userData.growSpeed;
                marker.scale.y = marker.userData.currentScale;
            }
        } else {
            // Pulse sphere marker
            marker.userData.scale += marker.userData.scaleSpeed;
            if (marker.userData.scale > 1.4 || marker.userData.scale < 0.8) {
                marker.userData.scaleSpeed *= -1;
            }
            marker.scale.set(marker.userData.scale, marker.userData.scale, marker.userData.scale);
        }
    });

    // Animate pulse rings
    pulseRings.forEach((ring, index) => {
        ring.userData.scale += ring.userData.expandSpeed;
        ring.userData.opacity -= ring.userData.fadeSpeed;
        ring.scale.set(ring.userData.scale, ring.userData.scale, 1);
        ring.material.opacity = ring.userData.opacity;

        if (ring.userData.opacity <= 0) {
            globe.remove(ring);
            ring.geometry.dispose();
            ring.material.dispose();
            pulseRings.splice(index, 1);
        }
    });

    // Animate attack waves
    attackWaves.forEach((wave, index) => {
        if (wave.userData.scale < wave.userData.maxScale) {
            wave.userData.scale += wave.userData.expandSpeed;
        }
        wave.userData.opacity -= wave.userData.fadeSpeed;
        wave.scale.set(wave.userData.scale, wave.userData.scale, wave.userData.scale);
        wave.material.opacity = wave.userData.opacity;

        if (wave.userData.opacity <= 0) {
            globe.remove(wave);
            wave.geometry.dispose();
            wave.material.dispose();
            attackWaves.splice(index, 1);
        }
    });

    // Animate threat connections
    threatConnections.forEach((conn, index) => {
        conn.userData.lifetime--;
        conn.userData.opacity -= conn.userData.fadeSpeed;
        conn.material.opacity = conn.userData.opacity;

        if (conn.userData.lifetime <= 0) {
            globe.remove(conn);
            conn.geometry.dispose();
            conn.material.dispose();
            threatConnections.splice(index, 1);
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

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGlobe);
} else {
    initGlobe();
}

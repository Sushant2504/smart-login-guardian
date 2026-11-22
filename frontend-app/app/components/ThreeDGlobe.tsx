'use client';

import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sphere, MeshDistortMaterial } from '@react-three/drei';
import * as THREE from 'three';

interface ThreatMarker {
  country: string;
  count: number;
}

function Globe({ threats }: { threats: ThreatMarker[] }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const particlesRef = useRef<THREE.Points>(null);

  // Create threat particles
  const particles = useMemo(() => {
    const positions: number[] = [];
    const colors: number[] = [];

    for (let i = 0; i < 1000; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const radius = 3 + Math.random() * 0.5;

      positions.push(
        radius * Math.sin(phi) * Math.cos(theta),
        radius * Math.sin(phi) * Math.sin(theta),
        radius * Math.cos(phi)
      );

      // Random colors between purple and red
      const color = new THREE.Color();
      color.setHSL(Math.random() * 0.3, 1, 0.5);
      colors.push(color.r, color.g, color.b);
    }

    return { positions: new Float32Array(positions), colors: new Float32Array(colors) };
  }, []);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.002;
    }
    if (particlesRef.current) {
      particlesRef.current.rotation.y += 0.001;
    }
  });

  return (
    <group>
      {/* Main Globe */}
      <Sphere ref={meshRef} args={[2.5, 64, 64]}>
        <MeshDistortMaterial
          color="#4c1d95"
          attach="material"
          distort={0.3}
          speed={1.5}
          roughness={0.4}
          metalness={0.8}
        />
      </Sphere>

      {/* Threat Particles */}
      <points ref={particlesRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={particles.positions.length / 3}
            array={particles.positions}
            itemSize={3}
          />
          <bufferAttribute
            attach="attributes-color"
            count={particles.colors.length / 3}
            array={particles.colors}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial size={0.05} vertexColors transparent opacity={0.8} />
      </points>

      {/* Glow Effect */}
      <Sphere args={[2.52, 64, 64]}>
        <meshBasicMaterial color="#8b5cf6" transparent opacity={0.1} side={THREE.BackSide} />
      </Sphere>
    </group>
  );
}

export default function ThreeDGlobe({ threats }: { threats: ThreatMarker[] }) {
  return (
    <div className="w-full h-full">
      <Canvas camera={{ position: [0, 0, 8], fov: 45 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#8b5cf6" />
        <Globe threats={threats} />
        <OrbitControls
          enableZoom={true}
          enablePan={false}
          minDistance={5}
          maxDistance={15}
          autoRotate
          autoRotateSpeed={0.5}
        />
      </Canvas>

      {/* Threat Legend */}
      <div className="absolute bottom-4 left-4 bg-black/50 backdrop-blur-md rounded-lg p-3 text-white text-xs space-y-1">
        <div className="font-semibold mb-2">Top Threat Origins</div>
        {threats.slice(0, 5).map((threat, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span>{threat.country}: {threat.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

function Leaf({
  angle,
  height,
  scale,
  phase,
}: {
  angle: number;
  height: number;
  scale: number;
  phase: number;
}) {
  const ref = useRef<THREE.Group>(null);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (ref.current) {
      ref.current.rotation.z = Math.sin(t * 0.9 + phase) * 0.09;
      ref.current.rotation.y = angle + Math.sin(t * 0.5 + phase) * 0.06;
    }
  });

  const shape = useMemo(() => {
    const s = new THREE.Shape();
    s.moveTo(0, 0);
    s.bezierCurveTo(0.35, 0.22, 0.85, 0.3, 1.15, 0);
    s.bezierCurveTo(0.85, -0.3, 0.35, -0.22, 0, 0);
    return s;
  }, []);

  return (
    <group ref={ref} position={[0, height, 0]} rotation={[0, angle, 0]}>
      <mesh rotation={[-Math.PI / 2.4, 0, 0.3]} scale={scale}>
        <shapeGeometry args={[shape, 24]} />
        <meshStandardMaterial
          color="#4c9a53"
          side={THREE.DoubleSide}
          roughness={0.55}
          metalness={0.02}
        />
      </mesh>
    </group>
  );
}

function Plant() {
  const group = useRef<THREE.Group>(null);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (group.current) {
      group.current.rotation.y = Math.sin(t * 0.25) * 0.35;
      group.current.position.y = Math.sin(t * 0.8) * 0.03 - 0.35;
    }
  });

  return (
    <group ref={group}>
      {/* stem */}
      <mesh position={[0, 0.55, 0]}>
        <cylinderGeometry args={[0.035, 0.055, 1.2, 12]} />
        <meshStandardMaterial color="#3f7d43" roughness={0.7} />
      </mesh>
      {/* leaves */}
      <Leaf angle={0} height={1.05} scale={0.55} phase={0} />
      <Leaf angle={Math.PI * 0.66} height={0.85} scale={0.62} phase={1.3} />
      <Leaf angle={Math.PI * 1.33} height={0.62} scale={0.5} phase={2.4} />
      <Leaf angle={Math.PI * 0.3} height={0.42} scale={0.4} phase={3.1} />
      {/* pot */}
      <mesh position={[0, -0.18, 0]}>
        <cylinderGeometry args={[0.32, 0.24, 0.36, 24]} />
        <meshStandardMaterial color="#8a6a4b" roughness={0.85} />
      </mesh>
      <mesh position={[0, 0.01, 0]}>
        <cylinderGeometry args={[0.3, 0.3, 0.04, 24]} />
        <meshStandardMaterial color="#4a3826" roughness={1} />
      </mesh>
    </group>
  );
}

export default function PlantScene() {
  return (
    <Canvas camera={{ position: [0, 0.9, 3.1], fov: 42 }} dpr={[1, 2]}>
      <ambientLight intensity={0.75} />
      <directionalLight position={[3, 4, 2]} intensity={1.15} />
      <directionalLight position={[-3, 2, -2]} intensity={0.35} color="#bfe6c2" />
      <Plant />
    </Canvas>
  );
}

import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import type { Group } from 'three';

export function NoiseOverlay() {
  const ref = useRef<Group>(null);
  const noise = useMemo(
    () =>
      Array.from({ length: 2000 }, (_, index) => ({
        x: Math.random(),
        y: Math.random(),
        size: 0.01 + Math.random() * 0.02,
        opacity: 0.12 + Math.random() * 0.18,
        key: index,
      })),
    [],
  );

  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.z = clock.getElapsedTime() * 0.05;
  });

  return (
    <group ref={ref} position={[0, 0, -6]}>
      {noise.map((point) => (
        <mesh key={point.key} position={[point.x * 16 - 8, point.y * 9 - 4.5, 0]}>
          <planeGeometry args={[point.size, point.size]} />
          <meshBasicMaterial color="#FFFFFF" transparent opacity={point.opacity} />
        </mesh>
      ))}
    </group>
  );
}

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import type { Group } from 'three';
import { themeVariants, type ThemeName } from './themeVariants';

interface LightRaysProps {
  theme: ThemeName;
}

export function LightRays({ theme }: LightRaysProps) {
  const ref = useRef<Group>(null);
  const variant = themeVariants[theme];

  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.z = clock.getElapsedTime() * 0.08;
  });

  return (
    <group ref={ref} position={[0, 2.5, -3.5]}>
      {Array.from({ length: 7 }).map((_, index) => (
        <mesh key={index} rotation={[0, 0, (-Math.PI / 18) * index]} position={[index * 0.9 - 3, 0, 0]}>
          <planeGeometry args={[0.8, 8, 1, 1]} />
          <meshBasicMaterial color={variant.ray} transparent opacity={0.12} blending={2} />
        </mesh>
      ))}
    </group>
  );
}

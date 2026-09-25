import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import type { Mesh } from 'three';
import { themeVariants, type ThemeName } from './themeVariants';

interface MeshGradientProps {
  theme: ThemeName;
}

export function MeshGradient({ theme }: MeshGradientProps) {
  const ref = useRef<Mesh>(null);
  const variant = themeVariants[theme];

  const colors = useMemo(
    () => [variant.planeA, variant.planeB, variant.planeA, variant.planeB],
    [variant.planeA, variant.planeB],
  );

  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.z = clock.getElapsedTime() * 0.09;
    ref.current.position.z = -4.5 + Math.sin(clock.getElapsedTime() * 0.5) * 0.25;
  });

  return (
    <mesh ref={ref} position={[0, 0, -5]} rotation={[0.35, 0.2, 0]}>
      <planeGeometry args={[18, 10, 24, 24]} />
      <meshStandardMaterial
        color={variant.backgroundSecondary}
        emissive={variant.backgroundSecondary}
        emissiveIntensity={0.2}
        transparent
        opacity={0.5}
        wireframe={false}
      />
    </mesh>
  );
}

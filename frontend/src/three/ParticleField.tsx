import { useMemo, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import type { Group } from 'three';
import { themeVariants, type ThemeName } from './themeVariants';

interface ParticleFieldProps {
  theme: ThemeName;
  intensity?: number;
}

export function ParticleField({ theme, intensity = 1 }: ParticleFieldProps) {
  const ref = useRef<Group>(null);
  const variant = themeVariants[theme];

  const positions = useMemo(() => {
    const points: number[] = [];
    const count = 2200;

    for (let i = 0; i < count; i += 1) {
      points.push((Math.random() - 0.5) * 20);
      points.push((Math.random() - 0.5) * 12);
      points.push((Math.random() - 0.5) * 18);
    }

    return new Float32Array(points);
  }, []);

  useFrame(({ clock }) => {
    if (!ref.current) return;
    ref.current.rotation.y = clock.getElapsedTime() * 0.06 * intensity;
    ref.current.rotation.x = Math.sin(clock.getElapsedTime() * 0.4) * 0.25;
  });

  return (
    <group ref={ref}>
      <points>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={positions.length / 3}
            array={positions}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          color={variant.particle}
          size={0.04}
          transparent
          opacity={0.8}
          depthWrite={false}
          sizeAttenuation
        />
      </points>
    </group>
  );
}

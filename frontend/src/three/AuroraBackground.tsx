'use client';

import { useRef, useEffect, useMemo, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { ShaderMaterial, Vector2, Clock } from 'three';
import { vertexShader, fragmentShader } from './shaders/auroraShaders';

interface AuroraBackgroundProps {
  intensity?: number;
  speed?: number;
  quality?: 'low' | 'medium' | 'high';
  className?: string;
  fallback?: React.ReactNode;
}

function AuroraMesh({ intensity = 1, speed = 1, quality = 'medium' }) {
  const { size, viewport } = useThree();
  const clock = useMemo(() => new Clock(), []);
  const mouse = useRef(new Vector2(0, 0));
  const qualityMap = { low: 0, medium: 1, high: 2 } as const;
  const qualityLevel = qualityMap[quality as keyof typeof qualityMap];

  const material = useMemo(() => new ShaderMaterial({
    vertexShader,
    fragmentShader,
    uniforms: {
      uTime: { value: 0 },
      uResolution: { value: new Vector2(size.width, size.height) },
      uMouse: { value: mouse.current },
      uIntensity: { value: intensity },
      uSpeed: { value: speed },
      uQuality: { value: qualityLevel },
    },
    transparent: true,
    depthWrite: false,
  }), [intensity, speed, qualityLevel]);

  useFrame(() => {
    material.uniforms.uTime.value = clock.getElapsedTime();
  });

  useEffect(() => {
    const handleResize = () => {
      material.uniforms.uResolution.value.set(size.width, size.height);
    };
    handleResize();
    return () => material.dispose();
  }, [material, size]);

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      mouse.current.x = (event.clientX / viewport.width) * 2 - 1;
      mouse.current.y = -(event.clientY / viewport.height) * 2 + 1;
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [viewport]);

  return (
    <mesh>
      <planeGeometry args={[2, 2]} />
      <primitive object={material} />
    </mesh>
  );
}

function AuroraCanvas({ intensity, speed, quality, fallback }: Omit<AuroraBackgroundProps, 'className'>) {
  const [webglError, setWebglError] = useState(false);

  useEffect(() => {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
    if (!gl) {
      setWebglError(true);
    }
  }, []);

  if (webglError) {
    return <>{fallback}</>;
  }

  return (
    <Canvas
      camera={{ position: [0, 0, 1], fov: 50 }}
      style={{ position: 'absolute', inset: 0, zIndex: 0 }}
      gl={{ alpha: true, antialias: false, preserveDrawingBuffer: false, powerPreference: 'high-performance' }}
      onCreated={({ gl }) => {
        gl.extensions.get('EXT_color_buffer_float');
        gl.extensions.get('OES_texture_float_linear');
      }}
    >
      <color attach="background" args={['#0a0a0f']} />
      <fog attach="fog" args={['#0a0a0f', 1, 10]} />
      <AuroraMesh intensity={intensity} speed={speed} quality={quality} />
    </Canvas>
  );
}

export function AuroraBackground({
  intensity = 0.6,
  speed = 0.8,
  quality = 'medium',
  className = '',
  fallback,
}: AuroraBackgroundProps) {
  const [mounted, setMounted] = useState(false);
  const prefersReducedMotion = typeof window !== 'undefined' 
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches 
    : false;

  useEffect(() => {
    setMounted(true);
  }, []);

  const effectiveQuality = prefersReducedMotion ? 'low' : quality;
  const effectiveIntensity = prefersReducedMotion ? 0 : intensity;
  const effectiveSpeed = prefersReducedMotion ? 0 : speed;

  const defaultFallback = (
    <div className="aurora-fallback" style={{
      position: 'absolute',
      inset: 0,
      background: 'linear-gradient(135deg, #0a0a0f 0%, #11131a 50%, #0a0a0f 100%)',
      zIndex: 0,
    }}>
      <div style={{
        position: 'absolute',
        inset: 0,
        background: 'radial-gradient(ellipse at 30% 20%, rgba(0, 212, 170, 0.08) 0%, transparent 60%), radial-gradient(ellipse at 70% 80%, rgba(138, 43, 226, 0.06) 0%, transparent 50%)',
      }} />
    </div>
  );

  if (!mounted) {
    return <div className={className} style={{ position: 'relative', minHeight: '100vh' }}>{defaultFallback}</div>;
  }

  return (
    <div className={className} style={{ position: 'relative', minHeight: '100vh', overflow: 'hidden' }}>
      <AuroraCanvas
        intensity={effectiveIntensity}
        speed={effectiveSpeed}
        quality={effectiveQuality}
        fallback={fallback || defaultFallback}
      />
    </div>
  );
}

export function AuroraBackgroundSimple({
  className = '',
  fallback,
}: Pick<AuroraBackgroundProps, 'className' | 'fallback'>) {
  return <AuroraBackground className={className} fallback={fallback} intensity={0.5} speed={0.6} quality="medium" />;
}
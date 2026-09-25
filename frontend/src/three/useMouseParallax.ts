import { useEffect, useRef } from 'react';

export function useMouseParallax() {
  const target = useRef({ x: 0, y: 0 });
  const current = useRef({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      const x = (event.clientX / window.innerWidth) * 2 - 1;
      const y = (event.clientY / window.innerHeight) * 2 - 1;
      target.current = { x, y };
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return {
    get offset() {
      current.current.x += (target.current.x - current.current.x) * 0.04;
      current.current.y += (target.current.y - current.current.y) * 0.04;
      return current.current;
    },
  };
}

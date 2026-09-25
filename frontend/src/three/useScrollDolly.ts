import { useEffect, useRef } from 'react';

export function useScrollDolly() {
  const target = useRef(0);
  const current = useRef(0);

  useEffect(() => {
    const handleScroll = () => {
      const next = window.scrollY / Math.max(window.innerHeight, 1);
      target.current = next;
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return {
    get depth() {
      current.current += (target.current - current.current) * 0.08;
      return current.current;
    },
  };
}

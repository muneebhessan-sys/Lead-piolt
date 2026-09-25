export type ThemeName = 'OBSIDIAN' | 'AURORA';

export type ThemeVariant = {
  id: ThemeName;
  background: string;
  backgroundSecondary: string;
  backgroundTertiary: string;
  panel: string;
  panelStrong: string;
  text: string;
  muted: string;
  border: string;
  glow: string;
  particle: string;
  ray: string;
  planeA: string;
  planeB: string;
};

export const themeVariants: Record<ThemeName, ThemeVariant> = {
  OBSIDIAN: {
    id: 'OBSIDIAN',
    background: '#0A0A0A',
    backgroundSecondary: '#111111',
    backgroundTertiary: '#1A1A1A',
    panel: 'rgba(255,255,255,0.06)',
    panelStrong: 'rgba(255,255,255,0.08)',
    text: '#FFFFFF',
    muted: 'rgba(255,255,255,0.72)',
    border: 'rgba(255,255,255,0.12)',
    glow: 'rgba(255,255,255,0.18)',
    particle: '#FFFFFF',
    ray: '#FFFFFF',
    planeA: '#0A0A0A',
    planeB: '#F5F5F7',
  },
  AURORA: {
    id: 'AURORA',
    background: '#F5F5F7',
    backgroundSecondary: '#EAEAEA',
    backgroundTertiary: '#DDDDDD',
    panel: 'rgba(0,0,0,0.04)',
    panelStrong: 'rgba(0,0,0,0.07)',
    text: '#1A1A1A',
    muted: 'rgba(26,26,26,0.7)',
    border: 'rgba(0,0,0,0.08)',
    glow: 'rgba(0,0,0,0.12)',
    particle: '#1A1A1A',
    ray: '#D9D9D9',
    planeA: '#F5F5F7',
    planeB: '#111111',
  },
};

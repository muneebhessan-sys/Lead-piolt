import { themeVariants, type ThemeName } from './themeVariants';

interface BackgroundProps {
  theme?: ThemeName;
  reducedMotion?: boolean;
}

export function Background({ theme = 'OBSIDIAN', reducedMotion = false }: BackgroundProps) {
  const variant = themeVariants[theme];
  return <div className="light-background" data-theme={theme} style={{ background: variant.background }} aria-hidden="true" />;
}

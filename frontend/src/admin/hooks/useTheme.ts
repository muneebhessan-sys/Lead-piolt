import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

type Theme = 'light' | 'dark' | 'system';

interface ThemeState {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

function getResolvedTheme(theme: Theme): 'light' | 'dark' {
  if (theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return theme;
}

function applyTheme(resolvedTheme: 'light' | 'dark') {
  document.documentElement.setAttribute('data-theme', resolvedTheme);
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'system',
      resolvedTheme: 'dark',
      setTheme: (theme: Theme) => {
        const resolved = getResolvedTheme(theme);
        applyTheme(resolved);
        set({ theme, resolvedTheme: resolved });
      },
      toggleTheme: () => {
        const { theme, resolvedTheme } = get();
        const nextTheme: Theme = theme === 'system' ? (resolvedTheme === 'dark' ? 'light' : 'dark') : theme === 'dark' ? 'light' : 'dark';
        const resolved = getResolvedTheme(nextTheme);
        applyTheme(resolved);
        set({ theme: nextTheme, resolvedTheme: resolved });
      },
    }),
    {
      name: 'admin-theme',
      storage: createJSONStorage(() => localStorage),
      onRehydrateStorage: () => (state) => {
        if (state) {
          const resolved = getResolvedTheme(state.theme);
          applyTheme(resolved);
          state.resolvedTheme = resolved;
        }
      },
    }
  )
);

export function useTheme() {
  const { theme, resolvedTheme, setTheme, toggleTheme } = useThemeStore();
  return { theme, resolvedTheme, setTheme, toggleTheme };
}

export function useThemeInit() {
  const { theme } = useThemeStore();
  if (typeof window !== 'undefined') {
    const resolved = getResolvedTheme(theme);
    applyTheme(resolved);
    useThemeStore.setState({ resolvedTheme: resolved });
  }
}
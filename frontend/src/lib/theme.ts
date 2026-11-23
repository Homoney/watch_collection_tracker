/**
 * Light/dark theme. The choice ('light', 'dark' or 'system') is kept in
 * localStorage; 'system' follows the OS setting. The theme is a `dark` class
 * on <html>, which Tailwind (darkMode: 'class') and the CSS tokens read.
 */
export type ThemeChoice = 'light' | 'dark' | 'system'

export const THEME_KEY = 'watch-tracker-theme'

const media = () =>
  typeof window !== 'undefined' && window.matchMedia
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : null

export function readThemeChoice(): ThemeChoice {
  try {
    const v = window.localStorage?.getItem(THEME_KEY)
    if (v === 'light' || v === 'dark' || v === 'system') return v
  } catch {
    // storage blocked: fall back to the OS setting
  }
  return 'system'
}

export function saveThemeChoice(choice: ThemeChoice) {
  try {
    window.localStorage?.setItem(THEME_KEY, choice)
  } catch {
    // storage blocked: the choice lasts for this page only
  }
}

export function resolveTheme(choice: ThemeChoice): 'light' | 'dark' {
  if (choice === 'system') return media()?.matches ? 'dark' : 'light'
  return choice
}

export function applyTheme(choice: ThemeChoice) {
  const dark = resolveTheme(choice) === 'dark'
  document.documentElement.classList.toggle('dark', dark)
}

/** Calls onChange when the OS setting changes; returns the unsubscribe. */
export function watchSystemTheme(onChange: () => void): () => void {
  const m = media()
  if (!m) return () => undefined
  m.addEventListener('change', onChange)
  return () => m.removeEventListener('change', onChange)
}

/* eslint-disable react-refresh/only-export-components */
import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from 'react'
import { applyTheme, readThemeChoice, resolveTheme, saveThemeChoice, ThemeChoice, watchSystemTheme } from '@/lib/theme'

interface ThemeContextValue {
  choice: ThemeChoice
  theme: 'light' | 'dark'
  setChoice: (choice: ThemeChoice) => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [choice, setChoiceState] = useState<ThemeChoice>(readThemeChoice)
  const [theme, setTheme] = useState<'light' | 'dark'>(() => resolveTheme(choice))

  useEffect(() => {
    const update = () => {
      applyTheme(choice)
      setTheme(resolveTheme(choice))
    }
    update()
    return choice === 'system' ? watchSystemTheme(update) : undefined
  }, [choice])

  const setChoice = useCallback((next: ThemeChoice) => {
    saveThemeChoice(next)
    setChoiceState(next)
  }, [])

  return <ThemeContext.Provider value={{ choice, theme, setChoice }}>{children}</ThemeContext.Provider>
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider')
  return ctx
}

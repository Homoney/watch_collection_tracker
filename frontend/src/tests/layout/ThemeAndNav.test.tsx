import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ThemeProvider } from '@/contexts/ThemeContext'
import ThemeToggle from '@/components/layout/ThemeToggle'
import Navbar from '@/components/layout/Navbar'
import { THEME_KEY, applyTheme, readThemeChoice } from '@/lib/theme'

const auth = { user: { email: 'demo@example.com', role: 'user' }, logout: vi.fn() }
vi.mock('@/contexts/AuthContext', () => ({ useAuth: () => auth }))

// jsdom on recent Node has no working localStorage or matchMedia; stub both
let store: Record<string, string>
let systemDark = false
beforeEach(() => {
  store = {}
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => store[k] ?? null,
    setItem: (k: string, v: string) => {
      store[k] = v
    },
    removeItem: (k: string) => delete store[k],
  })
  window.matchMedia = vi.fn().mockImplementation(() => ({
    matches: systemDark,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  })) as unknown as typeof window.matchMedia
  // Radix menus measure and capture pointers; jsdom lacks these
  window.HTMLElement.prototype.hasPointerCapture = () => false
  window.HTMLElement.prototype.releasePointerCapture = () => undefined
  window.HTMLElement.prototype.scrollIntoView = () => undefined
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver
  document.documentElement.classList.remove('dark')
  auth.user.role = 'user'
})
afterEach(() => {
  vi.unstubAllGlobals()
  systemDark = false
})

describe('theme', () => {
  it('follows the OS setting until the person chooses', () => {
    expect(readThemeChoice()).toBe('system')
    systemDark = true
    applyTheme('system')
    expect(document.documentElement).toHaveClass('dark')
    applyTheme('light')
    expect(document.documentElement).not.toHaveClass('dark')
  })

  it('the switch sets dark or light, and remembers the choice', async () => {
    const user = userEvent.setup()
    render(
      <ThemeProvider>
        <ThemeToggle />
      </ThemeProvider>
    )
    await user.click(screen.getByRole('button', { name: /theme/i }))
    await user.click(await screen.findByRole('menuitemradio', { name: 'Dark' }))
    expect(document.documentElement).toHaveClass('dark')
    expect(store[THEME_KEY]).toBe('dark')

    await user.click(screen.getByRole('button', { name: /theme/i }))
    await user.click(await screen.findByRole('menuitemradio', { name: 'Light' }))
    expect(document.documentElement).not.toHaveClass('dark')
    expect(store[THEME_KEY]).toBe('light')
  })
})

describe('navigation', () => {
  const renderNav = (path: string) =>
    render(
      <MemoryRouter initialEntries={[path]}>
        <ThemeProvider>
          <Navbar />
        </ThemeProvider>
      </MemoryRouter>
    )

  it('has a phone tab bar with the main pages and marks the current one', () => {
    renderNav('/watches/123')
    const bars = screen.getAllByRole('navigation', { name: 'Main' })
    const phone = bars[bars.length - 1]
    for (const name of ['Dashboard', 'Watches', 'Collections', 'Analytics', 'More']) {
      expect(within(phone).getByText(name)).toBeInTheDocument()
    }
    expect(within(phone).getByRole('link', { name: 'Watches' })).toHaveAttribute('aria-current', 'page')
  })

  it('the phone More menu reaches Settings, Admin (admins only) and Logout', async () => {
    auth.user.role = 'admin'
    const user = userEvent.setup()
    renderNav('/dashboard')
    await user.click(screen.getByRole('button', { name: 'More' }))
    expect(await screen.findByRole('menuitem', { name: 'Settings' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Admin' })).toBeInTheDocument()
    await user.click(screen.getByRole('menuitem', { name: 'Logout' }))
    expect(auth.logout).toHaveBeenCalled()
  })

  it('hides Admin from people who are not admins', () => {
    renderNav('/dashboard')
    expect(screen.queryByRole('link', { name: 'Admin' })).not.toBeInTheDocument()
  })
})

import { describe, it, expect, vi, beforeAll } from 'vitest'
import { ReactNode } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import WatchDetailPage from '@/pages/WatchDetailPage'
import { ThemeProvider } from '@/contexts/ThemeContext'

vi.mock('@/components/layout/AppLayout', () => ({
  default: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}))
// The tab bodies have their own tests; stub them to keep this one on layout
vi.mock('@/components/watches/ValueChart', () => ({ default: () => <div>value chart</div> }))
vi.mock('@/components/watches/WatchAnalytics', () => ({ default: () => <div>watch analytics</div> }))
vi.mock('@/components/watches/MarketValueHistory', () => ({ default: () => <div>value history</div> }))
vi.mock('@/components/watches/ServiceHistoryList', () => ({ default: () => <div>service list</div> }))
vi.mock('@/components/watches/WatchQRCode', () => ({ default: () => <div>qr code</div> }))
vi.mock('@/components/watches/ImageUpload', () => ({ default: () => <div>upload</div> }))

const watch = {
  id: 'w1',
  brand: { id: 'b1', name: 'Rolex', sort_order: 0 },
  model: 'Submariner Date',
  reference_number: '126610LN',
  serial_number: null,
  movement_type: { id: 'm1', name: 'Automatic', sort_order: 0 },
  caliber: '3235',
  case_diameter: 41,
  case_thickness: 12.5,
  case_material: 'Oystersteel',
  lug_width: 21,
  water_resistance: 300,
  power_reserve: 70,
  crystal: 'Sapphire',
  purchase_date: '2019-01-10T00:00:00',
  purchase_price: 9150,
  purchase_currency: 'USD',
  retailer: 'Authorized dealer',
  condition: 'excellent',
  current_market_value: 14200,
  current_market_currency: 'USD',
  last_value_update: '2026-11-01T00:00:00',
  notes: 'Bought for my 40th',
  complications: ['Date'],
  images: [],
  collection: null,
}
vi.mock('@/hooks/useWatches', () => ({
  useWatch: () => ({ data: watch, isLoading: false, error: null }),
  useUpdateWatch: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeleteWatch: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))

beforeAll(() => {
  window.HTMLElement.prototype.hasPointerCapture = () => false
  window.HTMLElement.prototype.releasePointerCapture = () => undefined
  window.HTMLElement.prototype.scrollIntoView = () => undefined
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver
  window.matchMedia = vi.fn().mockReturnValue({
    matches: false,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }) as unknown as typeof window.matchMedia
})

function renderPage() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <ThemeProvider>
        <MemoryRouter initialEntries={['/watches/w1']}>
          <Routes>
            <Route path="/watches/:id" element={<WatchDetailPage />} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>
    </QueryClientProvider>
  )
}

describe('watch detail (Collector\'s Vault)', () => {
  it('opens with the value, the gain and the key facts', () => {
    renderPage()
    expect(screen.getByRole('heading', { level: 1, name: 'Submariner Date' })).toBeInTheDocument()
    expect(screen.getByText('$14,200')).toBeInTheDocument()
    expect(screen.getByText(/\$5,050 · \+55\.2% on \$9,150/)).toBeInTheDocument()
    expect(screen.getByText('Automatic · cal. 3235')).toBeInTheDocument()
    expect(screen.getByText('41 mm · 12.5 mm thick · Oystersteel')).toBeInTheDocument()
    expect(screen.getByText('300 m')).toBeInTheDocument()
  })

  it('puts the rest in tabs, value first', async () => {
    const user = userEvent.setup()
    renderPage()
    const tabs = within(screen.getByRole('tablist', { name: 'Watch details' })).getAllByRole('tab')
    expect(tabs.map((t) => t.textContent)).toEqual(['Value', 'Details', 'Service', 'Photos', 'QR code'])
    expect(screen.getByText('value chart')).toBeInTheDocument()
    expect(screen.queryByText('service list')).not.toBeInTheDocument()

    await user.click(screen.getByRole('tab', { name: 'Details' }))
    expect(screen.getByText('Sapphire')).toBeInTheDocument()
    expect(screen.getByText('Bought for my 40th')).toBeInTheDocument()

    await user.click(screen.getByRole('tab', { name: 'Service' }))
    expect(screen.getByText('service list')).toBeInTheDocument()
  })

  it('keeps Delete, PDF and accuracy in the More menu', async () => {
    const user = userEvent.setup()
    renderPage()
    expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'More actions' }))
    expect(await screen.findByRole('menuitem', { name: 'Delete watch' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Export PDF' })).toBeInTheDocument()
    expect(screen.getByRole('menuitem', { name: 'Movement accuracy' })).toBeInTheDocument()
  })
})

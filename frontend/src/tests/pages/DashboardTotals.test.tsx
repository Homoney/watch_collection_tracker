import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ReactNode } from 'react'
import { renderWithProviders, screen, within } from '../test-utils'
import DashboardPage from '@/pages/DashboardPage'
import { watchesApi, collectionsApi, marketValuesApi } from '@/lib/api'
import type { CollectionAnalytics } from '@/types'

vi.mock('@/components/layout/AppLayout', () => ({
  default: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}))

const analytics = {
  total_watches: 8,
  total_current_value: '64026.00',
  total_purchase_price: '49680.00',
  currency: 'USD',
  total_return: '14346.00',
  average_roi: 28.87,
  top_performers: [],
  worst_performers: [],
  value_by_brand: {},
  value_by_collection: {},
  total_valuations: 8,
} as CollectionAnalytics

describe('dashboard value card', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('shows the whole collection current value and amount paid, not the recent five purchase prices', async () => {
    // The list endpoint only returns the five recent watches; their prices must not be the total
    vi.spyOn(watchesApi, 'list').mockResolvedValue({
      items: [{ id: 'w1', purchase_price: '31080.00' }],
      total: 8,
      limit: 5,
      offset: 0,
    } as unknown as Awaited<ReturnType<typeof watchesApi.list>>)
    vi.spyOn(collectionsApi, 'list').mockResolvedValue([])
    const spy = vi.spyOn(marketValuesApi, 'getCollectionAnalytics').mockResolvedValue(analytics)

    renderWithProviders(<DashboardPage />)

    expect(await screen.findByText('$64,026.00')).toBeInTheDocument()
    const card = screen.getByText('Current value').parentElement as HTMLElement
    expect(within(card).getByText('$64,026.00')).toBeInTheDocument()
    expect(within(card).getByText('Paid: $49,680.00')).toBeInTheDocument()
    expect(within(card).queryByText('$31,080.00')).not.toBeInTheDocument()
    expect(spy).toHaveBeenCalledWith('USD')
  })
})

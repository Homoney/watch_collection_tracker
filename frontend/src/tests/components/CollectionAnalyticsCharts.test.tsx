import { describe, it, expect, vi, beforeEach } from 'vitest'
import { cloneElement, ReactElement } from 'react'
import { renderWithProviders, screen } from '../test-utils'
import CollectionAnalytics from '@/components/analytics/CollectionAnalytics'
import { marketValuesApi } from '@/lib/api'
import type { CollectionAnalytics as Analytics } from '@/types'

// jsdom has no layout, so give the charts a fixed size, and skip the
// animations so the slices are drawn at once
vi.mock('recharts', async (importOriginal) => {
  const actual = await importOriginal<typeof import('recharts')>()
  for (const chart of [actual.Pie, actual.Bar] as unknown as { defaultProps: Record<string, unknown> }[]) {
    chart.defaultProps = { ...chart.defaultProps, isAnimationActive: false }
  }
  return {
    ...actual,
    ResponsiveContainer: ({ children }: { children: ReactElement }) =>
      cloneElement(children, { width: 600, height: 300 }),
  }
})

describe('collection analytics charts', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('draws the distribution pie and scales the bar axis when the API sends values as strings', async () => {
    // Pydantic sends Decimal values as JSON strings, exactly like this
    vi.spyOn(marketValuesApi, 'getCollectionAnalytics').mockResolvedValue({
      total_watches: 3,
      total_current_value: '35619.00',
      total_purchase_price: '30000.00',
      currency: 'USD',
      total_return: '5619.00',
      average_roi: 18.7,
      top_performers: [],
      worst_performers: [],
      value_by_brand: { 'Patek Philippe': '21461.00', Rolex: '13653.00', Seiko: '505.00' },
      value_by_collection: {},
      total_valuations: 3,
    } as Analytics)

    const { container } = renderWithProviders(<CollectionAnalytics currency="USD" />)
    await screen.findByText('Collection distribution')

    // One pie slice per brand (none were drawn when values were strings)
    expect(container.querySelectorAll('.recharts-pie-sector')).toHaveLength(3)
    // The bar axis reaches the largest value, not the largest string ('505.00')
    const ticks = Array.from(container.querySelectorAll('.recharts-yAxis .recharts-cartesian-axis-tick-value')).map(
      (t) => t.textContent
    )
    const top = Number(String(ticks[ticks.length - 1]).replace('K', '')) * 1000
    expect(top).toBeGreaterThanOrEqual(21461)
  })

  const perf = (model: string, roi: number) => ({
    watch_id: model,
    model,
    brand: 'Brand',
    roi,
    current_value: 1000,
    purchase_price: 900,
  })
  const base = {
    total_watches: 7,
    total_current_value: '1000.00',
    total_purchase_price: '900.00',
    currency: 'USD',
    total_return: '100.00',
    average_roi: 12,
    value_by_brand: { Rolex: '600.00', Omega: '400.00' },
    value_by_collection: {},
    total_valuations: 7,
  }

  it('colours a return by its sign: a small gain in the lowest returns is green, a loss red', async () => {
    vi.spyOn(marketValuesApi, 'getCollectionAnalytics').mockResolvedValue({
      ...base,
      top_performers: [perf('Best', 80)],
      worst_performers: [perf('Small gain', 10.31), perf('Loss', -4)],
    } as Analytics)
    renderWithProviders(<CollectionAnalytics currency="USD" />)
    expect(await screen.findByText('Lowest returns')).toBeInTheDocument()
    expect(screen.queryByText(/needs attention/i)).not.toBeInTheDocument()
    for (const el of screen.getAllByText('+10.31%')) expect(el).toHaveClass('text-positive')
    expect(screen.getByText('-4.00%')).toHaveClass('text-negative')
  })

  it('on a phone the pie uses a legend instead of labels that run off the edges', async () => {
    window.matchMedia = vi.fn().mockImplementation((q: string) => ({
      matches: q.includes('max-width'),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    })) as unknown as typeof window.matchMedia
    vi.spyOn(marketValuesApi, 'getCollectionAnalytics').mockResolvedValue({
      ...base,
      top_performers: [],
      worst_performers: [],
    } as Analytics)
    const { container } = renderWithProviders(<CollectionAnalytics currency="USD" />)
    await screen.findByText('Collection distribution')
    expect(container.querySelectorAll('.recharts-pie-sector')).toHaveLength(2)
    expect(container.querySelector('.recharts-pie-labels')).toBeNull()
    expect(container.querySelector('.recharts-legend-wrapper')).toHaveTextContent(/Rolex.*Omega/)
  })
})

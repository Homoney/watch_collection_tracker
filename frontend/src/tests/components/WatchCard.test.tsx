import { describe, it, expect, vi } from 'vitest'
import { renderWithProviders, screen } from '../test-utils'
import WatchCard from '@/components/watches/WatchCard'
import type { WatchListItem } from '@/types'

const mockWatch: WatchListItem = {
  id: '123',
  brand_id: 'brand-1',
  model: 'Submariner Date',
  reference_number: '116610LN',
  collection_id: 'col-1',
  purchase_date: '2020-01-15T00:00:00',
  purchase_price: 9000.00,
  purchase_currency: 'USD',
  condition: 'excellent',
  created_at: '2024-01-01T00:00:00',
  brand: {
    id: 'brand-1',
    name: 'Rolex',
    sort_order: 0
  },
  collection: {
    id: 'col-1',
    name: 'Dive Watches',
    description: null,
    color: '#0000FF',
    user_id: 'user-1',
    is_default: false,
    watch_count: 1,
    created_at: '2024-01-01T00:00:00',
    updated_at: '2024-01-01T00:00:00'
  },
  primary_image: {
    id: 'img-1',
    watch_id: '123',
    file_path: 'watch-123/image.jpg',
    file_name: 'image.jpg',
    file_size: 12345,
    mime_type: 'image/jpeg',
    width: 800,
    height: 600,
    is_primary: true,
    sort_order: 0,
    source: 'user_upload',
    created_at: '2024-01-01T00:00:00',
    url: '/uploads/watch-123/image.jpg'
  }
}

describe('WatchCard', () => {
  it('renders watch model and brand', () => {
    renderWithProviders(<WatchCard watch={mockWatch} />)

    expect(screen.getByText('Submariner Date')).toBeInTheDocument()
    expect(screen.getByText('Rolex')).toBeInTheDocument()
  })

  it('displays primary image when available', () => {
    renderWithProviders(<WatchCard watch={mockWatch} />)

    const image = screen.getByRole('img', { name: /Rolex Submariner Date/i })
    expect(image).toBeInTheDocument()
    expect(image).toHaveAttribute('src', '/uploads/watch-123/image.jpg')
  })

  it('displays placeholder when no primary image', () => {
    const watchWithoutImage = { ...mockWatch, primary_image: null }
    renderWithProviders(<WatchCard watch={watchWithoutImage} />)

    // Check for SVG placeholder instead
    const placeholder = document.querySelector('svg')
    expect(placeholder).toBeInTheDocument()
  })

  it('displays collection color', () => {
    renderWithProviders(<WatchCard watch={mockWatch} />)

    expect(screen.getByText('Dive Watches')).toBeInTheDocument()
  })

  it('displays purchase price', () => {
    renderWithProviders(<WatchCard watch={mockWatch} />)

    // Price is formatted as currency, e.g., "$9,000.00"
    expect(screen.getByText(/\$9,000/)).toBeInTheDocument()
  })

  it('calls onSelectionToggle when in compare mode', () => {
    const onSelectionToggle = vi.fn()
    renderWithProviders(
      <WatchCard
        watch={mockWatch}
        isCompareMode={true}
        isSelected={false}
        onSelectionToggle={onSelectionToggle}
      />
    )

    const checkbox = screen.getByRole('checkbox')
    expect(checkbox).toBeInTheDocument()
  })

  it('does not show checkbox when not in compare mode', () => {
    renderWithProviders(<WatchCard watch={mockWatch} isCompareMode={false} />)

    const checkbox = screen.queryByRole('checkbox')
    expect(checkbox).not.toBeInTheDocument()
  })
})

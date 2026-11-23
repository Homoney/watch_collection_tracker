import { describe, it, expect, vi } from 'vitest'
import { renderWithProviders, screen } from '../test-utils'
import WatchForm from '@/components/watches/WatchForm'
import type { Watch } from '@/types'

// Brands start empty (still loading) and arrive on a later render
const ref = vi.hoisted(() => ({ brands: [] as { id: string; name: string; sort_order: number }[] }))
vi.mock('@/hooks/useReferenceData', () => ({
  useBrands: () => ({ data: ref.brands }),
  useMovementTypes: () => ({ data: [] }),
  useComplications: () => ({ data: [] }),
}))
vi.mock('@/hooks/useCollections', () => ({ useCollections: () => ({ data: [] }) }))

describe('Edit Watch on a direct load', () => {
  it('shows the stored brand once the brand list arrives', () => {
    const watch = { id: 'w1', brand_id: 'b-rolex', model: 'Submariner', complications: [] } as unknown as Watch
    const { rerender } = renderWithProviders(
      <WatchForm defaultValues={watch} onSubmit={vi.fn()} onCancel={vi.fn()} />
    )
    expect((screen.getByLabelText(/^Brand/) as HTMLSelectElement).value).toBe('')

    ref.brands = [
      { id: 'b-omega', name: 'Omega', sort_order: 0 },
      { id: 'b-rolex', name: 'Rolex', sort_order: 1 },
    ]
    rerender(<WatchForm defaultValues={watch} onSubmit={vi.fn()} onCancel={vi.fn()} />)
    expect((screen.getByLabelText(/^Brand/) as HTMLSelectElement).value).toBe('b-rolex')
  })
})

import { describe, it, expect, vi } from 'vitest'
import { renderWithProviders, screen, within } from '../test-utils'
import WatchForm from '@/components/watches/WatchForm'

vi.mock('@/hooks/useReferenceData', () => ({
  useBrands: () => ({ data: [{ id: 'b-rolex', name: 'Rolex', sort_order: 0 }] }),
  useMovementTypes: () => ({ data: [] }),
  useComplications: () => ({ data: [{ id: 'c1', name: 'Date', sort_order: 0 }] }),
}))
vi.mock('@/hooks/useCollections', () => ({ useCollections: () => ({ data: [] }) }))

describe('watch form layout (Collector\'s Vault)', () => {
  it('groups the fields into labelled sections', () => {
    renderWithProviders(<WatchForm onSubmit={vi.fn()} onCancel={vi.fn()} />)
    const names = screen.getAllByRole('group').map((g) => g.querySelector('legend')?.textContent)
    expect(names).toEqual(['The watch', 'Purchase and value', 'Specifications', 'Notes'])
    const purchase = screen.getByRole('group', { name: 'Purchase and value' })
    expect(within(purchase).getByLabelText('Purchase Price')).toBeInTheDocument()
    expect(within(purchase).getByLabelText('Current Market Value')).toBeInTheDocument()
  })

  it('puts Look up beside the reference field', () => {
    renderWithProviders(<WatchForm onSubmit={vi.fn()} onCancel={vi.fn()} />)
    const lookup = screen.getByRole('button', { name: /look up/i })
    const reference = screen.getByLabelText('Reference Number')
    // Same two-column row: the button is a sibling cell of the field's wrapper
    expect(lookup.parentElement?.parentElement).toBe(reference.closest('.grid'))
  })
})

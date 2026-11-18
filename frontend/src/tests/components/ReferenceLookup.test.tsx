import { describe, it, expect, vi, beforeEach } from 'vitest'
import userEvent from '@testing-library/user-event'
import { renderWithProviders, screen, waitFor } from '../test-utils'
import WatchForm from '@/components/watches/WatchForm'
import { specLookupApi } from '@/lib/api'
import type { SpecLookupResult } from '@/types'

vi.mock('@/hooks/useReferenceData', () => ({
  useBrands: () => ({ data: [{ id: 'b-rolex', name: 'Rolex' }, { id: 'b-omega', name: 'Omega' }] }),
  useMovementTypes: () => ({ data: [{ id: 'mt-auto', name: 'Automatic' }] }),
  useComplications: () => ({
    data: [
      { id: 'c1', name: 'Date' },
      { id: 'c2', name: 'Dive Bezel' },
    ],
  }),
}))
vi.mock('@/hooks/useCollections', () => ({ useCollections: () => ({ data: [] }) }))

const wb = { name: 'WatchBase', url: 'https://watchbase.com/rolex/submariner/126610ln-0001' }

const okAnswer: SpecLookupResult = {
  status: 'ok',
  message: 'Filled the empty fields we found. Check them before saving.',
  reference: '126610LN',
  fields: {
    brand_name: 'Rolex',
    model: 'Submariner Date 41',
    movement_type_name: 'Automatic',
    case_diameter: 41,
    lug_width: 21,
    water_resistance: 300,
    caliber: '3235',
    crystal: 'Sapphire',
    complications: ['Date', 'Dive Bezel', 'Unknown Thing'],
  },
  sources: {
    brand_name: wb,
    model: wb,
    movement_type_name: wb,
    case_diameter: wb,
    lug_width: wb,
    water_resistance: wb,
    caliber: wb,
    crystal: wb,
    complications: wb,
  },
  choices: [],
  movement: { caliber: '3235', jewels: 31, frequency: '28,800 bph', source: { name: 'Caliber Corner', url: 'https://calibercorner.com/rolex-caliber-3235/' } },
  links: [{ label: 'WatchBase', url: 'https://duckduckgo.com/?q=site%3Awatchbase.com+126610LN' }],
  watchbase_id: 31501,
  has_photo: true,
}

function renderForm() {
  const onSubmit = vi.fn()
  renderWithProviders(<WatchForm onSubmit={onSubmit} onCancel={() => {}} />)
  return onSubmit
}

describe('reference look-up on the watch form', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('fills only empty fields and marks their source', async () => {
    const spy = vi.spyOn(specLookupApi, 'lookup').mockResolvedValue(okAnswer)
    const onSubmit = renderForm()
    const user = userEvent.setup()

    await user.type(screen.getByPlaceholderText('e.g., Submariner, Speedmaster'), 'My Sub')
    await user.type(screen.getByPlaceholderText('e.g., 126610LN'), '126610LN')
    await user.click(screen.getByRole('button', { name: /look up/i }))

    await screen.findByText(/Filled the empty fields/)
    expect(spy).toHaveBeenCalledWith({
      reference: '126610LN',
      brand_id: undefined,
      caliber: undefined,
      watchbase_id: undefined,
    })
    // Model was typed by the user: kept
    expect(screen.getByPlaceholderText('e.g., Submariner, Speedmaster')).toHaveValue('My Sub')
    expect(screen.getByPlaceholderText('e.g., 3235')).toHaveValue('3235')
    expect(screen.getByPlaceholderText('e.g., Sapphire')).toHaveValue('Sapphire')
    expect(screen.getByPlaceholderText('40.00')).toHaveValue(41)
    // Source marks on filled fields only (not on Model)
    const marks = screen.getAllByText(/Filled from/)
    expect(marks.length).toBe(8) // brand, movement, diameter, lug, WR, caliber, crystal, complications
    expect(screen.getByText(/31 jewels/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Caliber Corner/ })).toHaveAttribute(
      'href',
      'https://calibercorner.com/rolex-caliber-3235/'
    )

    await user.click(screen.getByRole('button', { name: 'Add Watch' }))
    await waitFor(() => expect(onSubmit).toHaveBeenCalled())
    const [sent, extras] = onSubmit.mock.calls[0]
    // Photo offered and kept ticked: the parent saves it after the watch
    expect(extras).toEqual({ referencePhotoWatchbaseId: 31501 })
    expect(sent.brand_id).toBe('b-rolex')
    expect(sent.movement_type_id).toBe('mt-auto')
    expect(sent.complications).toEqual(['Date', 'Dive Bezel'])
    expect(sent.caliber).toBe('3235')
    expect(sent.model).toBe('My Sub')
  })

  it('can untick the reference photo', async () => {
    vi.spyOn(specLookupApi, 'lookup').mockResolvedValue(okAnswer)
    const onSubmit = renderForm()
    const user = userEvent.setup()
    await user.type(screen.getByPlaceholderText('e.g., 126610LN'), '126610LN')
    await user.click(screen.getByRole('button', { name: /look up/i }))
    const box = await screen.findByRole('checkbox', { name: /reference photo/i })
    expect(box).toBeChecked()
    await user.click(box)
    await user.click(screen.getByRole('button', { name: 'Add Watch' }))
    await waitFor(() => expect(onSubmit).toHaveBeenCalled())
    expect(onSubmit.mock.calls[0][1]).toEqual({ referencePhotoWatchbaseId: undefined })
  })

  it('offers no photo when WatchBase has none', async () => {
    vi.spyOn(specLookupApi, 'lookup').mockResolvedValue({ ...okAnswer, has_photo: false })
    renderForm()
    const user = userEvent.setup()
    await user.type(screen.getByPlaceholderText('e.g., 126610LN'), '126610LN')
    await user.click(screen.getByRole('button', { name: /look up/i }))
    await screen.findByText(/Filled the empty fields/)
    expect(screen.queryByRole('checkbox', { name: /reference photo/i })).not.toBeInTheDocument()
  })

  it('offers a choice when several watches match, then looks up the one picked', async () => {
    const spy = vi
      .spyOn(specLookupApi, 'lookup')
      .mockResolvedValueOnce({
        ...okAnswer,
        status: 'choices',
        message: 'Several watches match. Pick yours.',
        fields: {},
        sources: {},
        movement: null,
        choices: [
          { id: 1, reference: 'SBGE201', name: 'Spring Drive GMT', brand: 'Grand Seiko', family: 'Spring Drive' },
          { id: 2, reference: 'SBGE205', name: 'Ice Blue', brand: 'Grand Seiko', family: 'Spring Drive' },
        ],
      })
      .mockResolvedValueOnce(okAnswer)
    renderForm()
    const user = userEvent.setup()
    await user.type(screen.getByPlaceholderText('e.g., 126610LN'), 'SBGE2')
    await user.click(screen.getByRole('button', { name: /look up/i }))
    await user.click(await screen.findByRole('button', { name: /SBGE205/ }))
    await waitFor(() => expect(spy).toHaveBeenCalledTimes(2))
    expect(spy.mock.calls[1][0].watchbase_id).toBe(2)
  })

  it('without a key shows the message and links, fills nothing', async () => {
    vi.spyOn(specLookupApi, 'lookup').mockResolvedValue({
      ...okAnswer,
      status: 'links_only',
      message: 'Automatic look-up is off (no WatchBase key). Use the links to look the reference up yourself.',
      fields: {},
      sources: {},
      movement: null,
    })
    renderForm()
    const user = userEvent.setup()
    await user.type(screen.getByPlaceholderText('e.g., 126610LN'), '126610LN')
    await user.click(screen.getByRole('button', { name: /look up/i }))
    expect(await screen.findByText(/Automatic look-up is off/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /WatchBase/ })).toHaveAttribute('target', '_blank')
    expect(screen.queryByText(/Filled from/)).not.toBeInTheDocument()
  })

  it('asks for a reference before looking up', async () => {
    const spy = vi.spyOn(specLookupApi, 'lookup')
    renderForm()
    await userEvent.setup().click(screen.getByRole('button', { name: /look up/i }))
    expect(await screen.findByText('Type a reference number first.')).toBeInTheDocument()
    expect(spy).not.toHaveBeenCalled()
  })
})

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useState } from 'react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders, screen, waitFor } from '../test-utils'
import Modal from '@/components/common/Modal'
import WatchForm from '@/components/watches/WatchForm'
import CollectionForm from '@/components/collections/CollectionForm'
import { addWatchDraftKey, clearDraft, loadDraft } from '@/lib/watchDraft'
import type { Watch } from '@/types'

vi.mock('@/hooks/useReferenceData', () => ({
  useBrands: () => ({ data: [{ id: 'b-rolex', name: 'Rolex' }] }),
  useMovementTypes: () => ({ data: [{ id: 'mt-auto', name: 'Automatic' }] }),
  useComplications: () => ({ data: [{ id: 'c1', name: 'Date' }] }),
}))
vi.mock('@/hooks/useCollections', () => ({ useCollections: () => ({ data: [] }) }))

const KEY = addWatchDraftKey('user-1')
const MODEL = 'e.g., Submariner, Speedmaster'

/** The Add watch pop-up as WatchListPage wires it */
function AddWatch({ onSaved = () => undefined }: { onSaved?: () => void }) {
  const [open, setOpen] = useState(true)
  return (
    <>
      <button onClick={() => setOpen(true)}>Open</button>
      <span>{open ? 'is open' : 'is closed'}</span>
      <Modal
        isOpen={open}
        onClose={() => {
          clearDraft(KEY)
          setOpen(false)
        }}
        title="Add New Watch"
        form
      >
        <WatchForm
          onSubmit={() => {
            clearDraft(KEY)
            setOpen(false)
            onSaved()
          }}
          onCancel={() => setOpen(false)}
          draftKey={KEY}
        />
      </Modal>
    </>
  )
}

/** In-memory localStorage (some Node versions leave jsdom's undefined) */
function memoryStorage(): Storage {
  const items = new Map<string, string>()
  return {
    get length() {
      return items.size
    },
    clear: () => items.clear(),
    getItem: (k) => items.get(k) ?? null,
    key: (i) => [...items.keys()][i] ?? null,
    removeItem: (k) => void items.delete(k),
    setItem: (k, v) => void items.set(k, String(v)),
  }
}

describe('form pop-ups keep what was typed', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'localStorage', { value: memoryStorage(), configurable: true })
  })

  it('a click outside never closes a form pop-up', async () => {
    const user = userEvent.setup()
    renderWithProviders(<AddWatch />)
    await user.type(screen.getByPlaceholderText(MODEL), 'Sub')
    await user.click(screen.getByTestId('modal-backdrop'))
    expect(screen.getByText('is open')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(MODEL)).toHaveValue('Sub')
    expect(screen.queryByText('Discard changes?')).not.toBeInTheDocument()
  })

  it('a click outside still closes a pop-up without a form', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    renderWithProviders(
      <Modal isOpen onClose={onClose} title="Delete Watch">
        <p>Sure?</p>
      </Modal>
    )
    await user.click(screen.getByTestId('modal-backdrop'))
    expect(onClose).toHaveBeenCalled()
  })

  it('Escape closes at once when nothing was typed', async () => {
    const user = userEvent.setup()
    renderWithProviders(<AddWatch />)
    await user.keyboard('{Escape}')
    expect(screen.getByText('is closed')).toBeInTheDocument()
  })

  it('Escape asks first when something was typed; Keep editing keeps it', async () => {
    const user = userEvent.setup()
    renderWithProviders(<AddWatch />)
    await user.type(screen.getByPlaceholderText(MODEL), 'Sub')
    await user.keyboard('{Escape}')
    expect(screen.getByText('Discard changes?')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Keep editing' }))
    expect(screen.queryByText('Discard changes?')).not.toBeInTheDocument()
    expect(screen.getByPlaceholderText(MODEL)).toHaveValue('Sub')
  })

  it.each([
    ['the X', () => screen.getByRole('button', { name: 'Close' })],
    ['Cancel', () => screen.getByRole('button', { name: 'Cancel' })],
  ])('%s asks first, and Discard closes and drops the draft', async (_name, button) => {
    const user = userEvent.setup()
    renderWithProviders(<AddWatch />)
    await user.type(screen.getByPlaceholderText(MODEL), 'Sub')
    await waitFor(() => expect(loadDraft(KEY)?.values.model).toBe('Sub'))
    await user.click(button())
    expect(screen.getByText('is open')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Discard' }))
    expect(screen.getByText('is closed')).toBeInTheDocument()
    expect(loadDraft(KEY)).toBeNull()
  })

  it('a reload or crash reopens the Add form with what was typed', async () => {
    const user = userEvent.setup()
    const first = renderWithProviders(<AddWatch />)
    await user.type(screen.getByPlaceholderText(MODEL), 'Snowflake')
    await user.click(screen.getByRole('checkbox', { name: 'Date' }))
    await waitFor(() => expect(loadDraft(KEY)?.complications).toEqual(['Date']))
    first.unmount() // the page goes away without closing the pop-up

    renderWithProviders(<AddWatch />)
    expect(await screen.findByText(/Restored what you typed last time/)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(MODEL)).toHaveValue('Snowflake')
    expect(screen.getByRole('checkbox', { name: 'Date' })).toBeChecked()
    // Restored text counts as typed: closing still asks
    await user.keyboard('{Escape}')
    expect(screen.getByText('Discard changes?')).toBeInTheDocument()
  })

  it('saving the watch clears the draft', async () => {
    const onSaved = vi.fn()
    const user = userEvent.setup()
    renderWithProviders(<AddWatch onSaved={onSaved} />)
    await user.selectOptions(screen.getByRole('option', { name: 'Rolex' }).closest('select')!, 'b-rolex')
    await user.type(screen.getByPlaceholderText(MODEL), 'Sub')
    await waitFor(() => expect(loadDraft(KEY)).not.toBeNull())
    await user.click(screen.getByRole('button', { name: 'Add Watch' }))
    await waitFor(() => expect(onSaved).toHaveBeenCalled())
    expect(loadDraft(KEY)).toBeNull()
  })

  it('a broken draft is ignored', () => {
    window.localStorage.setItem(KEY, '{not json')
    renderWithProviders(<AddWatch />)
    expect(screen.getByPlaceholderText(MODEL)).toHaveValue('')
    expect(screen.queryByText(/Restored/)).not.toBeInTheDocument()
  })

  it('the Edit form asks only after a change, and keeps no draft', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    const watch = { id: 'w1', brand_id: 'b-rolex', model: 'Sub', complications: [] } as unknown as Watch
    renderWithProviders(
      <Modal isOpen onClose={onClose} title="Edit Watch" form>
        <WatchForm defaultValues={watch} onSubmit={() => undefined} onCancel={onClose} />
      </Modal>
    )
    await user.click(screen.getByTestId('modal-backdrop'))
    expect(onClose).not.toHaveBeenCalled()
    await user.type(screen.getByPlaceholderText(MODEL), ' Date')
    await user.keyboard('{Escape}')
    expect(screen.getByText('Discard changes?')).toBeInTheDocument()
    expect(onClose).not.toHaveBeenCalled()
    expect(window.localStorage.length).toBe(0)
  })

  it('the collection form asks before discarding too', async () => {
    const onClose = vi.fn()
    const user = userEvent.setup()
    renderWithProviders(
      <Modal isOpen onClose={onClose} title="Create New Collection" form>
        <CollectionForm onSubmit={() => undefined} onCancel={onClose} />
      </Modal>
    )
    await user.type(screen.getByPlaceholderText(/Current Collection/), 'Dress')
    await user.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(screen.getByText('Discard changes?')).toBeInTheDocument()
    expect(onClose).not.toHaveBeenCalled()
  })
})

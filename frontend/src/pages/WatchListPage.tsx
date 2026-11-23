import { useState, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { FileDown, GitCompare, MoreHorizontal, Plus, Search, SlidersHorizontal } from 'lucide-react'
import AppLayout from '@/components/layout/AppLayout'
import WatchList from '@/components/watches/WatchList'
import WatchFilters from '@/components/watches/WatchFilters'
import FilterChips from '@/components/watches/FilterChips'
import WatchForm, { type WatchFormExtras } from '@/components/watches/WatchForm'
import ComparisonBar from '@/components/watches/ComparisonBar'
import Modal from '@/components/common/Modal'
import Button from '@/components/common/Button'
import { useWatches, useCreateWatch, useDeleteWatch } from '@/hooks/useWatches'
import { useBrands, useMovementTypes } from '@/hooks/useReferenceData'
import { useCollections } from '@/hooks/useCollections'
import { useCollectionAnalytics } from '@/hooks/useMarketValues'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { formatMoney, formatPercent, gainPercent } from '@/lib/money'
import { useComparison } from '@/contexts/ComparisonContext'
import { api, referencePhotoApi } from '@/lib/api'
import { addWatchDraftKey, clearDraft } from '@/lib/watchDraft'
import { useAuth } from '@/contexts/AuthContext'
import type { WatchFilters as WatchFiltersType, WatchListItem, WatchCreate } from '@/types'

export default function WatchListPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [deleteWatch, setDeleteWatch] = useState<WatchListItem | null>(null)
  const [page, setPage] = useState(0)
  const limit = 20

  const {
    selectedWatchIds,
    isCompareMode,
    setCompareMode,
    toggleWatch,
    clearSelection,
  } = useComparison()

  const [filters, setFilters] = useState<WatchFiltersType>({
    collection_id: searchParams.get('collection_id') || undefined,
    brand_id: searchParams.get('brand_id') || undefined,
    movement_type_id: searchParams.get('movement_type_id') || undefined,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    condition: (searchParams.get('condition') as any) || undefined,
    search: searchParams.get('search') || undefined,
    sort_by: searchParams.get('sort_by') || 'created_at',
    sort_order: (searchParams.get('sort_order') as 'asc' | 'desc') || 'desc',
  })

  useEffect(() => {
    const params = new URLSearchParams()
    if (filters.collection_id) params.set('collection_id', filters.collection_id)
    if (filters.brand_id) params.set('brand_id', filters.brand_id)
    if (filters.movement_type_id) params.set('movement_type_id', filters.movement_type_id)
    if (filters.condition) params.set('condition', filters.condition)
    if (filters.search) params.set('search', filters.search)
    if (filters.sort_by) params.set('sort_by', filters.sort_by)
    if (filters.sort_order) params.set('sort_order', filters.sort_order)
    setSearchParams(params)
  }, [filters, setSearchParams])

  const { data, isLoading, error } = useWatches(filters, limit, page * limit)
  const { data: brands } = useBrands()
  const { data: movementTypes } = useMovementTypes()
  const { data: collections } = useCollections()
  const createMutation = useCreateWatch()
  const { user } = useAuth()
  const draftKey = addWatchDraftKey(user?.id)
  const deleteMutation = useDeleteWatch()
  const { data: analytics } = useCollectionAnalytics('USD')
  const [showFilters, setShowFilters] = useState(false)

  // Toolbar search box, applied half a second after typing stops
  const [search, setSearch] = useState(filters.search || '')
  useEffect(() => {
    setSearch(filters.search || '')
  }, [filters.search])
  useEffect(() => {
    const id = setTimeout(() => {
      if ((search || undefined) !== filters.search) {
        setFilters((f) => ({ ...f, search: search || undefined }))
        setPage(0)
      }
    }, 500)
    return () => clearTimeout(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search])

  const handleFiltersChange = (newFilters: WatchFiltersType) => {
    setFilters(newFilters)
    setPage(0)
  }

  const handleRemoveFilter = (filterKey: keyof WatchFiltersType) => {
    const newFilters = { ...filters }
    delete newFilters[filterKey]
    handleFiltersChange(newFilters)
  }

  const handleClearAllFilters = () => {
    handleFiltersChange({
      sort_by: 'created_at',
      sort_order: 'desc',
    })
  }

  const handleCreateWatch = async (data: WatchCreate, extras?: WatchFormExtras) => {
    try {
      const created = await createMutation.mutateAsync(data)
      clearDraft(draftKey)
      setIsAddModalOpen(false)
      if (extras?.referencePhoto && created?.id) {
        // The watch is saved either way; a missing photo is not an error here
        await referencePhotoApi
          .save(created.id, extras.referencePhoto.watchbaseId)
          .catch(() => undefined)
        queryClient.invalidateQueries({ queryKey: ['watches'] })
      }
    } catch (error) {
      console.error('Failed to create watch:', error)
    }
  }

  const handleDeleteConfirm = async () => {
    if (deleteWatch) {
      try {
        await deleteMutation.mutateAsync(deleteWatch.id)
        setDeleteWatch(null)
      } catch (error) {
        console.error('Failed to delete watch:', error)
      }
    }
  }

  const handleExportAllPDF = async () => {
    try {
      // Build query params for collection filter if active
      const params = new URLSearchParams()
      if (filters.collection_id) {
        params.append('collection_id', filters.collection_id)
      }

      const response = await api.get(`/v1/watches/export/pdf?${params.toString()}`, {
        responseType: 'blob'
      })

      // Create blob URL and trigger download
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url

      // Generate filename
      const collectionName = filters.collection_id
        ? collections?.find(c => c.id === filters.collection_id)?.name || 'Collection'
        : 'My_Watch_Collection'
      link.download = `${collectionName.replace(' ', '_')}.pdf`

      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to export PDF:', error)
    }
  }

  const totalPages = data ? Math.ceil(data.total / limit) : 0

  if (error) {
    return (
      <AppLayout>
        <div className="text-center py-12">
          <p className="text-destructive">Failed to load watches. Please try again.</p>
        </div>
      </AppLayout>
    )
  }

  const activeFilterCount = [
    filters.brand_id,
    filters.movement_type_id,
    filters.condition,
    filters.collection_id,
    filters.min_price ?? filters.max_price,
    filters.min_value ?? filters.max_value,
    filters.purchase_date_from ?? filters.purchase_date_to,
  ].filter((v) => v !== undefined && v !== null && v !== '').length

  const totalValue = analytics ? Number(analytics.total_current_value) : null
  const totalPaid = analytics ? Number(analytics.total_purchase_price) : null
  const totalReturn = totalValue !== null && totalPaid ? gainPercent(totalValue, totalPaid) : null

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="mb-2 text-[11px] uppercase tracking-[0.3em] text-gold">Collection</p>
            <h1 className="text-3xl font-light tracking-wide text-foreground sm:text-4xl">My Watches</h1>
            {data && (
              <p className="mt-1 text-sm text-muted-foreground">
                {data.total} {data.total === 1 ? 'watch' : 'watches'} in your collection
              </p>
            )}
          </div>
          {analytics && analytics.total_watches > 0 && (
            <dl className="flex gap-8 text-right">
              <div>
                <dd className="text-2xl font-light text-foreground">{formatMoney(totalValue, analytics.currency)}</dd>
                <dt className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Market value</dt>
              </div>
              {totalReturn !== null && (
                <div>
                  <dd className={`text-2xl font-light ${totalReturn >= 0 ? 'text-positive' : 'text-negative'}`}>
                    {formatPercent(totalReturn)}
                  </dd>
                  <dt className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground">Total return</dt>
                </div>
              )}
            </dl>
          )}
        </div>

        {/* Toolbar: search, filters, actions */}
        <div className="flex flex-wrap items-stretch gap-2">
          <label className="relative min-w-[12rem] flex-1">
            <span className="sr-only">Search watches</span>
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search brand, model, reference"
              className="h-10 w-full rounded-sm border border-input bg-card pl-9 pr-3 text-sm text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </label>
          <Button
            variant="secondary"
            onClick={() => setShowFilters((v) => !v)}
            aria-expanded={showFilters}
            aria-controls="watch-filters"
          >
            <SlidersHorizontal className="h-4 w-4" />
            Filters{activeFilterCount > 0 ? ` (${activeFilterCount})` : ''}
          </Button>
          <Button
            onClick={() => setCompareMode(!isCompareMode)}
            variant={isCompareMode ? 'outline' : 'secondary'}
            aria-pressed={isCompareMode}
          >
            <GitCompare className="h-4 w-4" />
            <span className="hidden sm:inline">{isCompareMode ? 'Exit compare' : 'Compare'}</span>
            <span className="sm:hidden">{isCompareMode ? 'Done' : 'Compare'}</span>
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="secondary" size="icon" aria-label="More actions">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onSelect={handleExportAllPDF} disabled={!data || data.total === 0}>
                <FileDown className="mr-2 h-4 w-4" /> Export PDF
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <Button onClick={() => setIsAddModalOpen(true)}>
            <Plus className="h-4 w-4" />
            Add watch
          </Button>
        </div>

        {/* Filter Chips */}
        <FilterChips
          filters={filters}
          brands={brands}
          movementTypes={movementTypes}
          collections={collections}
          onRemoveFilter={handleRemoveFilter}
          onClearAll={handleClearAllFilters}
        />

        <div className={showFilters ? 'grid grid-cols-1 gap-6 lg:grid-cols-4' : ''}>
          {showFilters && (
            <div id="watch-filters" className="lg:col-span-1">
              <WatchFilters filters={filters} onFiltersChange={handleFiltersChange} showSearch={false} />
            </div>
          )}

          <div className={showFilters ? 'space-y-6 lg:col-span-3' : 'space-y-6'}>
            <WatchList
              watches={data?.items || []}
              isLoading={isLoading}
              isCompareMode={isCompareMode}
              selectedWatchIds={selectedWatchIds}
              onSelectionToggle={toggleWatch}
              onDelete={setDeleteWatch}
            />

            {data && data.total > limit && (
              <div className="flex justify-between items-center">
                <Button
                  variant="secondary"
                  disabled={page === 0}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                >
                  Previous
                </Button>

                <span className="text-sm text-muted-foreground">
                  Page {page + 1} of {totalPages}
                </span>

                <Button
                  variant="secondary"
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      {selectedWatchIds.length > 0 && (
        <ComparisonBar
          selectedCount={selectedWatchIds.length}
          onClear={clearSelection}
          onCompare={() => navigate(`/compare?ids=${selectedWatchIds.join(',')}`)}
        />
      )}

      <Modal
        isOpen={isAddModalOpen}
        onClose={() => {
          // Only after "Discard" or with nothing typed
          clearDraft(draftKey)
          setIsAddModalOpen(false)
        }}
        title="Add New Watch"
        size="xl"
        form
      >
        <WatchForm
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          onSubmit={handleCreateWatch as any}
          onCancel={() => setIsAddModalOpen(false)}
          isLoading={createMutation.isPending}
          draftKey={draftKey}
        />
      </Modal>

      <Modal
        isOpen={!!deleteWatch}
        onClose={() => setDeleteWatch(null)}
        title="Delete Watch"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-muted-foreground">
            Are you sure you want to delete{' '}
            <span className="font-medium text-foreground">
              {deleteWatch?.brand?.name} {deleteWatch?.model}
            </span>
            ? This action cannot be undone.
          </p>
          <div className="flex gap-3">
            <Button
              variant="danger"
              onClick={handleDeleteConfirm}
              disabled={deleteMutation.isPending}
              className="flex-1"
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </Button>
            <Button
              variant="secondary"
              onClick={() => setDeleteWatch(null)}
              disabled={deleteMutation.isPending}
            >
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </AppLayout>
  )
}

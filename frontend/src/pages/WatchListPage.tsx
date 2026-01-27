import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import AppLayout from '@/components/layout/AppLayout'
import WatchList from '@/components/watches/WatchList'
import WatchFilters from '@/components/watches/WatchFilters'
import WatchForm from '@/components/watches/WatchForm'
import Modal from '@/components/common/Modal'
import Button from '@/components/common/Button'
import { useWatches, useCreateWatch, useDeleteWatch } from '@/hooks/useWatches'
import type { WatchFilters as WatchFiltersType, WatchListItem, WatchCreate } from '@/types'

export default function WatchListPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [deleteWatch, setDeleteWatch] = useState<WatchListItem | null>(null)
  const [page, setPage] = useState(0)
  const limit = 20

  const [filters, setFilters] = useState<WatchFiltersType>({
    collection_id: searchParams.get('collection_id') || undefined,
    brand_id: searchParams.get('brand_id') || undefined,
    movement_type_id: searchParams.get('movement_type_id') || undefined,
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
  const createMutation = useCreateWatch()
  const deleteMutation = useDeleteWatch()

  const handleFiltersChange = (newFilters: WatchFiltersType) => {
    setFilters(newFilters)
    setPage(0)
  }

  const handleCreateWatch = async (data: WatchCreate) => {
    try {
      await createMutation.mutateAsync(data)
      setIsAddModalOpen(false)
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

  const totalPages = data ? Math.ceil(data.total / limit) : 0

  if (error) {
    return (
      <AppLayout>
        <div className="text-center py-12">
          <p className="text-red-600">Failed to load watches. Please try again.</p>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">My Watches</h1>
            {data && (
              <p className="mt-1 text-sm text-gray-600">
                {data.total} {data.total === 1 ? 'watch' : 'watches'} in your collection
              </p>
            )}
          </div>
          <Button onClick={() => setIsAddModalOpen(true)}>Add Watch</Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1">
            <WatchFilters filters={filters} onFiltersChange={handleFiltersChange} />
          </div>

          <div className="lg:col-span-3 space-y-6">
            <WatchList
              watches={data?.items || []}
              isLoading={isLoading}
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

                <span className="text-sm text-gray-600">
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

      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add New Watch"
        size="xl"
      >
        <WatchForm
          onSubmit={handleCreateWatch}
          onCancel={() => setIsAddModalOpen(false)}
          isLoading={createMutation.isPending}
        />
      </Modal>

      <Modal
        isOpen={!!deleteWatch}
        onClose={() => setDeleteWatch(null)}
        title="Delete Watch"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Are you sure you want to delete{' '}
            <span className="font-semibold">
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

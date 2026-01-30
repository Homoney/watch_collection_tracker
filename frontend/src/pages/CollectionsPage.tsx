import { useState } from 'react'
import AppLayout from '@/components/layout/AppLayout'
import CollectionList from '@/components/collections/CollectionList'
import CollectionForm from '@/components/collections/CollectionForm'
import Modal from '@/components/common/Modal'
import Button from '@/components/common/Button'
import {
  useCollections,
  useCreateCollection,
  useUpdateCollection,
  useDeleteCollection,
} from '@/hooks/useCollections'
import type { Collection, CollectionCreate, CollectionUpdate } from '@/types'

export default function CollectionsPage() {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [editingCollection, setEditingCollection] = useState<Collection | null>(null)
  const [deleteCollection, setDeleteCollection] = useState<Collection | null>(null)

  const { data: collections, isLoading, error } = useCollections()
  const createMutation = useCreateCollection()
  const updateMutation = useUpdateCollection()
  const deleteMutation = useDeleteCollection()

  const handleCreate = async (data: CollectionCreate) => {
    try {
      await createMutation.mutateAsync(data)
      setIsCreateModalOpen(false)
    } catch (error) {
      console.error('Failed to create collection:', error)
    }
  }

  const handleUpdate = async (data: CollectionUpdate) => {
    if (editingCollection) {
      try {
        await updateMutation.mutateAsync({
          id: editingCollection.id,
          data,
        })
        setEditingCollection(null)
      } catch (error) {
        console.error('Failed to update collection:', error)
      }
    }
  }

  const handleDeleteConfirm = async () => {
    if (deleteCollection) {
      try {
        await deleteMutation.mutateAsync(deleteCollection.id)
        setDeleteCollection(null)
      } catch (error) {
        console.error('Failed to delete collection:', error)
      }
    }
  }

  if (error) {
    return (
      <AppLayout>
        <div className="text-center py-12">
          <p className="text-red-600">Failed to load collections. Please try again.</p>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Collections</h1>
            {collections && (
              <p className="mt-1 text-sm text-gray-600">
                {collections.length} {collections.length === 1 ? 'collection' : 'collections'}
              </p>
            )}
          </div>
          <Button onClick={() => setIsCreateModalOpen(true)}>Create Collection</Button>
        </div>

        <CollectionList
          collections={collections || []}
          isLoading={isLoading}
          onEdit={setEditingCollection}
          onDelete={setDeleteCollection}
        />
      </div>

      {/* Create Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New Collection"
        size="md"
      >
        <CollectionForm
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          onSubmit={handleCreate as any}
          onCancel={() => setIsCreateModalOpen(false)}
          isLoading={createMutation.isPending}
        />
      </Modal>

      {/* Edit Modal */}
      <Modal
        isOpen={!!editingCollection}
        onClose={() => setEditingCollection(null)}
        title="Edit Collection"
        size="md"
      >
        {editingCollection && (
          <CollectionForm
            defaultValues={editingCollection}
            onSubmit={handleUpdate}
            onCancel={() => setEditingCollection(null)}
            isLoading={updateMutation.isPending}
          />
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deleteCollection}
        onClose={() => setDeleteCollection(null)}
        title="Delete Collection"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Are you sure you want to delete{' '}
            <span className="font-semibold">{deleteCollection?.name}</span>? Watches in this
            collection will not be deleted, but will be unassigned from the collection.
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
              onClick={() => setDeleteCollection(null)}
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

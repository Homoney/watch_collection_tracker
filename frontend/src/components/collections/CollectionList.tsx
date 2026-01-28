import { Edit, Trash2, FolderOpen } from 'lucide-react'
import type { Collection } from '@/types'

interface CollectionListProps {
  collections: Collection[]
  isLoading: boolean
  onEdit: (collection: Collection) => void
  onDelete: (collection: Collection) => void
}

const colorClasses: Record<string, string> = {
  '#3B82F6': 'bg-blue-500',
  '#10B981': 'bg-green-500',
  '#EF4444': 'bg-red-500',
  '#F59E0B': 'bg-yellow-500',
  '#8B5CF6': 'bg-purple-500',
  '#EC4899': 'bg-pink-500',
  '#6366F1': 'bg-indigo-500',
  '#6B7280': 'bg-gray-500',
}

export default function CollectionList({
  collections,
  isLoading,
  onEdit,
  onDelete,
}: CollectionListProps) {
  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (collections.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
        <FolderOpen className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No collections</h3>
        <p className="mt-1 text-sm text-gray-500">
          Get started by creating a new collection.
        </p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {collections.map((collection) => (
        <div
          key={collection.id}
          className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3 flex-1">
              <div
                className={`w-4 h-4 rounded-full ${colorClasses[collection.color] || ''}`}
                style={!colorClasses[collection.color] ? { backgroundColor: collection.color } : undefined}
              />
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-semibold text-gray-900 truncate">
                  {collection.name}
                </h3>
                {collection.description && (
                  <p className="mt-1 text-sm text-gray-500 line-clamp-2">
                    {collection.description}
                  </p>
                )}
                <p className="mt-2 text-sm text-gray-600">
                  {collection.watch_count || 0}{' '}
                  {collection.watch_count === 1 ? 'watch' : 'watches'}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 ml-2">
              <button
                type="button"
                onClick={() => onEdit(collection)}
                className="p-2 text-gray-400 hover:text-blue-600 rounded-md hover:bg-gray-100"
                title="Edit collection"
              >
                <Edit className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={() => onDelete(collection)}
                className="p-2 text-gray-400 hover:text-red-600 rounded-md hover:bg-gray-100"
                title="Delete collection"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

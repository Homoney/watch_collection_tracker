import WatchCard from './WatchCard'
import Spinner from '@/components/common/Spinner'
import type { WatchListItem } from '@/types'

interface WatchListProps {
  watches: WatchListItem[]
  isLoading?: boolean
  onEdit?: (watch: WatchListItem) => void
  onDelete?: (watch: WatchListItem) => void
}

export default function WatchList({ watches, isLoading, onEdit, onDelete }: WatchListProps) {
  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  if (watches.length === 0) {
    return (
      <div className="text-center py-12">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900">No watches found</h3>
        <p className="mt-1 text-sm text-gray-500">Get started by adding your first watch.</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {watches.map((watch) => (
        <WatchCard key={watch.id} watch={watch} onEdit={onEdit} onDelete={onDelete} />
      ))}
    </div>
  )
}

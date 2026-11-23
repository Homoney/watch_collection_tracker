import WatchCard from './WatchCard'
import Spinner from '@/components/common/Spinner'
import WatchDial from './WatchDial'
import type { WatchListItem } from '@/types'

interface WatchListProps {
  watches: WatchListItem[]
  isLoading?: boolean
  isCompareMode?: boolean
  selectedWatchIds?: string[]
  onSelectionToggle?: (id: string) => void
  onEdit?: (watch: WatchListItem) => void
  onDelete?: (watch: WatchListItem) => void
}

export default function WatchList({
  watches,
  isLoading,
  isCompareMode = false,
  selectedWatchIds = [],
  onSelectionToggle,
  onEdit,
  onDelete
}: WatchListProps) {
  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  if (watches.length === 0) {
    return (
      <div className="flex flex-col items-center border border-border bg-card px-6 py-16 text-center">
        <WatchDial className="h-20 w-20 opacity-70" />
        <h3 className="mt-4 text-lg font-light tracking-wide text-foreground">No watches found</h3>
        <p className="mt-1 text-sm text-muted-foreground">Add your first watch, or clear the filters.</p>
      </div>
    )
  }

  return (
    // 1 px gaps on a hairline-coloured ground: the cards read as one tray
    <div className="grid grid-cols-2 gap-px border border-border bg-border md:grid-cols-3 xl:grid-cols-4">
      {watches.map((watch) => (
        <WatchCard
          key={watch.id}
          watch={watch}
          isCompareMode={isCompareMode}
          isSelected={selectedWatchIds.includes(watch.id)}
          onSelectionToggle={onSelectionToggle}
          onEdit={onEdit}
          onDelete={onDelete}
        />
      ))}
    </div>
  )
}

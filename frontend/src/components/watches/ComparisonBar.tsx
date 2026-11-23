import Button from '@/components/common/Button'

interface ComparisonBarProps {
  selectedCount: number
  onClear: () => void
  onCompare: () => void
}

export default function ComparisonBar({ selectedCount, onClear, onCompare }: ComparisonBarProps) {
  return (
    <div className="fixed bottom-16 left-0 right-0 z-50 border-t border-border bg-popover p-3 text-popover-foreground shadow-lg md:bottom-0 md:p-4">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-4">
          <span className="text-base text-foreground">
            {selectedCount} {selectedCount === 1 ? 'watch' : 'watches'} selected
          </span>
          {selectedCount < 2 && (
            <span className="hidden text-sm text-muted-foreground sm:inline">
              Select at least 2 watches to compare
            </span>
          )}
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" size="sm" onClick={onClear}>
            Clear
          </Button>
          <Button size="sm" onClick={onCompare} disabled={selectedCount < 2}>
            Compare
          </Button>
        </div>
      </div>
    </div>
  )
}

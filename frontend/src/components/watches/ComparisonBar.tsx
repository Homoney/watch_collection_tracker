interface ComparisonBarProps {
  selectedCount: number
  onClear: () => void
  onCompare: () => void
}

export default function ComparisonBar({ selectedCount, onClear, onCompare }: ComparisonBarProps) {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 shadow-lg border-t border-gray-200 dark:border-gray-700 p-4 z-50">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-lg font-medium dark:text-white">
            {selectedCount} {selectedCount === 1 ? 'watch' : 'watches'} selected
          </span>
          {selectedCount < 2 && (
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Select at least 2 watches to compare
            </span>
          )}
        </div>
        <div className="flex gap-3">
          <button
            onClick={onClear}
            className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            Clear
          </button>
          <button
            onClick={onCompare}
            disabled={selectedCount < 2}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
          >
            Compare →
          </button>
        </div>
      </div>
    </div>
  )
}

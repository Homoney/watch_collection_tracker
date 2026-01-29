/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useState, ReactNode } from 'react'

interface ComparisonContextType {
  selectedWatchIds: string[]
  isCompareMode: boolean
  toggleWatch: (id: string) => void
  clearSelection: () => void
  setCompareMode: (enabled: boolean) => void
  canSelectMore: boolean
}

const ComparisonContext = createContext<ComparisonContextType | undefined>(undefined)

const MAX_WATCHES = 4

export function ComparisonProvider({ children }: { children: ReactNode }) {
  const [selectedWatchIds, setSelectedWatchIds] = useState<string[]>([])
  const [isCompareMode, setIsCompareMode] = useState(false)

  const toggleWatch = (id: string) => {
    setSelectedWatchIds(prev => {
      if (prev.includes(id)) {
        return prev.filter(watchId => watchId !== id)
      } else if (prev.length < MAX_WATCHES) {
        return [...prev, id]
      }
      return prev
    })
  }

  const clearSelection = () => {
    setSelectedWatchIds([])
  }

  const handleSetCompareMode = (enabled: boolean) => {
    setIsCompareMode(enabled)
    if (!enabled) {
      clearSelection()
    }
  }

  const canSelectMore = selectedWatchIds.length < MAX_WATCHES

  return (
    <ComparisonContext.Provider
      value={{
        selectedWatchIds,
        isCompareMode,
        toggleWatch,
        clearSelection,
        setCompareMode: handleSetCompareMode,
        canSelectMore,
      }}
    >
      {children}
    </ComparisonContext.Provider>
  )
}

export function useComparison() {
  const context = useContext(ComparisonContext)
  if (context === undefined) {
    throw new Error('useComparison must be used within a ComparisonProvider')
  }
  return context
}

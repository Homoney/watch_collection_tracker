import { X } from 'lucide-react'
import type { WatchFilters, Brand, MovementType, Collection } from '@/types'

interface FilterChipsProps {
  filters: WatchFilters
  brands?: Brand[]
  movementTypes?: MovementType[]
  collections?: Collection[]
  onRemoveFilter: (filterKey: keyof WatchFilters) => void
  onClearAll: () => void
}

export default function FilterChips({
  filters,
  brands,
  movementTypes,
  collections,
  onRemoveFilter,
  onClearAll,
}: FilterChipsProps) {
  const chips: { key: keyof WatchFilters; label: string }[] = []

  // Search
  if (filters.search) {
    chips.push({ key: 'search', label: `Search: "${filters.search}"` })
  }

  // Brand
  if (filters.brand_id && brands) {
    const brand = brands.find((b) => b.id === filters.brand_id)
    if (brand) {
      chips.push({ key: 'brand_id', label: `Brand: ${brand.name}` })
    }
  }

  // Movement Type
  if (filters.movement_type_id && movementTypes) {
    const movementType = movementTypes.find((mt) => mt.id === filters.movement_type_id)
    if (movementType) {
      chips.push({ key: 'movement_type_id', label: `Movement: ${movementType.name}` })
    }
  }

  // Collection
  if (filters.collection_id && collections) {
    const collection = collections.find((c) => c.id === filters.collection_id)
    if (collection) {
      chips.push({ key: 'collection_id', label: `Collection: ${collection.name}` })
    }
  }

  // Condition
  if (filters.condition) {
    chips.push({
      key: 'condition',
      label: `Condition: ${filters.condition.charAt(0).toUpperCase() + filters.condition.slice(1)}`,
    })
  }

  // Price Range
  if (filters.min_price) {
    chips.push({ key: 'min_price', label: `Min Price: $${filters.min_price}` })
  }
  if (filters.max_price) {
    chips.push({ key: 'max_price', label: `Max Price: $${filters.max_price}` })
  }

  // Market Value Range
  if (filters.min_value) {
    chips.push({ key: 'min_value', label: `Min Value: $${filters.min_value}` })
  }
  if (filters.max_value) {
    chips.push({ key: 'max_value', label: `Max Value: $${filters.max_value}` })
  }

  // Date Range
  if (filters.purchase_date_from) {
    chips.push({
      key: 'purchase_date_from',
      label: `From: ${new Date(filters.purchase_date_from).toLocaleDateString()}`,
    })
  }
  if (filters.purchase_date_to) {
    chips.push({
      key: 'purchase_date_to',
      label: `To: ${new Date(filters.purchase_date_to).toLocaleDateString()}`,
    })
  }

  if (chips.length === 0) return null

  return (
    <div className="flex flex-wrap gap-2 items-center">
      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Active Filters:</span>
      {chips.map((chip) => (
        <button
          key={chip.key}
          onClick={() => onRemoveFilter(chip.key)}
          className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200 hover:bg-blue-200 dark:hover:bg-blue-900 transition-colors"
        >
          {chip.label}
          <X className="h-3 w-3" />
        </button>
      ))}
      <button
        onClick={onClearAll}
        className="text-sm text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 font-medium"
      >
        Clear All
      </button>
    </div>
  )
}

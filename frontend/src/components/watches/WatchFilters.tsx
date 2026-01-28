import { useEffect, useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import Input from '@/components/common/Input'
import Select from '@/components/common/Select'
import Button from '@/components/common/Button'
import { useBrands, useMovementTypes } from '@/hooks/useReferenceData'
import { useCollections } from '@/hooks/useCollections'
import type { WatchFilters as WatchFiltersType } from '@/types'

interface WatchFiltersProps {
  filters: WatchFiltersType
  onFiltersChange: (filters: WatchFiltersType) => void
}

const conditionOptions = [
  { value: '', label: 'All Conditions' },
  { value: 'mint', label: 'Mint' },
  { value: 'excellent', label: 'Excellent' },
  { value: 'good', label: 'Good' },
  { value: 'fair', label: 'Fair' },
  { value: 'poor', label: 'Poor' },
]

const sortOptions = [
  { value: 'created_at', label: 'Date Added' },
  { value: 'purchase_date', label: 'Purchase Date' },
  { value: 'purchase_price', label: 'Purchase Price' },
  { value: 'model', label: 'Model' },
]

const sortOrderOptions = [
  { value: 'desc', label: 'Descending' },
  { value: 'asc', label: 'Ascending' },
]

export default function WatchFilters({ filters, onFiltersChange }: WatchFiltersProps) {
  const { data: brands } = useBrands()
  const { data: movementTypes } = useMovementTypes()
  const { data: collections } = useCollections()

  const [search, setSearch] = useState(filters.search || '')
  const [showAdvanced, setShowAdvanced] = useState(false)

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (search !== filters.search) {
        onFiltersChange({ ...filters, search: search || undefined })
      }
    }, 500)

    return () => clearTimeout(timeoutId)
  }, [search])

  const handleClearFilters = () => {
    setSearch('')
    onFiltersChange({
      sort_by: 'created_at',
      sort_order: 'desc',
    })
  }

  const hasActiveFilters =
    filters.search ||
    filters.brand_id ||
    filters.movement_type_id ||
    filters.condition ||
    filters.collection_id ||
    filters.min_price ||
    filters.max_price ||
    filters.min_value ||
    filters.max_value ||
    filters.purchase_date_from ||
    filters.purchase_date_to

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Filters</h3>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={handleClearFilters}>
            Clear All
          </Button>
        )}
      </div>

      <Input
        placeholder="Search watches..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <Select
        label="Brand"
        value={filters.brand_id || ''}
        onChange={(e) =>
          onFiltersChange({ ...filters, brand_id: e.target.value || undefined })
        }
        options={[
          { value: '', label: 'All Brands' },
          ...(brands?.map((b) => ({ value: b.id, label: b.name })) || []),
        ]}
      />

      <Select
        label="Movement Type"
        value={filters.movement_type_id || ''}
        onChange={(e) =>
          onFiltersChange({ ...filters, movement_type_id: e.target.value || undefined })
        }
        options={[
          { value: '', label: 'All Movement Types' },
          ...(movementTypes?.map((mt) => ({ value: mt.id, label: mt.name })) || []),
        ]}
      />

      <Select
        label="Collection"
        value={filters.collection_id || ''}
        onChange={(e) =>
          onFiltersChange({ ...filters, collection_id: e.target.value || undefined })
        }
        options={[
          { value: '', label: 'All Collections' },
          ...(collections?.map((c) => ({ value: c.id, label: c.name })) || []),
        ]}
      />

      <Select
        label="Condition"
        value={filters.condition || ''}
        onChange={(e) =>
          onFiltersChange({
            ...filters,
            condition: (e.target.value as any) || undefined,
          })
        }
        options={conditionOptions}
      />

      {/* Advanced Filters Section */}
      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center justify-between w-full text-sm font-medium text-gray-900 dark:text-white mb-3"
        >
          <span>Advanced Filters</span>
          {showAdvanced ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </button>

        {showAdvanced && (
          <div className="space-y-4">
            {/* Price Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Purchase Price Range
              </label>
              <div className="grid grid-cols-2 gap-2">
                <Input
                  type="number"
                  placeholder="Min"
                  value={filters.min_price || ''}
                  onChange={(e) =>
                    onFiltersChange({
                      ...filters,
                      min_price: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                />
                <Input
                  type="number"
                  placeholder="Max"
                  value={filters.max_price || ''}
                  onChange={(e) =>
                    onFiltersChange({
                      ...filters,
                      max_price: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                />
              </div>
            </div>

            {/* Market Value Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Market Value Range
              </label>
              <div className="grid grid-cols-2 gap-2">
                <Input
                  type="number"
                  placeholder="Min"
                  value={filters.min_value || ''}
                  onChange={(e) =>
                    onFiltersChange({
                      ...filters,
                      min_value: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                />
                <Input
                  type="number"
                  placeholder="Max"
                  value={filters.max_value || ''}
                  onChange={(e) =>
                    onFiltersChange({
                      ...filters,
                      max_value: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                />
              </div>
            </div>

            {/* Purchase Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Purchase Date Range
              </label>
              <div className="grid grid-cols-2 gap-2">
                <Input
                  type="date"
                  placeholder="From"
                  value={filters.purchase_date_from || ''}
                  onChange={(e) =>
                    onFiltersChange({
                      ...filters,
                      purchase_date_from: e.target.value || undefined,
                    })
                  }
                />
                <Input
                  type="date"
                  placeholder="To"
                  value={filters.purchase_date_to || ''}
                  onChange={(e) =>
                    onFiltersChange({
                      ...filters,
                      purchase_date_to: e.target.value || undefined,
                    })
                  }
                />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Sort By</h4>

        <Select
          value={filters.sort_by || 'created_at'}
          onChange={(e) => onFiltersChange({ ...filters, sort_by: e.target.value })}
          options={sortOptions}
        />

        <div className="mt-2">
          <Select
            value={filters.sort_order || 'desc'}
            onChange={(e) =>
              onFiltersChange({ ...filters, sort_order: e.target.value as 'asc' | 'desc' })
            }
            options={sortOrderOptions}
          />
        </div>
      </div>
    </div>
  )
}

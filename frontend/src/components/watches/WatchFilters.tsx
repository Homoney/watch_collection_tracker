import { useEffect, useState } from 'react'
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
    filters.collection_id

  return (
    <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200 space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
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

      <div className="pt-4 border-t border-gray-200">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Sort By</h4>

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

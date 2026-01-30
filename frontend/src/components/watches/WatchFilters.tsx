import { useEffect, useState } from 'react'
import { ChevronDown, ChevronUp, Save, Star } from 'lucide-react'
import Input from '@/components/common/Input'
import Select from '@/components/common/Select'
import Button from '@/components/common/Button'
import { useBrands, useMovementTypes } from '@/hooks/useReferenceData'
import { useCollections } from '@/hooks/useCollections'
import { useSavedSearches, useCreateSavedSearch, useDeleteSavedSearch } from '@/hooks/useSavedSearches'
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
  const { data: savedSearches } = useSavedSearches()
  const createSavedSearch = useCreateSavedSearch()
  const deleteSavedSearch = useDeleteSavedSearch()

  const [search, setSearch] = useState(filters.search || '')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [showSaveDialog, setShowSaveDialog] = useState(false)
  const [searchName, setSearchName] = useState('')

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (search !== filters.search) {
        onFiltersChange({ ...filters, search: search || undefined })
      }
    }, 500)

    return () => clearTimeout(timeoutId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  const handleSaveSearch = async () => {
    if (!searchName.trim()) return

    try {
      await createSavedSearch.mutateAsync({
        name: searchName.trim(),
        filters: filters,
      })
      setSearchName('')
      setShowSaveDialog(false)
    } catch (error) {
      console.error('Failed to save search:', error)
    }
  }

  const handleLoadSearch = (savedSearch: { filters: WatchFiltersType }) => {
    onFiltersChange(savedSearch.filters)
    setSearch(savedSearch.filters.search || '')
  }

  const handleDeleteSearch = async (searchId: string) => {
    try {
      await deleteSavedSearch.mutateAsync(searchId)
    } catch (error) {
      console.error('Failed to delete search:', error)
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Filters</h3>
        <div className="flex gap-2">
          {hasActiveFilters && (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowSaveDialog(!showSaveDialog)}
              >
                <Save className="h-4 w-4 mr-1" />
                Save
              </Button>
              <Button variant="ghost" size="sm" onClick={handleClearFilters}>
                Clear All
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Save Search Dialog */}
      {showSaveDialog && (
        <div className="p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md space-y-2">
          <label className="block text-sm font-medium text-gray-900 dark:text-white">
            Save current filters as:
          </label>
          <div className="flex gap-2">
            <Input
              placeholder="Search name..."
              value={searchName}
              onChange={(e) => setSearchName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSaveSearch()}
            />
            <Button size="sm" onClick={handleSaveSearch} disabled={!searchName.trim()}>
              Save
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setShowSaveDialog(false)
                setSearchName('')
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {/* Saved Searches */}
      {savedSearches && savedSearches.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-900 dark:text-white mb-2">
            Saved Searches
          </label>
          <div className="space-y-1">
            {savedSearches.map((savedSearch) => (
              <div
                key={savedSearch.id}
                className="flex items-center justify-between p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
              >
                <button
                  onClick={() => handleLoadSearch(savedSearch)}
                  className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 flex-1 text-left"
                >
                  <Star className="h-4 w-4" />
                  {savedSearch.name}
                </button>
                <button
                  onClick={() => handleDeleteSearch(savedSearch.id)}
                  className="text-xs text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300"
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

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
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
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

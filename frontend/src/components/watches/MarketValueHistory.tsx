import { useState } from 'react'
import { Calendar, TrendingUp, TrendingDown, Edit, Trash2, DollarSign } from 'lucide-react'
import { MarketValue } from '@/types'
import { useMarketValues, useDeleteMarketValue } from '@/hooks/useMarketValues'
import { format } from 'date-fns'

interface MarketValueHistoryProps {
  watchId: string
  onAddValue: () => void
  onEditValue: (value: MarketValue) => void
}

export default function MarketValueHistory({
  watchId,
  onAddValue,
  onEditValue,
}: MarketValueHistoryProps) {
  const { data: values, isLoading, error } = useMarketValues(watchId)
  const deleteMutation = useDeleteMarketValue()
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMMM d, yyyy')
  }

  const formatValue = (value: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(value)
  }

  const calculateChange = (current: number, previous: number) => {
    const change = current - previous
    const changePercent = (change / previous) * 100
    return { change, changePercent }
  }

  const handleDelete = async (valueId: string) => {
    try {
      await deleteMutation.mutateAsync({ watchId, valueId })
      setDeleteConfirmId(null)
    } catch (error) {
      console.error('Failed to delete market value:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800">Failed to load market value history</p>
      </div>
    )
  }

  if (!values || values.length === 0) {
    return (
      <div className="text-center py-12">
        <DollarSign className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No value history</h3>
        <p className="mt-1 text-sm text-gray-500">
          Start tracking your watch's market value over time.
        </p>
        <div className="mt-6">
          <button
            type="button"
            onClick={onAddValue}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            Add Market Value
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium text-gray-900">
          Value History ({values.length})
        </h3>
        <button
          type="button"
          onClick={onAddValue}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          Add Value
        </button>
      </div>

      <div className="space-y-3">
        {values.map((value, index) => {
          const previousValue = index < values.length - 1 ? values[index + 1] : null
          let changeInfo = null

          if (previousValue && previousValue.currency === value.currency) {
            changeInfo = calculateChange(Number(value.value), Number(previousValue.value))
          }

          return (
            <div
              key={value.id}
              className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Date */}
                  <div className="flex items-center gap-2 mb-2">
                    <Calendar className="h-4 w-4 text-gray-400" />
                    <span className="font-medium text-gray-900">
                      {formatDate(value.recorded_at)}
                    </span>
                    {index === 0 && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                        Current
                      </span>
                    )}
                  </div>

                  <div className="ml-6 space-y-2">
                    {/* Value */}
                    <div className="flex items-baseline gap-2">
                      <span className="text-2xl font-bold text-gray-900">
                        {formatValue(Number(value.value), value.currency)}
                      </span>
                      {changeInfo && (
                        <span
                          className={`flex items-center gap-1 text-sm font-medium ${
                            changeInfo.change >= 0 ? 'text-green-600' : 'text-red-600'
                          }`}
                        >
                          {changeInfo.change >= 0 ? (
                            <TrendingUp className="h-4 w-4" />
                          ) : (
                            <TrendingDown className="h-4 w-4" />
                          )}
                          {Math.abs(changeInfo.changePercent).toFixed(1)}%
                        </span>
                      )}
                    </div>

                    {/* Source */}
                    <p className="text-sm text-gray-600">
                      <span className="font-medium">Source:</span>{' '}
                      {value.source === 'manual'
                        ? 'Manual Entry'
                        : value.source === 'chrono24'
                        ? 'Chrono24'
                        : 'API/External'}
                    </p>

                    {/* Notes */}
                    {value.notes && (
                      <p className="text-sm text-gray-600">{value.notes}</p>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 ml-4">
                  <button
                    type="button"
                    onClick={() => onEditValue(value)}
                    className="p-2 text-gray-400 hover:text-blue-600 rounded-md hover:bg-gray-100"
                    title="Edit value"
                  >
                    <Edit className="h-4 w-4" />
                  </button>

                  {deleteConfirmId === value.id ? (
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleDelete(value.id)}
                        disabled={deleteMutation.isPending}
                        className="px-2 py-1 text-xs font-medium text-white bg-red-600 hover:bg-red-700 rounded"
                      >
                        Confirm
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeleteConfirmId(null)}
                        className="px-2 py-1 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setDeleteConfirmId(value.id)}
                      className="p-2 text-gray-400 hover:text-red-600 rounded-md hover:bg-gray-100"
                      title="Delete value"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

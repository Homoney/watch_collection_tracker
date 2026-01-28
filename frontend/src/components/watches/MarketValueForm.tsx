import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { X } from 'lucide-react'
import { MarketValue, MarketValueCreate, MarketValueUpdate } from '@/types'
import {
  useCreateMarketValue,
  useUpdateMarketValue,
} from '@/hooks/useMarketValues'

interface MarketValueFormProps {
  watchId: string
  marketValue?: MarketValue
  onSuccess: () => void
  onCancel: () => void
}

const CURRENCIES = ['USD', 'EUR', 'GBP', 'CHF', 'JPY', 'AUD', 'CAD']
const SOURCES = [
  { value: 'manual', label: 'Manual Entry' },
  { value: 'chrono24', label: 'Chrono24' },
  { value: 'api', label: 'API/External' },
]

export default function MarketValueForm({
  watchId,
  marketValue,
  onSuccess,
  onCancel,
}: MarketValueFormProps) {
  const isEditing = !!marketValue
  const createMutation = useCreateMarketValue()
  const updateMutation = useUpdateMarketValue()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<MarketValueCreate>({
    defaultValues: marketValue
      ? {
          value: Number(marketValue.value),
          currency: marketValue.currency,
          source: marketValue.source,
          notes: marketValue.notes || '',
          recorded_at: marketValue.recorded_at.split('T')[0],
        }
      : {
          value: 0,
          currency: 'USD',
          source: 'manual',
          notes: '',
          recorded_at: new Date().toISOString().split('T')[0],
        },
  })

  useEffect(() => {
    if (marketValue) {
      reset({
        value: Number(marketValue.value),
        currency: marketValue.currency,
        source: marketValue.source,
        notes: marketValue.notes || '',
        recorded_at: marketValue.recorded_at.split('T')[0],
      })
    }
  }, [marketValue, reset])

  const onSubmit = async (data: MarketValueCreate) => {
    try {
      // Convert date to ISO string
      const submitData: MarketValueCreate = {
        ...data,
        recorded_at: data.recorded_at
          ? new Date(data.recorded_at).toISOString()
          : new Date().toISOString(),
        notes: data.notes || undefined,
      }

      if (isEditing) {
        await updateMutation.mutateAsync({
          watchId,
          valueId: marketValue.id,
          data: submitData as MarketValueUpdate,
        })
      } else {
        await createMutation.mutateAsync({
          watchId,
          data: submitData,
        })
      }

      onSuccess()
    } catch (error) {
      console.error('Failed to save market value:', error)
    }
  }

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            {isEditing ? 'Edit Market Value' : 'Add Market Value'}
          </h2>
          <button
            type="button"
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
          {/* Value and Currency */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="value" className="block text-sm font-medium text-gray-700">
                Market Value <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                id="value"
                step="0.01"
                min="0"
                {...register('value', {
                  required: 'Value is required',
                  valueAsNumber: true,
                  min: { value: 0, message: 'Value must be positive' },
                })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
              {errors.value && (
                <p className="mt-1 text-sm text-red-600">{errors.value.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="currency" className="block text-sm font-medium text-gray-700">
                Currency
              </label>
              <select
                id="currency"
                {...register('currency')}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                {CURRENCIES.map((curr) => (
                  <option key={curr} value={curr}>
                    {curr}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Recorded Date */}
          <div>
            <label htmlFor="recorded_at" className="block text-sm font-medium text-gray-700">
              Valuation Date <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              id="recorded_at"
              {...register('recorded_at', { required: 'Date is required' })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
            {errors.recorded_at && (
              <p className="mt-1 text-sm text-red-600">{errors.recorded_at.message}</p>
            )}
          </div>

          {/* Source */}
          <div>
            <label htmlFor="source" className="block text-sm font-medium text-gray-700">
              Source
            </label>
            <select
              id="source"
              {...register('source')}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              {SOURCES.map((src) => (
                <option key={src.value} value={src.value}>
                  {src.label}
                </option>
              ))}
            </select>
          </div>

          {/* Notes */}
          <div>
            <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
              Notes
            </label>
            <textarea
              id="notes"
              {...register('notes')}
              rows={3}
              placeholder="Optional notes about this valuation..."
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
          </div>

          {/* Form Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:bg-blue-300"
            >
              {isSubmitting ? 'Saving...' : isEditing ? 'Update' : 'Add Value'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

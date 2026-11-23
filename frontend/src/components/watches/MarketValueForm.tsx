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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="market-value-form-title"
        className="w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-sm border border-border bg-card text-card-foreground shadow-2xl"
      >
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-card px-6 py-4">
          <h2 id="market-value-form-title" className="text-lg font-light tracking-wide text-foreground">
            {isEditing ? 'Edit Market Value' : 'Add Market Value'}
          </h2>
          <button
            type="button"
            onClick={onCancel}
            aria-label="Close"
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
          {/* Value and Currency */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="value" className="block text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
                Market Value <span className="text-destructive">*</span>
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
                className="mt-1 block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
              />
              {errors.value && (
                <p className="mt-1 text-sm text-destructive">{errors.value.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="currency" className="block text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
                Currency
              </label>
              <select
                id="currency"
                {...register('currency')}
                className="mt-1 block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
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
            <label htmlFor="recorded_at" className="block text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Valuation Date <span className="text-destructive">*</span>
            </label>
            <input
              type="date"
              id="recorded_at"
              {...register('recorded_at', { required: 'Date is required' })}
              className="mt-1 block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
            />
            {errors.recorded_at && (
              <p className="mt-1 text-sm text-destructive">{errors.recorded_at.message}</p>
            )}
          </div>

          {/* Source */}
          <div>
            <label htmlFor="source" className="block text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Source
            </label>
            <select
              id="source"
              {...register('source')}
              className="mt-1 block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
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
            <label htmlFor="notes" className="block text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Notes
            </label>
            <textarea
              id="notes"
              {...register('notes')}
              rows={3}
              placeholder="Optional notes about this valuation..."
              className="mt-1 block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
            />
          </div>

          {/* Form Actions */}
          <div className="flex justify-end gap-3 border-t border-border pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-sm border border-input bg-transparent px-5 text-[11px] font-medium uppercase tracking-[0.18em] text-foreground hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex h-10 items-center justify-center gap-2 rounded-sm border border-primary bg-primary px-5 text-[11px] font-medium uppercase tracking-[0.18em] text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : isEditing ? 'Update' : 'Add Value'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

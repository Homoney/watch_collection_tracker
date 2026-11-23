import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { X } from 'lucide-react'
import { ServiceHistory, ServiceHistoryCreate, ServiceHistoryUpdate } from '@/types'
import {
  useCreateServiceHistory,
  useUpdateServiceHistory,
} from '@/hooks/useServiceHistory'

interface ServiceHistoryFormProps {
  watchId: string
  service?: ServiceHistory
  onSuccess: () => void
  onCancel: () => void
}

const COMMON_SERVICE_TYPES = [
  'Full Service',
  'Regulation',
  'Battery Replacement',
  'Crystal Replacement',
  'Bracelet Adjustment',
  'Water Resistance Test',
  'Polishing',
  'Other',
]

const CURRENCIES = ['USD', 'EUR', 'GBP', 'CHF', 'JPY', 'AUD', 'CAD']

export default function ServiceHistoryForm({
  watchId,
  service,
  onSuccess,
  onCancel,
}: ServiceHistoryFormProps) {
  const isEditing = !!service
  const createMutation = useCreateServiceHistory()
  const updateMutation = useUpdateServiceHistory()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<ServiceHistoryCreate>({
    defaultValues: service
      ? {
          service_date: service.service_date.split('T')[0],
          provider: service.provider,
          service_type: service.service_type || '',
          description: service.description || '',
          cost: service.cost || undefined,
          cost_currency: service.cost_currency,
          next_service_due: service.next_service_due
            ? service.next_service_due.split('T')[0]
            : '',
        }
      : {
          service_date: new Date().toISOString().split('T')[0],
          provider: '',
          service_type: '',
          description: '',
          cost_currency: 'USD',
          next_service_due: '',
        },
  })

  useEffect(() => {
    if (service) {
      reset({
        service_date: service.service_date.split('T')[0],
        provider: service.provider,
        service_type: service.service_type || '',
        description: service.description || '',
        cost: service.cost || undefined,
        cost_currency: service.cost_currency,
        next_service_due: service.next_service_due
          ? service.next_service_due.split('T')[0]
          : '',
      })
    }
  }, [service, reset])

  const onSubmit = async (data: ServiceHistoryCreate) => {
    try {
      // Convert empty strings to undefined for optional fields
      const submitData: ServiceHistoryCreate = {
        service_date: new Date(data.service_date).toISOString(),
        provider: data.provider,
        service_type: data.service_type || undefined,
        description: data.description || undefined,
        cost: data.cost || undefined,
        cost_currency: data.cost_currency || 'USD',
        next_service_due: data.next_service_due
          ? new Date(data.next_service_due).toISOString()
          : undefined,
      }

      if (isEditing) {
        await updateMutation.mutateAsync({
          watchId,
          serviceId: service.id,
          data: submitData as ServiceHistoryUpdate,
        })
      } else {
        await createMutation.mutateAsync({
          watchId,
          data: submitData,
        })
      }

      onSuccess()
    } catch (error) {
      console.error('Failed to save service record:', error)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="service-form-title"
        className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-sm border border-border bg-card text-card-foreground shadow-2xl"
      >
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-card px-6 py-4">
          <h2 id="service-form-title" className="text-lg font-light tracking-wide text-foreground">
            {isEditing ? 'Edit Service Record' : 'Add Service Record'}
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
          {/* Service Date */}
          <div>
            <label htmlFor="service_date" className="block text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Service Date <span className="text-destructive">*</span>
            </label>
            <input
              type="date"
              id="service_date"
              {...register('service_date', { required: 'Service date is required' })}
              className="mt-1 block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
            />
            {errors.service_date && (
              <p className="mt-1 text-sm text-destructive">{errors.service_date.message}</p>
            )}
          </div>

          {/* Provider */}
          <div>
            <label htmlFor="provider" className="block text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Service Provider <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              id="provider"
              {...register('provider', {
                required: 'Provider is required',
                minLength: { value: 1, message: 'Provider name is required' },
              })}
              placeholder="e.g., Rolex Service Center"
              className="mt-1 block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
            />
            {errors.provider && (
              <p className="mt-1 text-sm text-destructive">{errors.provider.message}</p>
            )}
          </div>

          {/* Service Type */}
          <div>
            <label htmlFor="service_type" className="block text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Service Type
            </label>
            <select
              id="service_type"
              {...register('service_type')}
              className="mt-1 block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
            >
              <option value="">Select a service type...</option>
              {COMMON_SERVICE_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
              Description
            </label>
            <textarea
              id="description"
              {...register('description')}
              rows={3}
              placeholder="Additional details about the service..."
              className="mt-1 block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
            />
          </div>

          {/* Cost and Currency */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="cost" className="block text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
                Cost
              </label>
              <input
                type="number"
                id="cost"
                step="0.01"
                min="0"
                {...register('cost', {
                  valueAsNumber: true,
                  min: { value: 0, message: 'Cost must be positive' },
                })}
                placeholder="0.00"
                className="mt-1 block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
              />
              {errors.cost && (
                <p className="mt-1 text-sm text-destructive">{errors.cost.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="cost_currency" className="block text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
                Currency
              </label>
              <select
                id="cost_currency"
                {...register('cost_currency')}
                className="mt-1 block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
              >
                {CURRENCIES.map((currency) => (
                  <option key={currency} value={currency}>
                    {currency}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Next Service Due */}
          <div>
            <label
              htmlFor="next_service_due"
              className="block text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground"
            >
              Next Service Due
            </label>
            <input
              type="date"
              id="next_service_due"
              {...register('next_service_due')}
              className="mt-1 block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
            />
            <p className="mt-1 text-sm text-muted-foreground">
              Optional: Set a reminder for the next service date
            </p>
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
              {isSubmitting ? 'Saving...' : isEditing ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

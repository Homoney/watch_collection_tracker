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
    <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            {isEditing ? 'Edit Service Record' : 'Add Service Record'}
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
          {/* Service Date */}
          <div>
            <label htmlFor="service_date" className="block text-sm font-medium text-gray-700">
              Service Date <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              id="service_date"
              {...register('service_date', { required: 'Service date is required' })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
            {errors.service_date && (
              <p className="mt-1 text-sm text-red-600">{errors.service_date.message}</p>
            )}
          </div>

          {/* Provider */}
          <div>
            <label htmlFor="provider" className="block text-sm font-medium text-gray-700">
              Service Provider <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="provider"
              {...register('provider', {
                required: 'Provider is required',
                minLength: { value: 1, message: 'Provider name is required' },
              })}
              placeholder="e.g., Rolex Service Center"
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
            {errors.provider && (
              <p className="mt-1 text-sm text-red-600">{errors.provider.message}</p>
            )}
          </div>

          {/* Service Type */}
          <div>
            <label htmlFor="service_type" className="block text-sm font-medium text-gray-700">
              Service Type
            </label>
            <select
              id="service_type"
              {...register('service_type')}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
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
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">
              Description
            </label>
            <textarea
              id="description"
              {...register('description')}
              rows={3}
              placeholder="Additional details about the service..."
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
          </div>

          {/* Cost and Currency */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="cost" className="block text-sm font-medium text-gray-700">
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
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
              {errors.cost && (
                <p className="mt-1 text-sm text-red-600">{errors.cost.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="cost_currency" className="block text-sm font-medium text-gray-700">
                Currency
              </label>
              <select
                id="cost_currency"
                {...register('cost_currency')}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
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
              className="block text-sm font-medium text-gray-700"
            >
              Next Service Due
            </label>
            <input
              type="date"
              id="next_service_due"
              {...register('next_service_due')}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            />
            <p className="mt-1 text-sm text-gray-500">
              Optional: Set a reminder for the next service date
            </p>
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
              {isSubmitting ? 'Saving...' : isEditing ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

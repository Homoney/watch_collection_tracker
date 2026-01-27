import { useForm } from 'react-hook-form'
import { useState } from 'react'
import Input from '@/components/common/Input'
import Select from '@/components/common/Select'
import Button from '@/components/common/Button'
import { useBrands, useMovementTypes, useComplications } from '@/hooks/useReferenceData'
import { useCollections } from '@/hooks/useCollections'
import type { WatchCreate, WatchUpdate, Watch } from '@/types'

interface WatchFormProps {
  defaultValues?: Watch
  onSubmit: (data: any) => void
  onCancel: () => void
  isLoading?: boolean
}

const conditionOptions = [
  { value: '', label: 'Select condition...' },
  { value: 'mint', label: 'Mint' },
  { value: 'excellent', label: 'Excellent' },
  { value: 'good', label: 'Good' },
  { value: 'fair', label: 'Fair' },
  { value: 'poor', label: 'Poor' },
]

export default function WatchForm({
  defaultValues,
  onSubmit,
  onCancel,
  isLoading,
}: WatchFormProps) {
  const { data: brands } = useBrands()
  const { data: movementTypes } = useMovementTypes()
  const { data: complications } = useComplications()
  const { data: collections } = useCollections()

  const [selectedComplications, setSelectedComplications] = useState<string[]>(
    defaultValues?.complications || []
  )

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<WatchCreate | WatchUpdate>({
    defaultValues: defaultValues
      ? {
          ...defaultValues,
          purchase_date: defaultValues.purchase_date
            ? new Date(defaultValues.purchase_date).toISOString().split('T')[0]
            : undefined,
          last_value_update: defaultValues.last_value_update
            ? new Date(defaultValues.last_value_update).toISOString().split('T')[0]
            : undefined,
        }
      : {
          purchase_currency: 'USD',
          current_market_currency: 'USD',
        },
  })

  const handleFormSubmit = (data: WatchCreate | WatchUpdate) => {
    const formattedData = {
      ...data,
      complications: selectedComplications,
      purchase_date: data.purchase_date ? `${data.purchase_date}T00:00:00Z` : null,
      last_value_update: data.last_value_update ? `${data.last_value_update}T00:00:00Z` : null,
      purchase_price: data.purchase_price ? Number(data.purchase_price) : null,
      current_market_value: data.current_market_value
        ? Number(data.current_market_value)
        : null,
      case_diameter: data.case_diameter ? Number(data.case_diameter) : null,
      case_thickness: data.case_thickness ? Number(data.case_thickness) : null,
      lug_width: data.lug_width ? Number(data.lug_width) : null,
      water_resistance: data.water_resistance ? Number(data.water_resistance) : null,
      power_reserve: data.power_reserve ? Number(data.power_reserve) : null,
      collection_id: data.collection_id || null,
      movement_type_id: data.movement_type_id || null,
      condition: data.condition || null,
    }
    onSubmit(formattedData as WatchCreate | WatchUpdate)
  }

  const toggleComplication = (complicationName: string) => {
    setSelectedComplications((prev) =>
      prev.includes(complicationName)
        ? prev.filter((c) => c !== complicationName)
        : [...prev, complicationName]
    )
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>

        <Select
          label="Brand"
          required
          {...register('brand_id', { required: 'Brand is required' })}
          error={errors.brand_id?.message}
          options={[
            { value: '', label: 'Select brand...' },
            ...(brands?.map((b) => ({ value: b.id, label: b.name })) || []),
          ]}
        />

        <Input
          label="Model"
          required
          {...register('model', { required: 'Model is required' })}
          error={errors.model?.message}
          placeholder="e.g., Submariner, Speedmaster"
        />

        <Input
          label="Reference Number"
          {...register('reference_number')}
          placeholder="e.g., 126610LN"
        />

        <Input
          label="Serial Number"
          {...register('serial_number')}
          placeholder="e.g., S1234567"
        />

        <Select
          label="Collection"
          {...register('collection_id')}
          options={[
            { value: '', label: 'No collection' },
            ...(collections?.map((c) => ({ value: c.id, label: c.name })) || []),
          ]}
        />

        <Select
          label="Movement Type"
          {...register('movement_type_id')}
          options={[
            { value: '', label: 'Select movement type...' },
            ...(movementTypes?.map((mt) => ({ value: mt.id, label: mt.name })) || []),
          ]}
        />

        <Select
          label="Condition"
          {...register('condition')}
          options={conditionOptions}
        />
      </div>

      <div className="space-y-4 pt-4 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Purchase Information</h3>

        <Input label="Purchase Date" type="date" {...register('purchase_date')} />

        <Input label="Retailer" {...register('retailer')} placeholder="e.g., Authorized Dealer" />

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Purchase Price"
            type="number"
            step="0.01"
            {...register('purchase_price')}
            placeholder="0.00"
          />
          <Input label="Currency" {...register('purchase_currency')} placeholder="USD" />
        </div>
      </div>

      <div className="space-y-4 pt-4 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Specifications</h3>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Case Diameter (mm)"
            type="number"
            step="0.01"
            {...register('case_diameter')}
            placeholder="40.00"
          />
          <Input
            label="Case Thickness (mm)"
            type="number"
            step="0.01"
            {...register('case_thickness')}
            placeholder="12.00"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Lug Width (mm)"
            type="number"
            step="0.01"
            {...register('lug_width')}
            placeholder="20.00"
          />
          <Input
            label="Water Resistance (m)"
            type="number"
            {...register('water_resistance')}
            placeholder="300"
          />
        </div>

        <Input
          label="Power Reserve (hours)"
          type="number"
          {...register('power_reserve')}
          placeholder="70"
        />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Complications
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {complications?.map((comp) => (
              <label
                key={comp.id}
                className="flex items-center space-x-2 p-2 border border-gray-300 rounded-md hover:bg-gray-50 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedComplications.includes(comp.name)}
                  onChange={() => toggleComplication(comp.name)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">{comp.name}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="space-y-4 pt-4 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Market Value</h3>

        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Current Market Value"
            type="number"
            step="0.01"
            {...register('current_market_value')}
            placeholder="0.00"
          />
          <Input
            label="Currency"
            {...register('current_market_currency')}
            placeholder="USD"
          />
        </div>

        <Input label="Last Value Update" type="date" {...register('last_value_update')} />
      </div>

      <div className="space-y-4 pt-4 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Notes</h3>

        <textarea
          {...register('notes')}
          rows={4}
          className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          placeholder="Add any additional notes about this watch..."
        />
      </div>

      <div className="flex gap-3 pt-4">
        <Button type="submit" disabled={isLoading} className="flex-1">
          {isLoading ? 'Saving...' : defaultValues ? 'Update Watch' : 'Add Watch'}
        </Button>
        <Button type="button" variant="secondary" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
      </div>
    </form>
  )
}

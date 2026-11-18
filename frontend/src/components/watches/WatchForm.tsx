import { useForm } from 'react-hook-form'
import { useState } from 'react'
import Input from '@/components/common/Input'
import Select from '@/components/common/Select'
import Button from '@/components/common/Button'
import { useBrands, useMovementTypes, useComplications } from '@/hooks/useReferenceData'
import { useCollections } from '@/hooks/useCollections'
import ReferenceLookup, { SourceNote } from '@/components/watches/ReferenceLookup'
import type { WatchCreate, WatchUpdate, Watch, SpecLookupResult, SpecSource } from '@/types'

type FormField = keyof WatchCreate

export interface WatchFormExtras {
  /** Save this WatchBase watch's photo as a reference photo after saving */
  referencePhotoWatchbaseId?: number
}

interface WatchFormProps {
  defaultValues?: Watch
  onSubmit: (data: WatchCreate | WatchUpdate, extras?: WatchFormExtras) => void | Promise<void>
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

  // Fields the reference look-up filled, and where from
  const [filledFrom, setFilledFrom] = useState<Partial<Record<string, SpecSource>>>({})
  // WatchBase watch with a photo, from the last look-up; saved after the watch
  const [photoFrom, setPhotoFrom] = useState<number | null>(null)
  const [savePhoto, setSavePhoto] = useState(true)

  const {
    register,
    handleSubmit,
    getValues,
    setValue,
    formState: { errors },
  } = useForm<WatchCreate | WatchUpdate>({
    defaultValues: defaultValues
      ? {
          brand_id: defaultValues.brand_id,
          model: defaultValues.model,
          reference_number: defaultValues.reference_number,
          serial_number: defaultValues.serial_number,
          collection_id: defaultValues.collection_id,
          movement_type_id: defaultValues.movement_type_id,
          retailer: defaultValues.retailer,
          purchase_price: defaultValues.purchase_price,
          purchase_currency: defaultValues.purchase_currency,
          case_diameter: defaultValues.case_diameter,
          case_thickness: defaultValues.case_thickness,
          case_material: defaultValues.case_material,
          caliber: defaultValues.caliber,
          crystal: defaultValues.crystal,
          dial_color: defaultValues.dial_color,
          strap_material: defaultValues.strap_material,
          lug_width: defaultValues.lug_width,
          water_resistance: defaultValues.water_resistance,
          power_reserve: defaultValues.power_reserve,
          condition: defaultValues.condition,
          current_market_value: defaultValues.current_market_value,
          current_market_currency: defaultValues.current_market_currency || defaultValues.purchase_currency,
          notes: defaultValues.notes,
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
      caliber: data.caliber || null,
      crystal: data.crystal || null,
      case_material: data.case_material || null,
      collection_id: data.collection_id || null,
      movement_type_id: data.movement_type_id || null,
      condition: data.condition || null,
    }
    onSubmit(formattedData as WatchCreate | WatchUpdate, {
      referencePhotoWatchbaseId: photoFrom && savePhoto ? photoFrom : undefined,
    })
  }

  // Put a look-up answer into the empty fields only; never overwrite
  const applyLookup = (result: SpecLookupResult) => {
    const f = result.fields
    const filled: Partial<Record<string, SpecSource>> = {}
    const isEmpty = (v: unknown) => v === undefined || v === null || v === ''
    const fill = (name: FormField, value: unknown, from: keyof typeof f) => {
      if (value === undefined || value === null || !isEmpty(getValues(name))) return
      setValue(name, value as never, { shouldDirty: true })
      filled[name] = result.sources[from]
    }
    const byName = <T extends { id: string; name: string }>(list: T[] | undefined, name?: string) =>
      name ? list?.find((x) => x.name.toLowerCase() === name.toLowerCase())?.id : undefined

    fill('brand_id', byName(brands, f.brand_name), 'brand_name')
    fill('model', f.model, 'model')
    fill('movement_type_id', byName(movementTypes, f.movement_type_name), 'movement_type_name')
    fill('case_diameter', f.case_diameter, 'case_diameter')
    fill('case_thickness', f.case_thickness, 'case_thickness')
    fill('lug_width', f.lug_width, 'lug_width')
    fill('water_resistance', f.water_resistance, 'water_resistance')
    fill('power_reserve', f.power_reserve, 'power_reserve')
    fill('caliber', f.caliber, 'caliber')
    fill('crystal', f.crystal, 'crystal')
    fill('case_material', f.case_material, 'case_material')

    const known = new Set(complications?.map((c) => c.name))
    const found = (f.complications || []).filter((name) => known.has(name))
    if (selectedComplications.length === 0 && found.length > 0) {
      setSelectedComplications(found)
      filled.complications = result.sources.complications
    }
    setFilledFrom((prev) => ({ ...prev, ...filled }))
    if (result.status === 'ok') {
      setPhotoFrom(result.has_photo && result.watchbase_id ? result.watchbase_id : null)
    }
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

        <div>
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
          <SourceNote source={filledFrom.brand_id} />
        </div>

        <div>
          <Input
            label="Model"
            required
            {...register('model', { required: 'Model is required' })}
            error={errors.model?.message}
            placeholder="e.g., Submariner, Speedmaster"
          />
          <SourceNote source={filledFrom.model} />
        </div>

        <div className="space-y-2">
          <Input
            label="Reference Number"
            {...register('reference_number')}
            placeholder="e.g., 126610LN"
          />
          <ReferenceLookup
            getContext={() => ({
              reference: (getValues('reference_number') as string) || '',
              brand_id: getValues('brand_id') as string,
              caliber: getValues('caliber') as string,
            })}
            onResult={applyLookup}
          />
          {photoFrom && (
            <label className="flex items-start gap-2 text-sm text-gray-800 dark:text-gray-100">
              <input
                type="checkbox"
                checked={savePhoto}
                onChange={(e) => setSavePhoto(e.target.checked)}
                className="mt-0.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span>
                Also save WatchBase's photo of this watch as a reference photo (kept private,
                labelled with its source; your own photos stay first)
              </span>
            </label>
          )}
        </div>

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

        <div>
          <Select
            label="Movement Type"
            {...register('movement_type_id')}
            options={[
              { value: '', label: 'Select movement type...' },
              ...(movementTypes?.map((mt) => ({ value: mt.id, label: mt.name })) || []),
            ]}
          />
          <SourceNote source={filledFrom.movement_type_id} />
        </div>

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
          <div>
            <Input
              label="Case Diameter (mm)"
              type="number"
              step="0.01"
              {...register('case_diameter')}
              placeholder="40.00"
            />
            <SourceNote source={filledFrom.case_diameter} />
          </div>
          <div>
            <Input
              label="Case Thickness (mm)"
              type="number"
              step="0.01"
              {...register('case_thickness')}
              placeholder="12.00"
            />
            <SourceNote source={filledFrom.case_thickness} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Input
              label="Lug Width (mm)"
              type="number"
              step="0.01"
              {...register('lug_width')}
              placeholder="20.00"
            />
            <SourceNote source={filledFrom.lug_width} />
          </div>
          <div>
            <Input
              label="Water Resistance (m)"
              type="number"
              {...register('water_resistance')}
              placeholder="300"
            />
            <SourceNote source={filledFrom.water_resistance} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Input
              label="Power Reserve (hours)"
              type="number"
              {...register('power_reserve')}
              placeholder="70"
            />
            <SourceNote source={filledFrom.power_reserve} />
          </div>
          <div>
            <Input label="Caliber" {...register('caliber')} placeholder="e.g., 3235" />
            <SourceNote source={filledFrom.caliber} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Input label="Crystal" {...register('crystal')} placeholder="e.g., Sapphire" />
            <SourceNote source={filledFrom.crystal} />
          </div>
          <div>
            <Input
              label="Case Material"
              {...register('case_material')}
              placeholder="e.g., Stainless steel"
            />
            <SourceNote source={filledFrom.case_material} />
          </div>
        </div>

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
          <SourceNote source={filledFrom.complications} />
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

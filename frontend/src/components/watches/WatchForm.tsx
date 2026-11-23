import { useForm } from 'react-hook-form'
import { useEffect, useRef, useState } from 'react'
import Input from '@/components/common/Input'
import Select from '@/components/common/Select'
import Button from '@/components/common/Button'
import { useBrands, useMovementTypes, useComplications } from '@/hooks/useReferenceData'
import { useCollections } from '@/hooks/useCollections'
import ReferenceLookup, { SourceNote } from '@/components/watches/ReferenceLookup'
import { useModalForm } from '@/components/common/modalForm'
import { clearDraft, loadDraft, saveDraft } from '@/lib/watchDraft'
import type { WatchCreate, WatchUpdate, Watch, SpecLookupResult, SpecSource } from '@/types'

type FormField = keyof WatchCreate

export interface WatchFormExtras {
  /**
   * Save WatchBase's photo as a reference photo after saving: the matched
   * watch's (watchbaseId), or without a key the one found by reference number.
   */
  referencePhoto?: { watchbaseId?: number }
}

interface WatchFormProps {
  defaultValues?: Watch
  onSubmit: (data: WatchCreate | WatchUpdate, extras?: WatchFormExtras) => void | Promise<void>
  onCancel: () => void
  isLoading?: boolean
  /** Keep what is typed in the browser under this key (Add form only) */
  draftKey?: string
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
  draftKey,
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
  // Photo to save after the watch, from the last look-up: a matched watch with
  // a photo (WatchBase or the brand's site), or (no key) a try by reference number
  const [photoFrom, setPhotoFrom] = useState<{ watchbaseId?: number; sourceName?: string } | null>(
    null
  )
  const [savePhoto, setSavePhoto] = useState(true)

  const {
    register,
    handleSubmit,
    getValues,
    setValue,
    reset,
    watch,
    formState: { errors, isDirty },
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

  // Typed changes: the pop-up asks before discarding them
  const defaultComplications = useRef(defaultValues?.complications || [])
  const complicationsChanged =
    [...selectedComplications].sort().join('|') !== [...defaultComplications.current].sort().join('|')
  const dirty = isDirty || complicationsChanged
  const cancel = useModalForm(dirty, onCancel)

  // Draft: restore once, then keep it up to date while something is typed
  const [restored, setRestored] = useState(false)
  const draftLoaded = useRef(false)
  useEffect(() => {
    if (!draftKey || draftLoaded.current) return
    draftLoaded.current = true
    const draft = loadDraft(draftKey)
    if (!draft) return
    reset(draft.values, { keepDefaultValues: true })
    setSelectedComplications(draft.complications)
    setRestored(true)
  }, [draftKey, reset])

  // A <select> can only show a value once that option exists. On a direct
  // load the brand, movement and collection lists arrive after the form has
  // mounted, so the stored ids are written back into the selects when they do.
  // Keyed on the list sizes, so it runs when a list arrives, not on every render.
  const optionCounts = [brands?.length ?? 0, movementTypes?.length ?? 0, collections?.length ?? 0]
  useEffect(() => {
    const names = ['brand_id', 'movement_type_id', 'collection_id'] as const
    names.forEach((name, i) => {
      const current = getValues(name)
      if (optionCounts[i] && current) setValue(name, current)
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...optionCounts, getValues, setValue])
  // Written only when what was typed changes, not on every render: after a
  // save the parent clears the draft while this form is still on screen, and
  // a re-render then (e.g. the save finishing) must not write it back.
  const snapshot = JSON.stringify({ values: watch(), complications: selectedComplications })
  useEffect(() => {
    if (!draftKey || !draftLoaded.current) return
    if (dirty) saveDraft(draftKey, JSON.parse(snapshot))
    else clearDraft(draftKey)
  }, [draftKey, dirty, snapshot])

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
      referencePhoto:
        photoFrom && savePhoto ? { watchbaseId: photoFrom.watchbaseId } : undefined,
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
      setPhotoFrom(
        result.has_photo
          ? {
              watchbaseId: result.watchbase_id ?? undefined,
              sourceName: result.photo_source?.name ?? 'WatchBase',
            }
          : null
      )
    } else if (result.status === 'links_only' && result.reference) {
      setPhotoFrom({})
    }
  }

  const toggleComplication = (complicationName: string) => {
    setSelectedComplications((prev) =>
      prev.includes(complicationName)
        ? prev.filter((c) => c !== complicationName)
        : [...prev, complicationName]
    )
  }

  const legend = 'mb-4 text-[11px] uppercase tracking-[0.24em] text-gold'

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {restored && (
        <p
          role="status"
          className="rounded-sm border border-border bg-muted px-3 py-2 text-sm text-foreground"
        >
          Restored what you typed last time. Save it, or Cancel to discard it.
        </p>
      )}
      {/* Sections of two to four columns instead of one long column */}
      <fieldset className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <legend className={legend}>The watch</legend>

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

        <div className="grid grid-cols-[1fr_auto] gap-2 sm:col-span-2">
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
            <label className="col-span-full flex items-start gap-2 text-sm text-foreground">
              <input
                type="checkbox"
                checked={savePhoto}
                onChange={(e) => setSavePhoto(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded-sm accent-[hsl(var(--gold))]"
              />
              <span>
                {photoFrom.sourceName
                  ? `Also save ${photoFrom.sourceName}'s photo of this watch`
                  : "Also look for this reference's photo on WatchBase"}{' '}
                as a reference photo (kept private, labelled with its source; your own photos
                stay first)
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
      </fieldset>

      <fieldset className="grid grid-cols-2 gap-4 border-t border-border pt-2 sm:grid-cols-4">
        <legend className={legend}>Purchase and value</legend>

        <div className="col-span-2">
          <Input label="Purchase Date" type="date" {...register('purchase_date')} />
        </div>
        <div className="col-span-2">
          <Input label="Retailer" {...register('retailer')} placeholder="e.g., Authorized Dealer" />
        </div>
        <Input
          label="Purchase Price"
          type="number"
          step="0.01"
          {...register('purchase_price')}
          placeholder="0.00"
        />
        <Input label="Currency" {...register('purchase_currency')} placeholder="USD" />
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
        <div className="col-span-2">
          <Input label="Last Value Update" type="date" {...register('last_value_update')} />
        </div>
      </fieldset>

      <fieldset className="grid grid-cols-2 gap-4 border-t border-border pt-2 sm:grid-cols-4">
        <legend className={legend}>Specifications</legend>

        <div className="contents">
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

        <div className="contents">
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

        <div className="contents">
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

        <div className="contents">
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

        <div className="col-span-full">
          <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
            Complications
          </p>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {complications?.map((comp) => (
              <label
                key={comp.id}
                className="flex cursor-pointer items-center gap-2 rounded-sm border border-border p-2 hover:bg-accent has-[:checked]:border-gold"
              >
                <input
                  type="checkbox"
                  checked={selectedComplications.includes(comp.name)}
                  onChange={() => toggleComplication(comp.name)}
                  className="h-4 w-4 rounded-sm accent-[hsl(var(--gold))]"
                />
                <span className="text-sm text-foreground">{comp.name}</span>
              </label>
            ))}
          </div>
          <SourceNote source={filledFrom.complications} />
        </div>
      </fieldset>

      <fieldset className="border-t border-border pt-2">
        <legend className={legend}>Notes</legend>

        <textarea
          {...register('notes')}
          rows={3}
          aria-label="Notes"
          className="block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
          placeholder="Add any additional notes about this watch..."
        />
      </fieldset>

      {/* Save and Cancel stay in view at the bottom of the pop-up */}
      <div className="sticky bottom-0 -mx-4 -mb-4 flex gap-3 border-t border-border bg-card px-4 py-4 sm:-mx-6 sm:-mb-6 sm:px-6">
        <Button type="submit" disabled={isLoading} className="flex-1">
          {isLoading ? 'Saving...' : defaultValues ? 'Update Watch' : 'Add Watch'}
        </Button>
        <Button type="button" variant="secondary" onClick={cancel} disabled={isLoading}>
          Cancel
        </Button>
      </div>
    </form>
  )
}

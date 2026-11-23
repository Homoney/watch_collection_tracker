import { useState, type ReactNode } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Clock, Download, FileDown, MoreHorizontal, Pencil, Plus, Trash2 } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import AppLayout from '@/components/layout/AppLayout'
import WatchForm, { type WatchFormExtras } from '@/components/watches/WatchForm'
import ImageUpload from '@/components/watches/ImageUpload'
import ImageGallery from '@/components/watches/ImageGallery'
import ImageLightbox from '@/components/common/ImageLightbox'
import ServiceHistoryList from '@/components/watches/ServiceHistoryList'
import ServiceHistoryForm from '@/components/watches/ServiceHistoryForm'
import MarketValueHistory from '@/components/watches/MarketValueHistory'
import MarketValueForm from '@/components/watches/MarketValueForm'
import WatchAnalytics from '@/components/watches/WatchAnalytics'
import ValueChart from '@/components/watches/ValueChart'
import WatchQRCode from '@/components/watches/WatchQRCode'
import Modal from '@/components/common/Modal'
import Button from '@/components/common/Button'
import Badge from '@/components/common/Badge'
import Spinner from '@/components/common/Spinner'
import Card from '@/components/common/Card'
import { useWatch, useUpdateWatch, useDeleteWatch } from '@/hooks/useWatches'
import WatchDial from '@/components/watches/WatchDial'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { formatMoney, formatPercent, gainPercent } from '@/lib/money'
import { api, referencePhotoApi } from '@/lib/api'
import type { WatchUpdate, ServiceHistory, MarketValue } from '@/types'

export default function WatchDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null)
  const [isServiceFormOpen, setIsServiceFormOpen] = useState(false)
  const [editingService, setEditingService] = useState<ServiceHistory | undefined>(undefined)
  const [isMarketValueFormOpen, setIsMarketValueFormOpen] = useState(false)
  const [editingMarketValue, setEditingMarketValue] = useState<MarketValue | undefined>(undefined)

  const { data: watch, isLoading, error } = useWatch(id)
  const updateMutation = useUpdateWatch()
  const deleteMutation = useDeleteWatch()
  const queryClient = useQueryClient()
  const [isFetchingImages, setIsFetchingImages] = useState(false)
  const [imageFetchMessage, setImageFetchMessage] = useState<string | null>(null)

  const handleUpdate = async (data: WatchUpdate, extras?: WatchFormExtras) => {
    if (!id) return
    try {
      await updateMutation.mutateAsync({ id, data })
      setIsEditModalOpen(false)
      if (extras?.referencePhoto) {
        await handleReferencePhoto(extras.referencePhoto.watchbaseId)
      }
    } catch (error) {
      console.error('Failed to update watch:', error)
    }
  }

  const handleDelete = async () => {
    if (!id) return
    try {
      await deleteMutation.mutateAsync(id)
      navigate('/watches')
    } catch (error) {
      console.error('Failed to delete watch:', error)
    }
  }

  const handleExportPDF = async () => {
    if (!id) return
    try {
      const response = await api.get(`/v1/watches/${id}/export/pdf`, {
        responseType: 'blob'
      })

      // Create blob URL and trigger download
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url

      // Generate filename
      const brandName = watch?.brand?.name || 'Watch'
      const model = watch?.model.replace('/', '-').replace(' ', '_') || 'Export'
      link.download = `${brandName}_${model}.pdf`.replace(' ', '_')

      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to export PDF:', error)
    }
  }

  const formatCurrency = (amount: number | null, currency: string) => {
    if (amount === null) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount)
  }

  const formatDate = (date: string | null) => {
    if (!date) return 'N/A'
    return new Date(date).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

  const handleAddService = () => {
    setEditingService(undefined)
    setIsServiceFormOpen(true)
  }

  const handleEditService = (service: ServiceHistory) => {
    setEditingService(service)
    setIsServiceFormOpen(true)
  }

  const handleServiceFormSuccess = () => {
    setIsServiceFormOpen(false)
    setEditingService(undefined)
  }

  const handleServiceFormCancel = () => {
    setIsServiceFormOpen(false)
    setEditingService(undefined)
  }

  const handleAddMarketValue = () => {
    setEditingMarketValue(undefined)
    setIsMarketValueFormOpen(true)
  }

  const handleEditMarketValue = (value: MarketValue) => {
    setEditingMarketValue(value)
    setIsMarketValueFormOpen(true)
  }

  const handleMarketValueFormSuccess = () => {
    setIsMarketValueFormOpen(false)
    setEditingMarketValue(undefined)
  }

  const handleMarketValueFormCancel = () => {
    setIsMarketValueFormOpen(false)
    setEditingMarketValue(undefined)
  }

  // The source's photo of this watch (WatchBase, or the brand's site for
  // references WatchBase lacks), saved as a labelled reference photo
  const handleReferencePhoto = async (watchbaseId?: number) => {
    if (!id) return
    setIsFetchingImages(true)
    setImageFetchMessage(null)
    try {
      const result = await referencePhotoApi.save(id, watchbaseId)
      if (result.image) {
        queryClient.invalidateQueries({ queryKey: ['watches', id] })
        queryClient.invalidateQueries({ queryKey: ['watches'] })
      }
      setImageFetchMessage(result.message)
    } catch (error: unknown) {
      const err = error as { response?: { status?: number } }
      setImageFetchMessage(
        err.response?.status === 429
          ? 'Too many requests in a row. Wait a minute and try again.'
          : 'Could not get the reference photo. Try again later, or upload your own.'
      )
    } finally {
      setIsFetchingImages(false)
    }
  }

  if (isLoading) {
    return (
      <AppLayout>
        <div className="flex justify-center py-12">
          <Spinner size="lg" />
        </div>
      </AppLayout>
    )
  }

  if (error || !watch) {
    return (
      <AppLayout>
        <div className="text-center py-12">
          <h2 className="text-2xl font-light text-foreground mb-2">Watch Not Found</h2>
          <p className="text-muted-foreground mb-4">The watch you're looking for doesn't exist.</p>
          <Button onClick={() => navigate('/watches')}>Back to Watches</Button>
        </div>
      </AppLayout>
    )
  }

  const primaryIndex = watch.images?.findIndex((img) => img.is_primary) ?? -1
  const heroImage = watch.images?.[primaryIndex >= 0 ? primaryIndex : 0]
  const hasValue = watch.current_market_value !== null && watch.current_market_value !== undefined
  const valueCurrency = watch.current_market_currency || watch.purchase_currency
  const gain = hasValue
    ? gainPercent(watch.current_market_value, watch.purchase_price, valueCurrency, watch.purchase_currency)
    : null
  const gainAmount = gain !== null ? Number(watch.current_market_value) - Number(watch.purchase_price) : null
  const hasReferencePhoto = watch.images?.some((img) => img.source === 'reference_photo')

  const caseFacts = [
    watch.case_diameter && `${watch.case_diameter} mm`,
    watch.case_thickness && `${watch.case_thickness} mm thick`,
    watch.case_material,
  ].filter(Boolean)
  const movementFacts = [watch.movement_type?.name, watch.caliber && `cal. ${watch.caliber}`].filter(Boolean)
  const purchaseFacts = [watch.purchase_date && formatDate(watch.purchase_date), watch.retailer].filter(Boolean)

  // Key facts beside the photo; everything else sits in the tabs below
  const keyFacts: Array<[string, ReactNode]> = [
    ['Reference', watch.reference_number],
    ['Movement', movementFacts.join(' · ')],
    ['Case', caseFacts.join(' · ')],
    ['Water resistance', watch.water_resistance ? `${watch.water_resistance} m` : null],
    ['Purchased', purchaseFacts.join(' · ')],
    ['Condition', watch.condition ? <Badge condition={watch.condition} /> : null],
  ]
  const shownFacts = keyFacts.filter(([, v]) => v !== null && v !== undefined && v !== '')

  const specs: Array<[string, ReactNode]> = [
    ['Brand', watch.brand?.name],
    ['Model', watch.model],
    ['Reference number', watch.reference_number],
    ['Serial number', watch.serial_number],
    ['Movement type', watch.movement_type?.name],
    ['Caliber', watch.caliber],
    ['Case diameter', watch.case_diameter ? `${watch.case_diameter} mm` : null],
    ['Case thickness', watch.case_thickness ? `${watch.case_thickness} mm` : null],
    ['Lug width', watch.lug_width ? `${watch.lug_width} mm` : null],
    ['Case material', watch.case_material],
    ['Crystal', watch.crystal],
    ['Water resistance', watch.water_resistance ? `${watch.water_resistance} m` : null],
    ['Power reserve', watch.power_reserve ? `${watch.power_reserve} hours` : null],
    ['Purchase date', watch.purchase_date ? formatDate(watch.purchase_date) : null],
    ['Purchase price', watch.purchase_price !== null ? formatCurrency(watch.purchase_price, watch.purchase_currency) : null],
    ['Retailer', watch.retailer],
    ['Collection', watch.collection?.name],
    ['Value last updated', watch.last_value_update ? formatDate(watch.last_value_update) : null],
  ]
  const shownSpecs = specs.filter(([, v]) => v !== null && v !== undefined && v !== '')

  const eyebrow = 'text-[10px] uppercase tracking-[0.22em] text-muted-foreground'

  return (
    <AppLayout>
      <div className="space-y-8">
        <button
          type="button"
          onClick={() => navigate('/watches')}
          className="inline-flex items-center gap-1 text-[11px] uppercase tracking-[0.2em] text-muted-foreground hover:text-gold"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Collection
        </button>

        {/* Photo and key facts first */}
        <section className="grid grid-cols-1 gap-px border border-border bg-border lg:grid-cols-2">
          <div className="flex min-h-[18rem] items-center justify-center bg-card bg-[radial-gradient(circle_at_50%_40%,hsl(var(--muted)),hsl(var(--card))_70%)] p-6">
            {heroImage ? (
              <button
                type="button"
                onClick={() => setLightboxIndex(primaryIndex >= 0 ? primaryIndex : 0)}
                className="block w-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                aria-label="Open photos"
              >
                <img
                  src={heroImage.url}
                  alt={`${watch.brand?.name} ${watch.model}`}
                  className="mx-auto max-h-[28rem] w-full object-contain"
                />
              </button>
            ) : (
              <WatchDial accent={watch.collection?.color} className="h-56 w-56 sm:h-72 sm:w-72" />
            )}
          </div>

          <div className="bg-card p-6 sm:p-10">
            <p className="text-[11px] uppercase tracking-[0.3em] text-gold">{watch.brand?.name}</p>
            <h1 className="mt-2 break-words text-3xl font-light tracking-wide text-foreground sm:text-4xl">
              {watch.model}
            </h1>
            {watch.collection && (
              <p className="mt-2 text-xs uppercase tracking-[0.16em] text-muted-foreground">{watch.collection.name}</p>
            )}

            <p className="mt-6 text-4xl font-light text-foreground sm:text-5xl">
              {hasValue
                ? formatMoney(watch.current_market_value, valueCurrency)
                : formatMoney(watch.purchase_price, watch.purchase_currency)}
            </p>
            {hasValue && gain !== null && gainAmount !== null ? (
              <p className={`mt-1 text-sm ${gain >= 0 ? 'text-positive' : 'text-negative'}`}>
                {gain >= 0 ? '▲' : '▼'} {formatMoney(Math.abs(gainAmount), valueCurrency)} · {formatPercent(gain)} on{' '}
                {formatMoney(watch.purchase_price, watch.purchase_currency)}
              </p>
            ) : (
              <p className="mt-1 text-sm text-muted-foreground">
                {hasValue ? 'Current market value' : 'Price paid · no valuation yet'}
              </p>
            )}

            {shownFacts.length > 0 && (
              <dl className="mt-8 grid grid-cols-2 gap-x-6 gap-y-5">
                {shownFacts.map(([label, value]) => (
                  <div key={label} className="min-w-0">
                    <dt className={eyebrow}>{label}</dt>
                    <dd className="mt-1 break-words text-sm text-foreground">{value}</dd>
                  </div>
                ))}
              </dl>
            )}

            <div className="mt-8 flex flex-wrap gap-2">
              <Button onClick={() => setIsEditModalOpen(true)}>
                <Pencil className="h-4 w-4" />
                Edit
              </Button>
              <Button variant="outline" onClick={handleAddMarketValue}>
                <Plus className="h-4 w-4" />
                Add valuation
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="secondary" size="icon" aria-label="More actions">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onSelect={() => navigate(`/watches/${id}/accuracy`)}>
                    <Clock className="mr-2 h-4 w-4" /> Movement accuracy
                  </DropdownMenuItem>
                  <DropdownMenuItem onSelect={handleExportPDF}>
                    <FileDown className="mr-2 h-4 w-4" /> Export PDF
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onSelect={() => setIsDeleteModalOpen(true)}
                    className="text-destructive focus:text-destructive"
                  >
                    <Trash2 className="mr-2 h-4 w-4" /> Delete watch
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </section>

        {/* Everything else, one tab at a time */}
        <Tabs defaultValue="value">
          <TabsList aria-label="Watch details">
            <TabsTrigger value="value">Value</TabsTrigger>
            <TabsTrigger value="details">Details</TabsTrigger>
            <TabsTrigger value="service">Service</TabsTrigger>
            <TabsTrigger value="photos">
              Photos{watch.images && watch.images.length > 0 ? ` (${watch.images.length})` : ''}
            </TabsTrigger>
            <TabsTrigger value="qr">QR code</TabsTrigger>
          </TabsList>

          <TabsContent value="value" className="space-y-6">
            <Card className="p-6">
              <ValueChart watchId={watch.id} />
            </Card>
            <Card className="p-6">
              <WatchAnalytics watchId={watch.id} />
            </Card>
            <Card className="p-6">
              <MarketValueHistory
                watchId={watch.id}
                onAddValue={handleAddMarketValue}
                onEditValue={handleEditMarketValue}
              />
            </Card>
          </TabsContent>

          <TabsContent value="details" className="space-y-6">
            <Card className="p-6">
              <dl className="grid grid-cols-1 gap-x-8 gap-y-5 sm:grid-cols-2 lg:grid-cols-3">
                {shownSpecs.map(([label, value]) => (
                  <div key={label} className="min-w-0">
                    <dt className={eyebrow}>{label}</dt>
                    <dd className="mt-1 break-words text-sm text-foreground">{value}</dd>
                  </div>
                ))}
              </dl>
              {watch.complications && watch.complications.length > 0 && (
                <div className="mt-8 border-t border-border pt-6">
                  <h2 className={eyebrow}>Complications</h2>
                  <ul className="mt-3 flex flex-wrap gap-2">
                    {watch.complications.map((comp) => (
                      <li key={comp} className="border border-border px-3 py-1 text-sm text-foreground">
                        {comp}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {watch.notes && (
                <div className="mt-8 border-t border-border pt-6">
                  <h2 className={eyebrow}>Notes</h2>
                  <p className="mt-3 whitespace-pre-wrap text-sm text-foreground">{watch.notes}</p>
                </div>
              )}
            </Card>
          </TabsContent>

          <TabsContent value="service">
            <Card className="p-6">
              <ServiceHistoryList
                watchId={watch.id}
                onAddService={handleAddService}
                onEditService={handleEditService}
              />
            </Card>
          </TabsContent>

          <TabsContent value="photos">
            <Card className="space-y-6 p-6">
              {!watch.images || watch.images.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No images yet. Upload your own, or get the reference photo (from WatchBase or the brand's site).
                </p>
              ) : (
                <ImageGallery
                  watchId={watch.id}
                  images={watch.images || []}
                  onImageClick={(index) => setLightboxIndex(index)}
                />
              )}
              {!hasReferencePhoto && (
                <Button onClick={() => handleReferencePhoto()} disabled={isFetchingImages} variant="secondary">
                  <Download className="h-4 w-4" />
                  {isFetchingImages ? 'Getting photo...' : 'Get reference photo'}
                </Button>
              )}
              {imageFetchMessage && (
                <p role="status" className="text-sm text-muted-foreground">
                  {imageFetchMessage}
                </p>
              )}
              <div className="border-t border-border pt-6">
                <h3 className={`${eyebrow} mb-3`}>Upload new images</h3>
                <ImageUpload watchId={watch.id} />
              </div>
            </Card>
          </TabsContent>

          <TabsContent value="qr">
            <WatchQRCode watchId={watch.id} />
          </TabsContent>
        </Tabs>
      </div>

      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Watch"
        size="xl"
        form
      >
        <WatchForm
          defaultValues={watch}
          onSubmit={handleUpdate}
          onCancel={() => setIsEditModalOpen(false)}
          isLoading={updateMutation.isPending}
        />
      </Modal>

      <Modal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        title="Delete Watch"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-muted-foreground">
            Are you sure you want to delete{' '}
            <span className="font-semibold">
              {watch.brand?.name} {watch.model}
            </span>
            ? This action cannot be undone.
          </p>
          <div className="flex gap-3">
            <Button
              variant="danger"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              className="flex-1"
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </Button>
            <Button
              variant="secondary"
              onClick={() => setIsDeleteModalOpen(false)}
              disabled={deleteMutation.isPending}
            >
              Cancel
            </Button>
          </div>
        </div>
      </Modal>

      {lightboxIndex !== null && watch.images && watch.images.length > 0 && (
        <ImageLightbox
          images={watch.images}
          currentIndex={lightboxIndex}
          onClose={() => setLightboxIndex(null)}
          onNavigate={setLightboxIndex}
        />
      )}

      {isServiceFormOpen && (
        <ServiceHistoryForm
          watchId={watch.id}
          service={editingService}
          onSuccess={handleServiceFormSuccess}
          onCancel={handleServiceFormCancel}
        />
      )}

      {isMarketValueFormOpen && (
        <MarketValueForm
          watchId={watch.id}
          marketValue={editingMarketValue}
          onSuccess={handleMarketValueFormSuccess}
          onCancel={handleMarketValueFormCancel}
        />
      )}
    </AppLayout>
  )
}

import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { FileDown, Download, Clock } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'
import AppLayout from '@/components/layout/AppLayout'
import WatchForm from '@/components/watches/WatchForm'
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
import { api } from '@/lib/api'
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
  const [imageOffset, setImageOffset] = useState(0)

  const handleUpdate = async (data: WatchUpdate) => {
    if (!id) return
    try {
      await updateMutation.mutateAsync({ id, data })
      setIsEditModalOpen(false)
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

  const handleFetchGoogleImages = async () => {
    if (!id) return
    setIsFetchingImages(true)
    try {
      await api.post(`/v1/watches/${id}/fetch-images?offset=${imageOffset}`)
      // Invalidate queries to refetch watch data with new images
      queryClient.invalidateQueries({ queryKey: ['watches', id] })
      queryClient.invalidateQueries({ queryKey: ['watches'] })
      // Increment offset for next fetch
      setImageOffset((prev) => prev + 3)
    } catch (error: any) {
      console.error('Failed to fetch images:', error)
      alert(error.response?.data?.detail || 'Failed to fetch images from Google')
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
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Watch Not Found</h2>
          <p className="text-gray-600 mb-4">The watch you're looking for doesn't exist.</p>
          <Button onClick={() => navigate('/watches')}>Back to Watches</Button>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-start">
          <div>
            <button
              onClick={() => navigate('/watches')}
              className="text-blue-600 hover:text-blue-800 mb-2 flex items-center text-sm"
            >
              <svg
                className="w-4 h-4 mr-1"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
              Back to Watches
            </button>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              {watch.brand?.name} {watch.model}
            </h1>
            {watch.reference_number && (
              <p className="text-gray-600 dark:text-gray-400 mt-1">Reference: {watch.reference_number}</p>
            )}
          </div>
          <div className="flex gap-3">
            <Button onClick={() => navigate(`/watches/${id}/accuracy`)} variant="secondary">
              <Clock className="h-4 w-4 mr-2" />
              Movement Accuracy
            </Button>
            <Button onClick={handleExportPDF} variant="secondary">
              <FileDown className="h-4 w-4 mr-2" />
              Export PDF
            </Button>
            <Button onClick={() => setIsEditModalOpen(true)}>Edit</Button>
            <Button variant="danger" onClick={() => setIsDeleteModalOpen(true)}>
              Delete
            </Button>
          </div>
        </div>

        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Images {watch.images && watch.images.length > 0 && `(${watch.images.length})`}
          </h2>

          <div className="space-y-6">
            {!watch.images || watch.images.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  No images yet. Upload your own or fetch from Google Images.
                </p>
                <div className="flex gap-3 justify-center">
                  <Button
                    onClick={handleFetchGoogleImages}
                    disabled={isFetchingImages}
                    variant="secondary"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    {isFetchingImages ? 'Fetching Images...' : 'Fetch from Google Images'}
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <ImageGallery
                  watchId={watch.id}
                  images={watch.images || []}
                  onImageClick={(index) => setLightboxIndex(index)}
                />
                <div className="flex justify-center pt-4">
                  <Button
                    onClick={handleFetchGoogleImages}
                    disabled={isFetchingImages}
                    variant="secondary"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    {isFetchingImages ? 'Loading More Images...' : 'Load More Images from Google'}
                  </Button>
                </div>
              </>
            )}

            <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Upload New Images</h3>
              <ImageUpload watchId={watch.id} />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <ServiceHistoryList
            watchId={watch.id}
            onAddService={handleAddService}
            onEditService={handleEditService}
          />
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

        <ValueChart watchId={watch.id} />

        <WatchQRCode watchId={watch.id} />

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <Card className="p-6">
              <div className="aspect-square bg-gray-100 rounded-lg flex items-center justify-center mb-4 overflow-hidden">
                {watch.images?.[0] ? (
                  <img
                    src={watch.images.find(img => img.is_primary)?.url || watch.images[0].url}
                    alt={`${watch.brand?.name} ${watch.model}`}
                    className="w-full h-full object-cover cursor-pointer hover:opacity-90 transition-opacity"
                    onClick={() => {
                      const primaryIndex = watch.images?.findIndex(img => img.is_primary) ?? -1
                      setLightboxIndex(primaryIndex >= 0 ? primaryIndex : 0)
                    }}
                  />
                ) : (
                  <svg
                    className="w-24 h-24 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                )}
              </div>
              {watch.condition && (
                <div className="mb-4">
                  <Badge condition={watch.condition} />
                </div>
              )}
              {watch.collection && (
                <div>
                  <span
                    className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium"
                    style={{
                      backgroundColor: `${watch.collection.color}20`,
                      color: watch.collection.color,
                      borderColor: watch.collection.color,
                      borderWidth: '1px',
                    }}
                  >
                    {watch.collection.name}
                  </span>
                </div>
              )}
            </Card>
          </div>

          <div className="lg:col-span-2 space-y-6">
            <Card className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Basic Information</h2>
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Brand</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-gray-300">{watch.brand?.name || 'N/A'}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Model</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-gray-300">{watch.model}</dd>
                </div>
                {watch.reference_number && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Reference Number</dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-gray-300">{watch.reference_number}</dd>
                  </div>
                )}
                {watch.serial_number && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Serial Number</dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-gray-300">{watch.serial_number}</dd>
                  </div>
                )}
                {watch.movement_type && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Movement Type</dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-gray-300">{watch.movement_type.name}</dd>
                  </div>
                )}
              </dl>
            </Card>

            <Card className="p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Purchase Information</h2>
              <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Purchase Date</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-gray-300">
                    {formatDate(watch.purchase_date)}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Purchase Price</dt>
                  <dd className="mt-1 text-sm text-gray-900 dark:text-gray-300">
                    {formatCurrency(watch.purchase_price, watch.purchase_currency)}
                  </dd>
                </div>
                {watch.retailer && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Retailer</dt>
                    <dd className="mt-1 text-sm text-gray-900 dark:text-gray-300">{watch.retailer}</dd>
                  </div>
                )}
              </dl>
            </Card>

            {(watch.case_diameter ||
              watch.case_thickness ||
              watch.lug_width ||
              watch.water_resistance ||
              watch.power_reserve) && (
              <Card className="p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Specifications</h2>
                <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {watch.case_diameter && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Case Diameter</dt>
                      <dd className="mt-1 text-sm text-gray-900 dark:text-gray-300">{watch.case_diameter}mm</dd>
                    </div>
                  )}
                  {watch.case_thickness && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Case Thickness</dt>
                      <dd className="mt-1 text-sm text-gray-900 dark:text-gray-300">{watch.case_thickness}mm</dd>
                    </div>
                  )}
                  {watch.lug_width && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Lug Width</dt>
                      <dd className="mt-1 text-sm text-sm text-gray-900 dark:text-gray-300">{watch.lug_width}mm</dd>
                    </div>
                  )}
                  {watch.water_resistance && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Water Resistance</dt>
                      <dd className="mt-1 text-sm text-gray-900 dark:text-gray-300">{watch.water_resistance}m</dd>
                    </div>
                  )}
                  {watch.power_reserve && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Power Reserve</dt>
                      <dd className="mt-1 text-sm text-gray-900 dark:text-gray-300">{watch.power_reserve} hours</dd>
                    </div>
                  )}
                </dl>
              </Card>
            )}

            {watch.complications && watch.complications.length > 0 && (
              <Card className="p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Complications</h2>
                <div className="flex flex-wrap gap-2">
                  {watch.complications.map((comp) => (
                    <span
                      key={comp.id}
                      className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                    >
                      {comp.name}
                    </span>
                  ))}
                </div>
              </Card>
            )}

            {(watch.current_market_value || watch.last_value_update) && (
              <Card className="p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Market Value</h2>
                <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {watch.current_market_value && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Current Market Value</dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {formatCurrency(
                          watch.current_market_value,
                          watch.current_market_currency || watch.purchase_currency
                        )}
                      </dd>
                    </div>
                  )}
                  {watch.last_value_update && (
                    <div>
                      <dt className="text-sm font-medium text-gray-500">Last Updated</dt>
                      <dd className="mt-1 text-sm text-gray-900">
                        {formatDate(watch.last_value_update)}
                      </dd>
                    </div>
                  )}
                </dl>
              </Card>
            )}

            {watch.notes && (
              <Card className="p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Notes</h2>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">{watch.notes}</p>
              </Card>
            )}
          </div>
        </div>
      </div>

      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Watch"
        size="xl"
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
          <p className="text-gray-600">
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

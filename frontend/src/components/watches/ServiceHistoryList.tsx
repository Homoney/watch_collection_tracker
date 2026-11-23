import { useState } from 'react'
import { Calendar, DollarSign, FileText, Trash2, Edit, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { ServiceHistory } from '@/types'
import { useServiceHistory, useDeleteServiceHistory } from '@/hooks/useServiceHistory'
import { format } from 'date-fns'
import ServiceDocuments from './ServiceDocuments'

interface ServiceHistoryListProps {
  watchId: string
  onAddService: () => void
  onEditService: (service: ServiceHistory) => void
}

export default function ServiceHistoryList({
  watchId,
  onAddService,
  onEditService,
}: ServiceHistoryListProps) {
  const { data: services, isLoading, error } = useServiceHistory(watchId)
  const deleteMutation = useDeleteServiceHistory()
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)
  const [expandedServiceId, setExpandedServiceId] = useState<string | null>(null)

  const formatDate = (dateString: string) => {
    return format(new Date(dateString), 'MMMM d, yyyy')
  }

  const formatCost = (cost: number | null, currency: string) => {
    if (cost === null) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(cost)
  }

  const isOverdue = (nextServiceDue: string | null) => {
    if (!nextServiceDue) return false
    return new Date(nextServiceDue) < new Date()
  }

  const handleDelete = async (serviceId: string) => {
    try {
      await deleteMutation.mutateAsync({ watchId, serviceId })
      setDeleteConfirmId(null)
    } catch (error) {
      console.error('Failed to delete service record:', error)
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
      <div className="p-4 bg-red-50 border border-red-200 rounded-sm">
        <p className="text-red-800">Failed to load service history</p>
      </div>
    )
  }

  if (!services || services.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="mx-auto h-12 w-12 text-muted-foreground" />
        <h3 className="mt-2 text-sm font-medium text-foreground">No service history</h3>
        <p className="mt-1 text-sm text-muted-foreground">
          Get started by adding your first service record.
        </p>
        <div className="mt-6">
          <button
            type="button"
            onClick={onAddService}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-sm text-white bg-blue-600 hover:bg-blue-700"
          >
            Add Service Record
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-light tracking-wide text-foreground">
          Service History ({services.length})
        </h3>
        <button
          type="button"
          onClick={onAddService}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-sm text-white bg-blue-600 hover:bg-blue-700"
        >
          Add Service Record
        </button>
      </div>

      <div className="space-y-4">
        {services.map((service, index) => (
          <div
            key={service.id}
            className="bg-card border border-border rounded-sm p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                {/* Service Date and Provider */}
                <div className="flex items-center gap-2 mb-2">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium text-foreground">
                    {formatDate(service.service_date)}
                  </span>
                  {index === 0 && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                      Most Recent
                    </span>
                  )}
                </div>

                <div className="ml-6 space-y-2">
                  {/* Provider */}
                  <p className="text-sm text-foreground">
                    <span className="font-medium">Provider:</span> {service.provider}
                  </p>

                  {/* Service Type */}
                  {service.service_type && (
                    <p className="text-sm text-muted-foreground">
                      <span className="font-medium">Type:</span> {service.service_type}
                    </p>
                  )}

                  {/* Description */}
                  {service.description && (
                    <p className="text-sm text-muted-foreground">{service.description}</p>
                  )}

                  {/* Cost */}
                  {service.cost !== null && (
                    <div className="flex items-center gap-2 text-sm">
                      <DollarSign className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium text-foreground">
                        {formatCost(service.cost, service.cost_currency)}
                      </span>
                    </div>
                  )}

                  {/* Next Service Due */}
                  {service.next_service_due && (
                    <div
                      className={`flex items-center gap-2 text-sm ${
                        isOverdue(service.next_service_due)
                          ? 'text-red-600'
                          : 'text-gray-600'
                      }`}
                    >
                      {isOverdue(service.next_service_due) && (
                        <AlertCircle className="h-4 w-4" />
                      )}
                      <span>
                        Next service due: {formatDate(service.next_service_due)}
                        {isOverdue(service.next_service_due) && ' (Overdue)'}
                      </span>
                    </div>
                  )}

                  {/* Documents Count - Clickable to expand */}
                  {service.documents.length > 0 && (
                    <button
                      type="button"
                      onClick={() =>
                        setExpandedServiceId(
                          expandedServiceId === service.id ? null : service.id
                        )
                      }
                      className="flex items-center gap-1 text-sm text-gold hover:opacity-80"
                    >
                      {expandedServiceId === service.id ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                      <span>
                        {service.documents.length} document
                        {service.documents.length !== 1 ? 's' : ''} attached
                      </span>
                    </button>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 ml-4">
                <button
                  type="button"
                  onClick={() => onEditService(service)}
                  className="p-2 text-muted-foreground hover:text-blue-600 rounded-sm hover:bg-accent"
                  title="Edit service record"
                >
                  <Edit className="h-4 w-4" />
                </button>

                {deleteConfirmId === service.id ? (
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleDelete(service.id)}
                      disabled={deleteMutation.isPending}
                      className="px-2 py-1 text-xs font-medium text-white bg-red-600 hover:bg-red-700 rounded"
                    >
                      Confirm
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeleteConfirmId(null)}
                      className="px-2 py-1 text-xs font-medium text-foreground bg-muted hover:bg-accent rounded"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => setDeleteConfirmId(service.id)}
                    className="p-2 text-muted-foreground hover:text-red-600 rounded-sm hover:bg-accent"
                    title="Delete service record"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>

            {/* Expandable Documents Section */}
            {expandedServiceId === service.id && service.documents.length > 0 && (
              <div className="mt-4 pt-4 border-t border-border">
                <ServiceDocuments
                  watchId={watchId}
                  serviceId={service.id}
                  documents={service.documents}
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

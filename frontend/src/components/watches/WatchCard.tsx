import { useNavigate } from 'react-router-dom'
import Card from '@/components/common/Card'
import Badge from '@/components/common/Badge'
import Button from '@/components/common/Button'
import type { WatchListItem } from '@/types'

interface WatchCardProps {
  watch: WatchListItem
  onEdit?: (watch: WatchListItem) => void
  onDelete?: (watch: WatchListItem) => void
}

export default function WatchCard({ watch, onEdit, onDelete }: WatchCardProps) {
  const navigate = useNavigate()

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
      month: 'short',
      day: 'numeric',
    })
  }

  const handleCardClick = () => {
    navigate(`/watches/${watch.id}`)
  }

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    onEdit?.(watch)
  }

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    onDelete?.(watch)
  }

  return (
    <Card onClick={handleCardClick} className="p-4 hover:shadow-lg transition-shadow">
      <div className="flex flex-col h-full">
        <div className="flex-1">
          <div className="aspect-w-16 aspect-h-9 bg-gray-100 rounded-md mb-3 flex items-center justify-center">
            <svg
              className="w-16 h-16 text-gray-400"
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
          </div>

          <div className="mb-2">
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {watch.brand?.name || 'Unknown Brand'}
            </h3>
            <p className="text-sm text-gray-600 truncate">{watch.model}</p>
            {watch.reference_number && (
              <p className="text-xs text-gray-500 truncate">Ref: {watch.reference_number}</p>
            )}
          </div>

          {watch.collection && (
            <div className="mb-2">
              <span
                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
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

          <div className="space-y-1 text-sm text-gray-600 mb-3">
            <div className="flex justify-between">
              <span>Purchase:</span>
              <span className="font-medium">
                {formatCurrency(watch.purchase_price, watch.purchase_currency)}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Date:</span>
              <span>{formatDate(watch.purchase_date)}</span>
            </div>
          </div>

          {watch.condition && (
            <div className="mb-3">
              <Badge condition={watch.condition} />
            </div>
          )}
        </div>

        {(onEdit || onDelete) && (
          <div className="flex gap-2 pt-3 border-t border-gray-200">
            {onEdit && (
              <Button variant="secondary" size="sm" onClick={handleEdit} className="flex-1">
                Edit
              </Button>
            )}
            {onDelete && (
              <Button variant="danger" size="sm" onClick={handleDelete} className="flex-1">
                Delete
              </Button>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}

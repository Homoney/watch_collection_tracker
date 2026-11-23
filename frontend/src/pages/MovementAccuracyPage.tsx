import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Clock } from 'lucide-react'
import AppLayout from '@/components/layout/AppLayout'
import { useWatch } from '@/hooks/useWatches'
import { useAccuracyReadings } from '@/hooks/useMovementAccuracy'
import { AccuracyAnalytics } from '@/components/watches/AccuracyAnalytics'
import { AccuracyChart } from '@/components/watches/AccuracyChart'
import { AccuracyReadingsList } from '@/components/watches/AccuracyReadingsList'
import { AccuracyReadingForm } from '@/components/watches/AccuracyReadingForm'

export default function MovementAccuracyPage() {
  const { id } = useParams<{ id: string }>()
  const watchId = id!

  const { data: watch, isLoading: watchLoading } = useWatch(watchId)
  const { data: readings } = useAccuracyReadings(watchId)
  const [isFormOpen, setIsFormOpen] = useState(false)

  const isFirstReading = !readings || readings.length === 0

  if (watchLoading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </AppLayout>
    )
  }

  if (!watch) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <p className="text-xl text-muted-foreground">Watch not found</p>
            <Link
              to="/watches"
              className="mt-4 inline-flex items-center gap-2 text-gold hover:opacity-80"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Watches
            </Link>
          </div>
        </div>
      </AppLayout>
    )
  }

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link
          to={`/watches/${watchId}`}
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Watch Details
        </Link>

        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Clock className="w-8 h-8 text-gold" />
              <h1 className="text-3xl font-light tracking-wide text-foreground sm:text-4xl">Movement Accuracy</h1>
            </div>
            <p className="text-lg text-muted-foreground">
              {watch.brand?.name} {watch.model}
              {watch.reference_number && (
                <span className="text-muted-foreground"> • Ref. {watch.reference_number}</span>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="space-y-8">
        {/* Analytics Card */}
        <div className="bg-card rounded-sm border border-border p-6">
          <h2 className="text-xl font-light tracking-wide text-foreground mb-6">Accuracy Metrics</h2>
          <AccuracyAnalytics watchId={watchId} />
        </div>

        {/* Chart Card */}
        <div className="bg-card rounded-sm border border-border p-6">
          <AccuracyChart watchId={watchId} />
        </div>

        {/* Readings List Card */}
        <div className="bg-card rounded-sm border border-border p-6">
          <AccuracyReadingsList watchId={watchId} onAddReading={() => setIsFormOpen(true)} />
        </div>
      </div>

      {/* Reading Form Modal */}
      <AccuracyReadingForm
        watchId={watchId}
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        isFirstReading={isFirstReading}
      />
    </div>
    </AppLayout>
  )
}

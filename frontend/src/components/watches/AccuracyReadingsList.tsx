import { useState } from 'react'
import { Clock, Target, Trash2, Calendar, FileText, AlertCircle } from 'lucide-react'
import { useAccuracyReadings, useDeleteAccuracyReading } from '@/hooks/useMovementAccuracy'
import { format } from 'date-fns'

interface AccuracyReadingsListProps {
  watchId: string
  onAddReading: () => void
}

export function AccuracyReadingsList({ watchId, onAddReading }: AccuracyReadingsListProps) {
  const { data: readings, isLoading, error } = useAccuracyReadings(watchId)
  const deleteMutation = useDeleteAccuracyReading()
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleDelete = async (readingId: string) => {
    if (!window.confirm('Are you sure you want to delete this reading? This action cannot be undone.')) {
      return
    }

    setDeletingId(readingId)
    try {
      await deleteMutation.mutateAsync({ watchId, readingId })
    } catch (error) {
      console.error('Failed to delete reading:', error)
    } finally {
      setDeletingId(null)
    }
  }

  const formatDrift = (drift: number | null) => {
    if (drift === null) return null
    const sign = drift >= 0 ? '+' : ''
    return `${sign}${drift.toFixed(2)} spd`
  }

  const getDriftColor = (drift: number | null) => {
    if (drift === null) return ''
    const abs = Math.abs(drift)
    if (abs <= 5) return 'text-green-600 dark:text-green-400'
    if (abs <= 10) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Failed to load accuracy readings</p>
        </div>
      </div>
    )
  }

  if (!readings || readings.length === 0) {
    return (
      <div className="text-center py-12">
        <Clock className="w-16 h-16 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No accuracy readings yet</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
          Start tracking your watch's accuracy by recording your first baseline reading.
        </p>
        <button
          onClick={onAddReading}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <Clock className="w-5 h-5" />
          Record First Reading
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Readings ({readings.length})
        </h3>
        <button
          onClick={onAddReading}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <Clock className="w-4 h-4" />
          Add Reading
        </button>
      </div>

      {/* Timeline */}
      <div className="space-y-4">
        {readings.map((reading, index) => {
          const isFirst = index === 0
          const readingDate = new Date(reading.reference_time)

          return (
            <div
              key={reading.id}
              className="relative border border-gray-200 dark:border-gray-700 rounded-lg p-4 bg-white dark:bg-gray-800 hover:shadow-md transition-shadow"
            >
              {/* Badge */}
              <div className="flex items-start justify-between gap-4 mb-3">
                <div className="flex items-center gap-2">
                  {reading.is_initial_reading ? (
                    <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded-full">
                      <Target className="w-3 h-3" />
                      Initial
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200 rounded-full">
                      <Clock className="w-3 h-3" />
                      Measurement
                    </span>
                  )}
                  {isFirst && (
                    <span className="px-2 py-1 text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 rounded-full">
                      Latest
                    </span>
                  )}
                  {!reading.is_atomic_source && (
                    <span className="px-2 py-1 text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 rounded-full">
                      Fallback Time
                    </span>
                  )}
                </div>

                {/* Delete Button */}
                <button
                  onClick={() => handleDelete(reading.id)}
                  disabled={deletingId === reading.id}
                  className="text-gray-400 hover:text-red-600 dark:hover:text-red-400 transition-colors disabled:opacity-50"
                  title="Delete reading"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {/* Reading Info */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-start gap-2">
                  <Calendar className="w-4 h-4 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-gray-600 dark:text-gray-400">Date & Time</p>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {format(readingDate, 'MMM d, yyyy')}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-500">
                      {format(readingDate, 'h:mm:ss a')}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-2">
                  <Clock className="w-4 h-4 text-gray-400 mt-0.5" />
                  <div>
                    <p className="text-gray-600 dark:text-gray-400">Second Mark</p>
                    <p className="font-medium text-gray-900 dark:text-white">
                      :{reading.watch_seconds_position.toString().padStart(2, '0')}
                    </p>
                  </div>
                </div>

                {/* Drift Display (for subsequent readings) */}
                {!reading.is_initial_reading && reading.drift_seconds_per_day !== null && (
                  <>
                    <div className="flex items-start gap-2">
                      <Target className="w-4 h-4 text-gray-400 mt-0.5" />
                      <div>
                        <p className="text-gray-600 dark:text-gray-400">Drift</p>
                        <p className={`font-semibold ${getDriftColor(reading.drift_seconds_per_day)}`}>
                          {formatDrift(reading.drift_seconds_per_day)}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-500">
                          {reading.drift_seconds_per_day > 0 ? 'Running fast' : 'Running slow'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-2">
                      <Clock className="w-4 h-4 text-gray-400 mt-0.5" />
                      <div>
                        <p className="text-gray-600 dark:text-gray-400">Time Elapsed</p>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {reading.hours_since_initial?.toFixed(1)} hours
                        </p>
                      </div>
                    </div>
                  </>
                )}
              </div>

              {/* Notes */}
              {reading.notes && (
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                  <div className="flex items-start gap-2">
                    <FileText className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Notes</p>
                      <p className="text-sm text-gray-900 dark:text-white">{reading.notes}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

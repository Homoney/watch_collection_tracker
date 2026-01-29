import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Info } from 'lucide-react'
import Modal from '@/components/common/Modal'
import { AtomicClock } from './AtomicClock'
import { useCreateAccuracyReading } from '@/hooks/useMovementAccuracy'
import type { MovementAccuracyReadingCreate } from '@/types'

interface AccuracyReadingFormProps {
  watchId: string
  isOpen: boolean
  onClose: () => void
  isFirstReading?: boolean
}

interface FormData {
  is_initial_reading: boolean
  notes: string
}

export function AccuracyReadingForm({ watchId, isOpen, onClose, isFirstReading = false }: AccuracyReadingFormProps) {
  const [selectedMark, setSelectedMark] = useState<0 | 15 | 30 | 45 | null>(null)
  const createMutation = useCreateAccuracyReading()

  const {
    register,
    handleSubmit,
    reset,
    watch,
  } = useForm<FormData>({
    defaultValues: {
      is_initial_reading: isFirstReading,
      notes: '',
    },
  })

  const isInitial = watch('is_initial_reading')

  const onSubmit = async (formData: FormData) => {
    if (selectedMark === null) {
      return // Should not happen due to validation
    }

    const data: MovementAccuracyReadingCreate = {
      watch_seconds_position: selectedMark,
      is_initial_reading: formData.is_initial_reading,
      notes: formData.notes || null,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    }

    try {
      await createMutation.mutateAsync({ watchId, data })
      handleClose()
    } catch (error) {
      // Error is handled by mutation error state
      console.error('Failed to create reading:', error)
    }
  }

  const handleClose = () => {
    reset()
    setSelectedMark(null)
    onClose()
  }

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Record Accuracy Reading" size="lg">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Atomic Clock */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 bg-gray-50 dark:bg-gray-900">
          <AtomicClock
            onSecondMarkSelect={setSelectedMark}
            selectedMark={selectedMark}
            timezone={Intl.DateTimeFormat().resolvedOptions().timeZone}
          />
        </div>

        {/* Initial Reading Checkbox */}
        <div className="space-y-3">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              {...register('is_initial_reading')}
              disabled={isFirstReading}
              className="mt-1 w-4 h-4 text-blue-600 bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 rounded focus:ring-blue-500 focus:ring-2"
            />
            <div className="flex-1">
              <span className="font-medium text-gray-900 dark:text-white">
                This is an initial reading (baseline)
              </span>
              {isFirstReading && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Your first reading must be marked as initial.
                </p>
              )}
            </div>
          </label>

          {/* Explainer */}
          <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
            <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-900 dark:text-blue-100 space-y-1">
              {isInitial ? (
                <>
                  <p className="font-medium">Initial Reading</p>
                  <p>
                    This establishes a baseline where your watch is perfectly synced with atomic time. Use this after
                    regulating your watch, after service, or when starting to track accuracy.
                  </p>
                </>
              ) : (
                <>
                  <p className="font-medium">Subsequent Reading</p>
                  <p>
                    This measures how much your watch has drifted since your last initial reading. The system will
                    calculate drift in seconds per day (positive = running fast, negative = running slow).
                  </p>
                  <p className="text-xs mt-1 text-blue-700 dark:text-blue-300">
                    Note: Must be at least 6 hours after your last initial reading.
                  </p>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Notes */}
        <div className="space-y-2">
          <label htmlFor="notes" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Notes (optional)
          </label>
          <textarea
            id="notes"
            {...register('notes')}
            rows={3}
            placeholder="e.g., After 24 hours on wrist, crown up position"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
          />
        </div>

        {/* Error Messages */}
        {createMutation.isError && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <p className="text-sm text-red-800 dark:text-red-200">
              {createMutation.error instanceof Error ? createMutation.error.message : 'Failed to create reading'}
            </p>
          </div>
        )}

        {/* Form Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={handleClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={selectedMark === null || createMutation.isPending}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {createMutation.isPending ? 'Recording...' : 'Record Reading'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Info } from 'lucide-react'
import Modal, { ModalClose } from '@/components/common/Modal'
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
    formState: { isDirty },
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
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Record Accuracy Reading"
      size="lg"
      form
      dirty={isDirty || selectedMark !== null}
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Atomic Clock */}
        <div className="rounded-sm border border-border bg-card p-6">
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
              className="mt-1 h-4 w-4 rounded-sm accent-[hsl(var(--gold))]"
            />
            <div className="flex-1">
              <span className="font-medium text-foreground">
                This is an initial reading (baseline)
              </span>
              {isFirstReading && (
                <p className="mt-1 text-sm text-muted-foreground">
                  Your first reading must be marked as initial.
                </p>
              )}
            </div>
          </label>

          {/* Explainer */}
          <div className="flex items-start gap-2 rounded-sm border border-border bg-muted p-3">
            <Info className="mt-0.5 h-5 w-5 flex-shrink-0 text-gold" />
            <div className="space-y-1 text-sm text-foreground">
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
                  <p className="mt-1 text-xs text-muted-foreground">
                    Note: Must be at least 6 hours after your last initial reading.
                  </p>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Notes */}
        <div className="space-y-2">
          <label htmlFor="notes" className="block text-[11px] font-medium uppercase tracking-[0.16em] text-muted-foreground">
            Notes (optional)
          </label>
          <textarea
            id="notes"
            {...register('notes')}
            rows={3}
            placeholder="e.g., After 24 hours on wrist, crown up position"
            className="block w-full rounded-sm border border-input bg-card px-3 py-2 text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring sm:text-sm"
          />
        </div>

        {/* Error Messages */}
        {createMutation.isError && (
          <div className="rounded-sm border border-destructive/40 bg-destructive/10 p-3">
            <p className="text-sm text-destructive">
              {createMutation.error instanceof Error ? createMutation.error.message : 'Failed to create reading'}
            </p>
          </div>
        )}

        {/* Form Actions */}
        <div className="flex justify-end gap-3 border-t border-border pt-4">
          <ModalClose>
            {(close) => (
              <button
                type="button"
                onClick={close}
                className="inline-flex h-10 items-center justify-center gap-2 rounded-sm border border-input bg-transparent px-5 text-[11px] font-medium uppercase tracking-[0.18em] text-foreground hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                Cancel
              </button>
            )}
          </ModalClose>
          <button
            type="submit"
            disabled={selectedMark === null || createMutation.isPending}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-sm border border-primary bg-primary px-5 text-[11px] font-medium uppercase tracking-[0.18em] text-primary-foreground hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          >
            {createMutation.isPending ? 'Recording...' : 'Record Reading'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

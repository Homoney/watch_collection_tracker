import { useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import AppLayout from '@/components/layout/AppLayout'
import ComparisonTable from '@/components/watches/ComparisonTable'
import Button from '@/components/common/Button'
import Spinner from '@/components/common/Spinner'
import { useCompareWatches } from '@/hooks/useCompareWatches'

export default function ComparePage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  // Parse IDs from URL
  const watchIds = searchParams.get('ids')?.split(',').filter(Boolean) || []

  // Validate count
  useEffect(() => {
    if (watchIds.length < 2) {
      navigate('/watches')
    } else if (watchIds.length > 4) {
      // Take first 4 only
      navigate(`/compare?ids=${watchIds.slice(0, 4).join(',')}`, { replace: true })
    }
  }, [watchIds.length, navigate])

  // Fetch watches
  const { watches, isLoading, hasErrors } = useCompareWatches(watchIds.slice(0, 4))

  const handleRemoveWatch = (id: string) => {
    const newIds = watchIds.filter((wid) => wid !== id)
    if (newIds.length < 2) {
      navigate('/watches')
    } else {
      navigate(`/compare?ids=${newIds.join(',')}`)
    }
  }

  if (watchIds.length < 2) {
    return null // Will redirect via useEffect
  }

  if (isLoading) {
    return (
      <AppLayout>
        <div className="flex justify-center items-center py-12">
          <Spinner size="lg" />
        </div>
      </AppLayout>
    )
  }

  if (hasErrors && watches.length === 0) {
    return (
      <AppLayout>
        <div className="text-center py-12">
          <p className="text-red-600 dark:text-red-400">
            Failed to load watches. Please try again.
          </p>
          <Button onClick={() => navigate('/watches')} className="mt-4">
            Back to Watches
          </Button>
        </div>
      </AppLayout>
    )
  }

  // Filter out failed watches and redirect if less than 2
  if (watches.length < 2) {
    navigate('/watches')
    return null
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Watch Comparison</h1>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Comparing {watches.length} {watches.length === 1 ? 'watch' : 'watches'}
            </p>
          </div>
          <Button onClick={() => navigate('/watches')} variant="secondary">
            ← Back to Watches
          </Button>
        </div>

        {hasErrors && watches.length < watchIds.length && (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              Some watches could not be loaded and have been excluded from the comparison.
            </p>
          </div>
        )}

        <ComparisonTable watches={watches} onRemoveWatch={handleRemoveWatch} />
      </div>
    </AppLayout>
  )
}

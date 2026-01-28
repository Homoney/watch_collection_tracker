import { TrendingUp, TrendingDown, DollarSign, Calendar } from 'lucide-react'
import { useWatchAnalytics } from '@/hooks/useMarketValues'

interface WatchAnalyticsProps {
  watchId: string
}

export default function WatchAnalytics({ watchId }: WatchAnalyticsProps) {
  const { data: analytics, isLoading, error } = useWatchAnalytics(watchId)

  const formatCurrency = (value: number | null, currency: string) => {
    if (value === null) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
    }).format(value)
  }

  const formatPercent = (value: number | null) => {
    if (value === null) return 'N/A'
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(2)}%`
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-white"></div>
      </div>
    )
  }

  if (error || !analytics) {
    return (
      <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <p className="text-red-800 dark:text-red-200">Failed to load analytics</p>
      </div>
    )
  }

  const hasROI = analytics.roi_percentage !== null
  const hasValues = analytics.total_valuations > 0

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-medium text-gray-900 dark:text-white">Performance Analytics</h3>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Current Value */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-1">
            <DollarSign className="h-4 w-4" />
            <span>Current Value</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {formatCurrency(analytics.current_value, analytics.current_currency)}
          </p>
        </div>

        {/* ROI */}
        {hasROI && (
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-1">
              {analytics.roi_percentage! >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-600 dark:text-green-400" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600 dark:text-red-400" />
              )}
              <span>Return on Investment</span>
            </div>
            <p
              className={`text-2xl font-bold ${
                analytics.roi_percentage! >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
              }`}
            >
              {formatPercent(analytics.roi_percentage)}
            </p>
          </div>
        )}

        {/* Total Return */}
        {analytics.total_return !== null && (
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-1">
              <DollarSign className="h-4 w-4" />
              <span>Total Return</span>
            </div>
            <p
              className={`text-2xl font-bold ${
                analytics.total_return >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
              }`}
            >
              {formatCurrency(analytics.total_return, analytics.purchase_currency)}
            </p>
          </div>
        )}

        {/* Annualized Return */}
        {analytics.annualized_return !== null && (
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-1">
              <Calendar className="h-4 w-4" />
              <span>Annualized Return</span>
            </div>
            <p
              className={`text-2xl font-bold ${
                analytics.annualized_return >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
              }`}
            >
              {formatPercent(analytics.annualized_return)}
            </p>
          </div>
        )}
      </div>

      {/* Value Changes */}
      {hasValues && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Value Changes</h4>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {/* 30 Days */}
            {analytics.value_change_30d !== null && (
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Last 30 Days</p>
                <p
                  className={`text-lg font-semibold ${
                    analytics.value_change_30d >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  {formatCurrency(analytics.value_change_30d, analytics.current_currency)}
                </p>
              </div>
            )}

            {/* 90 Days */}
            {analytics.value_change_90d !== null && (
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Last 90 Days</p>
                <p
                  className={`text-lg font-semibold ${
                    analytics.value_change_90d >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  {formatCurrency(analytics.value_change_90d, analytics.current_currency)}
                </p>
              </div>
            )}

            {/* 1 Year */}
            {analytics.value_change_1y !== null && (
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Last Year</p>
                <p
                  className={`text-lg font-semibold ${
                    analytics.value_change_1y >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                  }`}
                >
                  {formatCurrency(analytics.value_change_1y, analytics.current_currency)}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Purchase Info */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-4">Purchase Information</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Purchase Price</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {formatCurrency(analytics.purchase_price, analytics.purchase_currency)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Valuations</p>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {analytics.total_valuations}
            </p>
          </div>
        </div>
      </div>

      {!hasValues && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <p className="text-sm text-blue-800 dark:text-blue-200">
            Add market values to track your watch's performance over time.
          </p>
        </div>
      )}
    </div>
  )
}

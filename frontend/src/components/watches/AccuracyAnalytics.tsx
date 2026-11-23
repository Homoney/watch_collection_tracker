import { TrendingUp, TrendingDown, Minus, Target, BarChart3, Calendar, Info } from 'lucide-react'
import { useAccuracyAnalytics } from '@/hooks/useMovementAccuracy'

interface AccuracyAnalyticsProps {
  watchId: string
}

export function AccuracyAnalytics({ watchId }: AccuracyAnalyticsProps) {
  const { data: analytics, isLoading } = useAccuracyAnalytics(watchId)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!analytics) {
    return null
  }

  const formatDrift = (drift: number | null, includeSign: boolean = true) => {
    if (drift === null) return 'N/A'
    const sign = includeSign && drift >= 0 ? '+' : ''
    return `${sign}${drift.toFixed(2)} spd`
  }

  const getDriftColor = (drift: number | null): string => {
    if (drift === null) return 'text-gray-500 dark:text-gray-400'
    const abs = Math.abs(drift)
    if (abs <= 5) return 'text-positive'
    if (abs <= 10) return 'text-yellow-700 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const getDriftBgColor = (drift: number | null): string => {
    if (drift === null) return 'bg-gray-50 dark:bg-gray-900'
    const abs = Math.abs(drift)
    if (abs <= 5) return 'bg-green-50 dark:bg-green-900/20'
    if (abs <= 10) return 'bg-yellow-50 dark:bg-yellow-900/20'
    return 'bg-red-50 dark:bg-red-900/20'
  }

  const getDriftBorderColor = (drift: number | null): string => {
    if (drift === null) return 'border-gray-200 dark:border-gray-700'
    const abs = Math.abs(drift)
    if (abs <= 5) return 'border-green-200 dark:border-green-800'
    if (abs <= 10) return 'border-yellow-200 dark:border-yellow-800'
    return 'border-red-200 dark:border-red-800'
  }

  const getTrendIcon = (drift: number | null) => {
    if (drift === null) return <Minus className="w-5 h-5" />
    if (drift > 0) return <TrendingUp className="w-5 h-5" />
    if (drift < 0) return <TrendingDown className="w-5 h-5" />
    return <Minus className="w-5 h-5" />
  }

  const getTrendText = (drift: number | null): string => {
    if (drift === null) return 'No data'
    if (drift > 0) return 'Running fast'
    if (drift < 0) return 'Running slow'
    return 'Perfect accuracy'
  }

  const hasData = analytics.total_subsequent_readings > 0

  return (
    <div className="space-y-6">
      {/* Info Box */}
      {!hasData && (
        <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-sm">
          <Info className="w-5 h-5 text-gold flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-900 dark:text-blue-100">
            <p className="font-medium mb-1">Record your first measurement</p>
            <p>
              After recording an initial reading, wait at least 6 hours and then record a subsequent reading to start
              tracking drift. The longer you wait between readings, the more accurate your drift calculation will be.
            </p>
          </div>
        </div>
      )}

      {/* Main Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Current Drift */}
        <div
          className={`p-6 rounded-sm border ${getDriftBgColor(analytics.current_drift_spd)} ${getDriftBorderColor(
            analytics.current_drift_spd
          )}`}
        >
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-muted-foreground" />
              <h3 className="text-sm font-medium text-foreground">Current Drift</h3>
            </div>
            <span className={getDriftColor(analytics.current_drift_spd)}>{getTrendIcon(analytics.current_drift_spd)}</span>
          </div>
          <div className="space-y-1">
            <p className={`text-3xl font-bold ${getDriftColor(analytics.current_drift_spd)}`}>
              {formatDrift(analytics.current_drift_spd)}
            </p>
            <p className="text-sm text-muted-foreground">{getTrendText(analytics.current_drift_spd)}</p>
          </div>
        </div>

        {/* Average Drift */}
        <div
          className={`p-6 rounded-sm border ${getDriftBgColor(analytics.average_drift_spd)} ${getDriftBorderColor(
            analytics.average_drift_spd
          )}`}
        >
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-muted-foreground" />
              <h3 className="text-sm font-medium text-foreground">Average Drift</h3>
            </div>
            <span className={getDriftColor(analytics.average_drift_spd)}>{getTrendIcon(analytics.average_drift_spd)}</span>
          </div>
          <div className="space-y-1">
            <p className={`text-3xl font-bold ${getDriftColor(analytics.average_drift_spd)}`}>
              {formatDrift(analytics.average_drift_spd)}
            </p>
            <p className="text-sm text-muted-foreground">All-time average</p>
          </div>
        </div>

        {/* Best Accuracy */}
        <div
          className={`p-6 rounded-sm border ${getDriftBgColor(analytics.best_accuracy_spd)} ${getDriftBorderColor(
            analytics.best_accuracy_spd
          )}`}
        >
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-2">
              <Target className="w-5 h-5 text-muted-foreground" />
              <h3 className="text-sm font-medium text-foreground">Best Accuracy</h3>
            </div>
          </div>
          <div className="space-y-1">
            <p className={`text-3xl font-bold ${getDriftColor(analytics.best_accuracy_spd)}`}>
              {formatDrift(analytics.best_accuracy_spd, false)}
            </p>
            <p className="text-sm text-muted-foreground">Closest to zero</p>
          </div>
        </div>
      </div>

      {/* Time-Based Trends */}
      {hasData && (
        <div className="border border-border rounded-sm p-6 bg-card">
          <div className="flex items-center gap-2 mb-4">
            <Calendar className="w-5 h-5 text-muted-foreground" />
            <h3 className="text-lg font-light tracking-wide text-foreground">Trend Analysis</h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">7-Day Average</p>
              <p className={`text-xl font-semibold ${getDriftColor(analytics.drift_7d_avg)}`}>
                {formatDrift(analytics.drift_7d_avg)}
              </p>
            </div>

            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">30-Day Average</p>
              <p className={`text-xl font-semibold ${getDriftColor(analytics.drift_30d_avg)}`}>
                {formatDrift(analytics.drift_30d_avg)}
              </p>
            </div>

            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">90-Day Average</p>
              <p className={`text-xl font-semibold ${getDriftColor(analytics.drift_90d_avg)}`}>
                {formatDrift(analytics.drift_90d_avg)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Reading Statistics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-muted border border-border rounded-sm">
          <p className="text-sm text-muted-foreground mb-1">Total Readings</p>
          <p className="text-2xl font-bold text-foreground">{analytics.total_readings}</p>
        </div>

        <div className="p-4 bg-muted border border-border rounded-sm">
          <p className="text-sm text-muted-foreground mb-1">Initial</p>
          <p className="text-2xl font-bold text-gold">{analytics.total_initial_readings}</p>
        </div>

        <div className="p-4 bg-muted border border-border rounded-sm">
          <p className="text-sm text-muted-foreground mb-1">Measurements</p>
          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">{analytics.total_subsequent_readings}</p>
        </div>

        <div className="p-4 bg-muted border border-border rounded-sm">
          <p className="text-sm text-muted-foreground mb-1">Days Tracked</p>
          <p className="text-2xl font-bold text-foreground">{analytics.date_range_days ?? 0}</p>
        </div>
      </div>
    </div>
  )
}

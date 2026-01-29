import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { format } from 'date-fns'
import { useAccuracyReadings } from '@/hooks/useMovementAccuracy'
import { TrendingUp, Info } from 'lucide-react'

interface AccuracyChartProps {
  watchId: string
}

interface ChartDataPoint {
  date: string
  displayDate: string
  drift: number
  notes?: string
}

export function AccuracyChart({ watchId }: AccuracyChartProps) {
  const { data: readings, isLoading } = useAccuracyReadings(watchId)

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  // Filter for readings with drift data and prepare chart data
  const chartData: ChartDataPoint[] = readings
    ?.filter(r => !r.is_initial_reading && r.drift_seconds_per_day !== null)
    .map(r => ({
      date: r.reference_time,
      displayDate: format(new Date(r.reference_time), 'MMM d'),
      drift: r.drift_seconds_per_day!,
      notes: r.notes || undefined,
    }))
    .reverse() || [] // Reverse to show oldest to newest

  if (chartData.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-12 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900">
        <TrendingUp className="w-16 h-16 text-gray-400 dark:text-gray-600 mb-4" />
        <p className="text-gray-600 dark:text-gray-400 text-center max-w-md">
          No drift data to display yet. Record at least one subsequent reading after your initial baseline to see your
          watch's accuracy trend over time.
        </p>
      </div>
    )
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as ChartDataPoint
      const drift = data.drift
      const driftColor = Math.abs(drift) <= 5 ? 'text-green-600' : Math.abs(drift) <= 10 ? 'text-yellow-600' : 'text-red-600'

      return (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-3">
          <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">
            {format(new Date(data.date), 'MMM d, yyyy h:mm a')}
          </p>
          <p className={`text-lg font-bold ${driftColor}`}>
            {drift >= 0 ? '+' : ''}{drift.toFixed(2)} spd
          </p>
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
            {drift > 0 ? 'Running fast' : drift < 0 ? 'Running slow' : 'Perfect'}
          </p>
          {data.notes && (
            <p className="text-xs text-gray-500 dark:text-gray-500 mt-2 border-t border-gray-200 dark:border-gray-700 pt-2">
              {data.notes}
            </p>
          )}
        </div>
      )
    }
    return null
  }

  // Find min/max for Y-axis
  const drifts = chartData.map(d => d.drift)
  const minDrift = Math.min(...drifts)
  const maxDrift = Math.max(...drifts)
  const yAxisPadding = Math.max(Math.abs(minDrift), Math.abs(maxDrift)) * 0.2
  const yAxisDomain = [
    Math.floor(minDrift - yAxisPadding),
    Math.ceil(maxDrift + yAxisPadding)
  ]

  return (
    <div className="space-y-4">
      {/* Info banner */}
      <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
        <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-900 dark:text-blue-100">
          <p>
            <strong>Understanding drift:</strong> Positive values (above zero) mean your watch is running fast.
            Negative values (below zero) mean it's running slow. Most mechanical watches drift ±5-10 seconds per day.
          </p>
        </div>
      </div>

      {/* Chart */}
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-6 bg-white dark:bg-gray-800">
        <div className="flex items-center gap-2 mb-6">
          <TrendingUp className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Drift Over Time</h3>
        </div>

        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.2} />
            <XAxis
              dataKey="displayDate"
              stroke="#9CA3AF"
              tick={{ fill: '#9CA3AF', fontSize: 12 }}
            />
            <YAxis
              label={{ value: 'Seconds per Day', angle: -90, position: 'insideLeft', fill: '#9CA3AF' }}
              stroke="#9CA3AF"
              tick={{ fill: '#9CA3AF', fontSize: 12 }}
              domain={yAxisDomain}
            />
            <Tooltip content={<CustomTooltip />} />

            {/* Reference line at zero (perfect accuracy) */}
            <ReferenceLine
              y={0}
              stroke="#10B981"
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{ value: 'Perfect', position: 'right', fill: '#10B981' }}
            />

            {/* Drift line */}
            <Line
              type="monotone"
              dataKey="drift"
              stroke="#3B82F6"
              strokeWidth={3}
              dot={{ fill: '#3B82F6', r: 5 }}
              activeDot={{ r: 7 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

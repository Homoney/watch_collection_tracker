import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'
import { useMarketValues } from '@/hooks/useMarketValues'

interface ValueChartProps {
  watchId: string
}

export default function ValueChart({ watchId }: ValueChartProps) {
  const { data: values, isLoading, error } = useMarketValues(watchId)
  const [isDarkMode, setIsDarkMode] = useState(false)

  // Detect dark mode
  useEffect(() => {
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)')
    setIsDarkMode(darkModeQuery.matches)

    const handler = (e: MediaQueryListEvent) => setIsDarkMode(e.matches)
    darkModeQuery.addEventListener('change', handler)

    return () => darkModeQuery.removeEventListener('change', handler)
  }, [])

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-white"></div>
      </div>
    )
  }

  if (error || !values || values.length === 0) {
    return (
      <div className="p-4 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
        <p className="text-gray-600 dark:text-gray-400 text-center">
          {error ? 'Failed to load value history' : 'No value history available'}
        </p>
      </div>
    )
  }

  // Prepare chart data (reverse to show oldest to newest)
  const chartData = [...values]
    .reverse()
    .map((value) => ({
      date: format(new Date(value.recorded_at), 'MMM dd, yyyy'),
      value: Number(value.value),
      currency: value.currency,
    }))

  // Format currency for tooltip
  const formatCurrency = (value: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
    }).format(value)
  }

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-gray-300 dark:border-gray-600 rounded shadow-lg">
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">{data.date}</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-white">
            {formatCurrency(data.value, data.currency)}
          </p>
        </div>
      )
    }
    return null
  }

  // Calculate min and max for Y axis domain
  const valueNumbers = chartData.map((d) => d.value)
  const minValue = Math.min(...valueNumbers)
  const maxValue = Math.max(...valueNumbers)
  const padding = (maxValue - minValue) * 0.1
  const yDomain = [
    Math.max(0, minValue - padding),
    maxValue + padding,
  ]

  // Theme-aware colors
  const gridColor = isDarkMode ? '#374151' : '#e5e7eb'
  const axisColor = isDarkMode ? '#9ca3af' : '#6b7280'
  const lineColor = isDarkMode ? '#60a5fa' : '#3b82f6'
  const textColor = isDarkMode ? '#e5e7eb' : '#374151'
  const backgroundColor = isDarkMode ? '#1f2937' : '#ffffff'

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Value History</h3>
      <div className="bg-white dark:bg-gray-900 rounded p-4">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <defs>
              <rect id="chartBackground" x="0" y="0" width="100%" height="100%" fill={backgroundColor} />
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12, fill: textColor }}
              stroke={axisColor}
            />
            <YAxis
              domain={yDomain}
              tick={{ fontSize: 12, fill: textColor }}
              stroke={axisColor}
              tickFormatter={(value) =>
                new Intl.NumberFormat('en-US', {
                  notation: 'compact',
                  compactDisplay: 'short',
                }).format(value)
              }
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ color: textColor }} />
            <Line
              type="monotone"
              dataKey="value"
              stroke={lineColor}
              strokeWidth={2}
              dot={{ fill: lineColor, r: 4 }}
              activeDot={{ r: 6 }}
              name="Market Value"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center">
        Showing {chartData.length} valuations from {chartData[0]?.date} to{' '}
        {chartData[chartData.length - 1]?.date}
      </div>
    </div>
  )
}

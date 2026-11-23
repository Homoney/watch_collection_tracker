import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'
import { useMarketValues } from '@/hooks/useMarketValues'
import { useTheme } from '@/contexts/ThemeContext'

interface ValueChartProps {
  watchId: string
}

export default function ValueChart({ watchId }: ValueChartProps) {
  const { data: values, isLoading, error } = useMarketValues(watchId)
  // Follows the app's theme switch, not only the OS setting
  const isDarkMode = useTheme().theme === 'dark'

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold"></div>
      </div>
    )
  }

  if (error || !values || values.length === 0) {
    return (
      <div className="py-6">
        <p className="text-sm text-muted-foreground">
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
  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: { date: string; value: number; currency: string } }> }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="rounded-sm border border-border bg-popover p-3 text-popover-foreground shadow-lg">
          <p className="mb-1 text-xs text-muted-foreground">{data.date}</p>
          <p className="text-base text-foreground">
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
  // Collector's Vault: gold line on hairlines (token values from index.css)
  const gridColor = isDarkMode ? '#25241f' : '#e7e1d3'
  const axisColor = isDarkMode ? '#9a958a' : '#5e5a51'
  const lineColor = isDarkMode ? '#c9a45c' : '#7a5d1c'
  const textColor = isDarkMode ? '#9a958a' : '#5e5a51'

  return (
    <div>
      <h3 className="mb-4 text-[11px] uppercase tracking-[0.24em] text-muted-foreground">Market value over time</h3>
      <div>
        <ResponsiveContainer width="100%" height={260}>
          <LineChart data={chartData}>
            <CartesianGrid stroke={gridColor} vertical={false} />
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
            <Line
              type="monotone"
              dataKey="value"
              stroke={lineColor}
              strokeWidth={1.5}
              dot={{ fill: lineColor, r: 3 }}
              activeDot={{ r: 6 }}
              name="Market Value"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-3 text-xs text-muted-foreground">
        Showing {chartData.length} valuations from {chartData[0]?.date} to{' '}
        {chartData[chartData.length - 1]?.date}
      </div>
    </div>
  )
}

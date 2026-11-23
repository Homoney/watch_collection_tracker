import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import { useCollectionAnalytics } from '@/hooks/useMarketValues'
import { useMediaQuery } from '@/hooks/useMediaQuery'
import { useTheme } from '@/contexts/ThemeContext'
import { cn } from '@/lib/utils'
import type { WatchPerformance } from '@/types'

interface CollectionAnalyticsProps {
  currency?: string
}

// Collector's Vault chart palettes: gold first, then warm and muted tones
// that stay apart from each other on both grounds.
const PALETTE = {
  dark: ['#c9a45c', '#7fc08f', '#8fa9c9', '#d9876f', '#b39ddb', '#e6d3a3', '#6fb3ad', '#9a958a'],
  light: ['#7a5d1c', '#2e6a3c', '#3d5f86', '#a23a2a', '#6a4c93', '#a3823a', '#2f7a74', '#5e5a51'],
}

const panel = 'bg-card border border-border rounded-sm p-6'
const eyebrow = 'text-[11px] uppercase tracking-[0.24em] text-muted-foreground'

export default function CollectionAnalytics({ currency = 'USD' }: CollectionAnalyticsProps) {
  const { data: analytics, isLoading, error } = useCollectionAnalytics(currency)
  const isPhone = useMediaQuery('(max-width: 639px)')
  const dark = useTheme().theme === 'dark'
  const colors = dark ? PALETTE.dark : PALETTE.light
  const axis = dark ? '#9a958a' : '#5e5a51'
  const grid = dark ? '#25241f' : '#e7e1d3'

  const formatCurrency = (value: number | string | null, curr: string) => {
    if (value === null) return 'N/A'
    const numValue = typeof value === 'string' ? Number(value) : value
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: curr,
    }).format(numValue)
  }

  const formatPercent = (value: number | null) => {
    if (value === null) return 'N/A'
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(2)}%`
  }

  // A return is green when it is a gain and red only when it is a loss
  const signColor = (value: number | null | undefined) =>
    value === null || value === undefined ? 'text-foreground' : value >= 0 ? 'text-positive' : 'text-negative'

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold"></div>
      </div>
    )
  }

  if (error || !analytics) {
    return (
      <div className="rounded-sm border border-destructive/40 bg-destructive/10 p-6">
        <p className="text-destructive">Failed to load collection analytics</p>
      </div>
    )
  }

  // Prepare brand chart data from value_by_brand. The API sends Decimals as
  // strings; recharts needs real numbers or the pie draws nothing and the bar
  // axis compares values as text.
  const brandData = Object.entries(analytics.value_by_brand).map(([name, value]) => ({
    name,
    value: Number(value),
  }))

  // Pie chart data for brand distribution
  const brandPieData = brandData.map((brand, index) => ({
    name: brand.name,
    value: brand.value,
    color: colors[index % colors.length],
  }))

  const tooltipStyle = {
    backgroundColor: dark ? '#151513' : '#ffffff',
    border: `1px solid ${dark ? '#2a2823' : '#d9d3c4'}`,
    borderRadius: 2,
    color: dark ? '#ece7da' : '#14130f',
  }

  const performerList = (title: string, list: WatchPerformance[]) => (
    <div className={panel}>
      <h3 className={`${eyebrow} mb-4`}>{title}</h3>
      <ol className="divide-y divide-border">
        {list.map((watch, index) => (
          <li key={watch.watch_id} className="flex items-center justify-between gap-3 py-3">
            <div className="flex min-w-0 items-center gap-3">
              <span className="w-6 text-sm text-gold tabular-nums">{index + 1}</span>
              <div className="min-w-0">
                <p className="truncate text-foreground">
                  {watch.brand} {watch.model}
                </p>
                <p className="text-sm text-muted-foreground">{formatCurrency(watch.current_value, analytics.currency)}</p>
              </div>
            </div>
            <span className={cn('text-sm tabular-nums', signColor(watch.roi))}>{formatPercent(watch.roi)}</span>
          </li>
        ))}
      </ol>
    </div>
  )

  const top = analytics.top_performers[0]
  const lowest = analytics.worst_performers[0]

  return (
    <div className="space-y-6">
      {/* Overview figures: one tray, hairline gaps */}
      <dl className="grid grid-cols-2 gap-px border border-border bg-border lg:grid-cols-4">
        <div className="bg-card p-5 sm:p-6">
          <dt className={eyebrow}>Collection value</dt>
          <dd className="mt-2 text-2xl font-light text-foreground sm:text-3xl">
            {formatCurrency(analytics.total_current_value, analytics.currency)}
          </dd>
          <dd className="mt-1 text-sm text-muted-foreground">{analytics.total_watches} watches</dd>
        </div>
        <div className="bg-card p-5 sm:p-6">
          <dt className={eyebrow}>Average return</dt>
          <dd className={cn('mt-2 text-2xl font-light sm:text-3xl', signColor(analytics.average_roi))}>
            {formatPercent(analytics.average_roi)}
          </dd>
          <dd className="mt-1 text-sm text-muted-foreground">Across collection</dd>
        </div>
        <div className="bg-card p-5 sm:p-6">
          <dt className={eyebrow}>Best return</dt>
          {top ? (
            <>
              <dd className="mt-2 truncate text-foreground">
                {top.brand} {top.model}
              </dd>
              <dd className={cn('mt-1 text-xl font-light', signColor(top.roi))}>{formatPercent(top.roi)}</dd>
            </>
          ) : (
            <dd className="mt-2 text-sm text-muted-foreground">No valuations yet</dd>
          )}
        </div>
        <div className="bg-card p-5 sm:p-6">
          <dt className={eyebrow}>Lowest return</dt>
          {lowest ? (
            <>
              <dd className="mt-2 truncate text-foreground">
                {lowest.brand} {lowest.model}
              </dd>
              <dd className={cn('mt-1 text-xl font-light', signColor(lowest.roi))}>{formatPercent(lowest.roi)}</dd>
            </>
          ) : (
            <dd className="mt-2 text-sm text-muted-foreground">Shown from six valued watches</dd>
          )}
        </div>
      </dl>

      {/* Brand breakdown */}
      {brandData.length > 0 && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className={panel}>
            <h3 className={`${eyebrow} mb-4`}>Value by brand</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={brandData}>
                <CartesianGrid stroke={grid} vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11, fill: axis }}
                  stroke={axis}
                  interval={0}
                  angle={isPhone ? -40 : 0}
                  textAnchor={isPhone ? 'end' : 'middle'}
                  height={isPhone ? 70 : 30}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: axis }}
                  stroke={axis}
                  width={44}
                  tickFormatter={(value) =>
                    new Intl.NumberFormat('en-US', {
                      notation: 'compact',
                      compactDisplay: 'short',
                    }).format(value)
                  }
                />
                <Tooltip
                  contentStyle={tooltipStyle}
                  cursor={{ fill: dark ? '#1c1b18' : '#ebe6da' }}
                  formatter={(value: number) => formatCurrency(value, analytics.currency)}
                />
                <Bar dataKey="value" fill={colors[0]} name="Total value" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className={panel}>
            <h3 className={`${eyebrow} mb-4`}>Collection distribution</h3>
            <ResponsiveContainer width="100%" height={isPhone ? 340 : 300}>
              <PieChart>
                <Pie
                  data={brandPieData}
                  cx="50%"
                  cy={isPhone ? '42%' : '50%'}
                  // On phones the labels would run off the edges: use the legend instead
                  labelLine={false}
                  label={isPhone ? false : ({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={isPhone ? 90 : 100}
                  dataKey="value"
                  stroke={dark ? '#121211' : '#ffffff'}
                >
                  {brandPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} formatter={(value: number) => formatCurrency(value, analytics.currency)} />
                {isPhone && (
                  <Legend
                    verticalAlign="bottom"
                    iconType="square"
                    iconSize={10}
                    wrapperStyle={{ fontSize: 12, color: axis }}
                  />
                )}
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Brand table */}
      {brandData.length > 0 && (
        <div className="overflow-hidden rounded-sm border border-border bg-card">
          <h3 className={`${eyebrow} border-b border-border px-6 py-4`}>Brands in detail</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-border">
              <thead>
                <tr>
                  <th className={`${eyebrow} px-3 py-3 text-left font-normal sm:px-6`}>Brand</th>
                  <th className={`${eyebrow} px-3 py-3 text-right font-normal sm:px-6`}>Total value</th>
                  <th className={`${eyebrow} px-3 py-3 text-right font-normal sm:px-6`}>% of collection</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {brandData.map((brand) => (
                  <tr key={brand.name}>
                    <td className="whitespace-nowrap px-3 py-4 sm:px-6 text-sm text-foreground">{brand.name}</td>
                    <td className="whitespace-nowrap px-3 py-4 sm:px-6 text-right text-sm text-foreground tabular-nums">
                      {formatCurrency(brand.value, analytics.currency)}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 sm:px-6 text-right text-sm text-muted-foreground tabular-nums">
                      {((brand.value / Number(analytics.total_current_value)) * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Best and lowest returns */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {analytics.top_performers.length > 0 && performerList('Best returns', analytics.top_performers)}
        {analytics.worst_performers.length > 0 && performerList('Lowest returns', analytics.worst_performers)}
      </div>

      {analytics.total_watches === 0 && (
        <div className="rounded-sm border border-border bg-card p-6 text-center">
          <p className="text-muted-foreground">
            Add watches with purchase prices and market values to see collection analytics.
          </p>
        </div>
      )}
    </div>
  )
}

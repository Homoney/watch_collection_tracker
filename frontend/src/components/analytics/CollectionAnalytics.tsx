import { TrendingUp, TrendingDown, DollarSign, Award, AlertTriangle } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { useCollectionAnalytics } from '@/hooks/useMarketValues'

interface CollectionAnalyticsProps {
  currency?: string
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#6366f1', '#6b7280']

export default function CollectionAnalytics({ currency = 'USD' }: CollectionAnalyticsProps) {
  const { data: analytics, isLoading, error } = useCollectionAnalytics(currency)

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

  if (isLoading) {
    return (
      <div className="flex justify-center items-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  if (error || !analytics) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800">Failed to load collection analytics</p>
      </div>
    )
  }

  // Prepare brand chart data from value_by_brand
  const brandData = Object.entries(analytics.value_by_brand).map(([name, value]) => ({
    name,
    value,
  }))

  // Prepare pie chart data for brand distribution
  const brandPieData = brandData.map((brand, index) => ({
    name: brand.name,
    value: brand.value,
    color: COLORS[index % COLORS.length],
  }))

  return (
    <div className="space-y-6">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Collection Value */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
            <DollarSign className="h-4 w-4" />
            <span>Total Collection Value</span>
          </div>
          <p className="text-3xl font-bold text-gray-900">
            {formatCurrency(analytics.total_current_value, analytics.currency)}
          </p>
          <p className="mt-2 text-sm text-gray-600">
            {analytics.total_watches} watches
          </p>
        </div>

        {/* Average ROI */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
            {analytics.average_roi && analytics.average_roi >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-600" />
            )}
            <span>Average ROI</span>
          </div>
          <p
            className={`text-3xl font-bold ${
              analytics.average_roi && analytics.average_roi >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {formatPercent(analytics.average_roi)}
          </p>
          <p className="mt-2 text-sm text-gray-600">
            Across collection
          </p>
        </div>

        {/* Top Performer */}
        {analytics.top_performers.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
              <Award className="h-4 w-4 text-green-600" />
              <span>Top Performer</span>
            </div>
            <p className="text-lg font-semibold text-gray-900 truncate">
              {analytics.top_performers[0].brand} {analytics.top_performers[0].model}
            </p>
            <p className="mt-2 text-xl font-bold text-green-600">
              {formatPercent(analytics.top_performers[0].roi)}
            </p>
          </div>
        )}

        {/* Worst Performer */}
        {analytics.worst_performers.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <span>Needs Attention</span>
            </div>
            <p className="text-lg font-semibold text-gray-900 truncate">
              {analytics.worst_performers[0].brand} {analytics.worst_performers[0].model}
            </p>
            <p className="mt-2 text-xl font-bold text-red-600">
              {formatPercent(analytics.worst_performers[0].roi)}
            </p>
          </div>
        )}
      </div>

      {/* Brand Breakdown */}
      {brandData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Bar Chart */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Value by Brand</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={brandData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="#6b7280" />
                <YAxis
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  tickFormatter={(value) =>
                    new Intl.NumberFormat('en-US', {
                      notation: 'compact',
                      compactDisplay: 'short',
                    }).format(value)
                  }
                />
                <Tooltip
                  formatter={(value: number) => formatCurrency(value, analytics.currency)}
                />
                <Bar dataKey="value" fill="#3b82f6" name="Total Value" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Pie Chart */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Collection Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={brandPieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {brandPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => formatCurrency(value, analytics.currency)} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Brand Details Table */}
      {brandData.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Value by Brand</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Brand
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Total Value
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    % of Collection
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {brandData.map((brand) => (
                  <tr key={brand.name} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {brand.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(brand.value, analytics.currency)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {((brand.value / Number(analytics.total_current_value)) * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Top and Worst Performers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Performers */}
        {analytics.top_performers.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
              <Award className="h-5 w-5 text-green-600" />
              Top Performers
            </h3>
            <div className="space-y-3">
              {analytics.top_performers.map((watch, index) => (
                <div
                  key={watch.watch_id}
                  className="flex items-center justify-between p-3 bg-green-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold text-green-600">#{index + 1}</span>
                    <div>
                      <p className="font-medium text-gray-900">
                        {watch.brand} {watch.model}
                      </p>
                      <p className="text-sm text-gray-600">
                        {formatCurrency(watch.current_value, analytics.currency)}
                      </p>
                    </div>
                  </div>
                  <span className="text-lg font-bold text-green-600">
                    {formatPercent(watch.roi)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Worst Performers */}
        {analytics.worst_performers.length > 0 && (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              Needs Attention
            </h3>
            <div className="space-y-3">
              {analytics.worst_performers.map((watch, index) => (
                <div
                  key={watch.watch_id}
                  className="flex items-center justify-between p-3 bg-red-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold text-red-600">#{index + 1}</span>
                    <div>
                      <p className="font-medium text-gray-900">
                        {watch.brand} {watch.model}
                      </p>
                      <p className="text-sm text-gray-600">
                        {formatCurrency(watch.current_value, analytics.currency)}
                      </p>
                    </div>
                  </div>
                  <span className="text-lg font-bold text-red-600">
                    {formatPercent(watch.roi)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {analytics.total_watches === 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
          <p className="text-blue-800">
            Add watches with purchase prices and market values to see collection analytics.
          </p>
        </div>
      )}
    </div>
  )
}

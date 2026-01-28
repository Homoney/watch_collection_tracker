import { useState } from 'react'
import AppLayout from '@/components/layout/AppLayout'
import CollectionAnalytics from '@/components/analytics/CollectionAnalytics'

const CURRENCIES = ['USD', 'EUR', 'GBP', 'CHF', 'JPY', 'AUD', 'CAD']

export default function AnalyticsPage() {
  const [selectedCurrency, setSelectedCurrency] = useState('USD')

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Collection Analytics</h1>
            <p className="mt-1 text-sm text-gray-600">
              Performance metrics and insights for your watch collection
            </p>
          </div>

          {/* Currency Selector */}
          <div className="flex items-center gap-2">
            <label htmlFor="currency" className="text-sm font-medium text-gray-700">
              Currency:
            </label>
            <select
              id="currency"
              value={selectedCurrency}
              onChange={(e) => setSelectedCurrency(e.target.value)}
              className="block rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
            >
              {CURRENCIES.map((currency) => (
                <option key={currency} value={currency}>
                  {currency}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Analytics Component */}
        <CollectionAnalytics currency={selectedCurrency} />
      </div>
    </AppLayout>
  )
}

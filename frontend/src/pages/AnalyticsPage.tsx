import { useState } from 'react'
import AppLayout from '@/components/layout/AppLayout'
import CollectionAnalytics from '@/components/analytics/CollectionAnalytics'
import PageHeader from '@/components/layout/PageHeader'

const CURRENCIES = ['USD', 'EUR', 'GBP', 'CHF', 'JPY', 'AUD', 'CAD']

export default function AnalyticsPage() {
  const [selectedCurrency, setSelectedCurrency] = useState('USD')

  return (
    <AppLayout>
      <div className="space-y-6">
        <PageHeader
          eyebrow="Collection"
          title="Analytics"
          description="How the collection's value has moved since purchase"
          actions={
            <label className="flex items-center gap-2 text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
              Currency
              <select
                value={selectedCurrency}
                onChange={(e) => setSelectedCurrency(e.target.value)}
                className="h-10 rounded-sm border border-input bg-card px-3 text-sm normal-case tracking-normal text-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
              >
                {CURRENCIES.map((currency) => (
                  <option key={currency} value={currency}>
                    {currency}
                  </option>
                ))}
              </select>
            </label>
          }
        />

        {/* Analytics Component */}
        <CollectionAnalytics currency={selectedCurrency} />
      </div>
    </AppLayout>
  )
}

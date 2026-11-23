import { Link } from 'react-router-dom'
import AppLayout from '@/components/layout/AppLayout'
import PageHeader from '@/components/layout/PageHeader'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'
import Spinner from '@/components/common/Spinner'
import { useWatches } from '@/hooks/useWatches'
import { useCollections } from '@/hooks/useCollections'
import { useCollectionAnalytics } from '@/hooks/useMarketValues'

export default function DashboardPage() {
  const { data: watchesData, isLoading: watchesLoading } = useWatches({}, 5, 0)
  const { data: collections, isLoading: collectionsLoading } = useCollections()
  // Totals cover every watch (not just the recent five listed below), in USD only
  const { data: analytics, isLoading: analyticsLoading } = useCollectionAnalytics('USD')

  const figLabel = 'text-[11px] uppercase tracking-[0.24em] text-muted-foreground'
  const returnPct = analytics && Number(analytics.total_purchase_price) > 0 ? ((Number(analytics.total_current_value) - Number(analytics.total_purchase_price)) / Number(analytics.total_purchase_price)) * 100 : null
  const formatPercent = (pct: number) => `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`

  const formatCurrency = (amount: number | string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(Number(amount))
  }

  return (
    <AppLayout>
      <div className="space-y-8">
        <PageHeader
          eyebrow="Watch Tracker"
          title="Dashboard"
          description="Welcome to your watch collection"
          actions={
            <>
              <Button variant="secondary" asChild>
                <Link to="/watches">View all watches</Link>
              </Button>
              <Button asChild>
                <Link to="/watches">Add new watch</Link>
              </Button>
            </>
          }
        />

        {/* Figures: one tray with hairline gaps */}
        <div className="grid grid-cols-2 gap-px border border-border bg-border md:grid-cols-4">
          <div className="bg-card p-5 sm:p-6">
            <p className={figLabel}>Watches</p>
            <p className="mt-2 text-3xl font-light text-foreground">{watchesLoading ? '-' : watchesData?.total || 0}</p>
          </div>
          <div className="col-span-2 bg-card p-5 sm:p-6 md:col-span-1">
            <p className={figLabel}>Current value</p>
            <p className="mt-2 text-3xl font-light text-foreground">
              {analyticsLoading || !analytics ? '-' : formatCurrency(analytics.total_current_value)}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Paid: {analyticsLoading || !analytics ? '-' : formatCurrency(analytics.total_purchase_price)}
            </p>
          </div>
          <div className="bg-card p-5 sm:p-6">
            <p className={figLabel}>Total return</p>
            <p className={`mt-2 text-3xl font-light ${returnPct === null ? 'text-foreground' : returnPct >= 0 ? 'text-positive' : 'text-negative'}`}>
              {returnPct === null ? '-' : formatPercent(returnPct)}
            </p>
          </div>
          <div className="bg-card p-5 sm:p-6">
            <p className={figLabel}>Collections</p>
            <p className="mt-2 text-3xl font-light text-foreground">{collectionsLoading ? '-' : collections?.length || 0}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className={figLabel}>Recent watches</h2>
              <Button variant="link" size="sm" asChild>
                <Link to="/watches">View all</Link>
              </Button>
            </div>

            {watchesLoading ? (
              <div className="flex justify-center py-8">
                <Spinner />
              </div>
            ) : watchesData?.items.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">No watches yet</p>
                <Button asChild>
                  <Link to="/watches">Add your first watch</Link>
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {watchesData?.items.map((watch) => (
                  <Link
                    key={watch.id}
                    to={`/watches/${watch.id}`}
                    className="block p-3 border border-border rounded-sm hover:bg-accent transition-colors"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-foreground">
                          {watch.brand?.name} {watch.model}
                        </p>
                        {watch.reference_number && (
                          <p className="text-sm text-muted-foreground">Ref: {watch.reference_number}</p>
                        )}
                      </div>
                      {watch.purchase_price && (
                        <p className="text-sm font-medium text-foreground">
                          {formatCurrency(Number(watch.purchase_price))}
                        </p>
                      )}
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </Card>

          <Card className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className={figLabel}>Collections</h2>
            </div>

            {collectionsLoading ? (
              <div className="flex justify-center py-8">
                <Spinner />
              </div>
            ) : collections?.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground">No collections yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {collections?.map((collection) => (
                  <Link
                    key={collection.id}
                    to={`/watches?collection_id=${collection.id}`}
                    className="block p-3 border border-border rounded-sm hover:bg-accent transition-colors"
                  >
                    <div className="flex justify-between items-center">
                      <div className="flex items-center space-x-3">
                        <div
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: collection.color }}
                        />
                        <p className="font-medium text-foreground">{collection.name}</p>
                      </div>
                      <p className="text-sm text-muted-foreground">{collection.watch_count} watches</p>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </Card>
        </div>

      </div>
    </AppLayout>
  )
}

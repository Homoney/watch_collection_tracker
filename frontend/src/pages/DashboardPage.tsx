import { Link } from 'react-router-dom'
import AppLayout from '@/components/layout/AppLayout'
import Card from '@/components/common/Card'
import Button from '@/components/common/Button'
import Spinner from '@/components/common/Spinner'
import { useWatches } from '@/hooks/useWatches'
import { useCollections } from '@/hooks/useCollections'

export default function DashboardPage() {
  const { data: watchesData, isLoading: watchesLoading } = useWatches({}, 5, 0)
  const { data: collections, isLoading: collectionsLoading } = useCollections()

  const totalValue =
    watchesData?.items.reduce((sum, watch) => {
      if (watch.purchase_price) {
        return sum + Number(watch.purchase_price)
      }
      return sum
    }, 0) || 0

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">Welcome to your watch collection</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Watches</p>
                <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                  {watchesLoading ? '-' : watchesData?.total || 0}
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <svg
                  className="w-8 h-8 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Value</p>
                <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                  {watchesLoading ? '-' : formatCurrency(totalValue)}
                </p>
              </div>
              <div className="p-3 bg-green-100 rounded-full">
                <svg
                  className="w-8 h-8 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Collections</p>
                <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
                  {collectionsLoading ? '-' : collections?.length || 0}
                </p>
              </div>
              <div className="p-3 bg-purple-100 rounded-full">
                <svg
                  className="w-8 h-8 text-purple-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                  />
                </svg>
              </div>
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Recent Watches</h2>
              <Link to="/watches">
                <Button variant="ghost" size="sm">
                  View All
                </Button>
              </Link>
            </div>

            {watchesLoading ? (
              <div className="flex justify-center py-8">
                <Spinner />
              </div>
            ) : watchesData?.items.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-600 dark:text-gray-400 mb-4">No watches yet</p>
                <Link to="/watches">
                  <Button>Add Your First Watch</Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {watchesData?.items.map((watch) => (
                  <Link
                    key={watch.id}
                    to={`/watches/${watch.id}`}
                    className="block p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">
                          {watch.brand?.name} {watch.model}
                        </p>
                        {watch.reference_number && (
                          <p className="text-sm text-gray-500">Ref: {watch.reference_number}</p>
                        )}
                      </div>
                      {watch.purchase_price && (
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
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
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Collections</h2>
            </div>

            {collectionsLoading ? (
              <div className="flex justify-center py-8">
                <Spinner />
              </div>
            ) : collections?.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-600 dark:text-gray-400">No collections yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {collections?.map((collection) => (
                  <Link
                    key={collection.id}
                    to={`/watches?collection_id=${collection.id}`}
                    className="block p-3 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    <div className="flex justify-between items-center">
                      <div className="flex items-center space-x-3">
                        <div
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: collection.color }}
                        />
                        <p className="font-medium text-gray-900 dark:text-white">{collection.name}</p>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{collection.watch_count} watches</p>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </Card>
        </div>

        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Link to="/watches">
              <Button className="w-full">View All Watches</Button>
            </Link>
            <Link to="/watches">
              <Button variant="secondary" className="w-full">
                Add New Watch
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    </AppLayout>
  )
}

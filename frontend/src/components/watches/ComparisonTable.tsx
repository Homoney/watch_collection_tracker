import { X } from 'lucide-react'
import type { Watch } from '@/types'
import { format } from 'date-fns'

interface ComparisonTableProps {
  watches: Watch[]
  onRemoveWatch: (id: string) => void
}

interface ComparisonRowProps {
  label: string
  values: any[]
  renderer?: (value: any, index: number) => React.ReactNode
}

function ComparisonRow({ label, values, renderer }: ComparisonRowProps) {
  return (
    <tr className="border-b border-gray-200 dark:border-gray-700">
      <td className="sticky left-0 bg-gray-50 dark:bg-gray-900 p-4 font-medium text-gray-900 dark:text-white">
        {label}
      </td>
      {values.map((value, idx) => (
        <td key={idx} className="p-4 text-center text-gray-700 dark:text-gray-300">
          {renderer ? (
            renderer(value, idx)
          ) : value !== null && value !== undefined && value !== '' ? (
            value
          ) : (
            <span className="text-gray-400 dark:text-gray-500 italic">N/A</span>
          )}
        </td>
      ))}
    </tr>
  )
}

function ComparisonSectionHeader({ title }: { title: string }) {
  return (
    <tr className="bg-gray-100 dark:bg-gray-800">
      <td colSpan={100} className="p-3 font-bold text-gray-900 dark:text-white">
        {title}
      </td>
    </tr>
  )
}

export default function ComparisonTable({ watches, onRemoveWatch }: ComparisonTableProps) {
  const formatCurrency = (amount: number | null, currency: string) => {
    if (amount === null || amount === undefined) return null
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
    }).format(amount)
  }

  const formatDate = (date: string | null) => {
    if (!date) return null
    try {
      return format(new Date(date), 'MMM d, yyyy')
    } catch {
      return null
    }
  }

  const calculateGainLoss = (watch: Watch) => {
    if (!watch.purchase_price || !watch.current_market_value) return null
    return watch.current_market_value - watch.purchase_price
  }

  const calculateROI = (watch: Watch) => {
    if (!watch.purchase_price || !watch.current_market_value) return null
    return ((watch.current_market_value - watch.purchase_price) / watch.purchase_price) * 100
  }

  return (
    <div className="overflow-x-auto bg-white dark:bg-gray-800 rounded-lg shadow">
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="border-b-2 border-gray-200 dark:border-gray-700">
            <th className="sticky left-0 bg-white dark:bg-gray-800 p-4"></th>
            {watches.map((watch) => (
              <th key={watch.id} className="p-4 relative min-w-[250px]">
                <button
                  onClick={() => onRemoveWatch(watch.id)}
                  className="absolute top-2 right-2 p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors"
                  title="Remove from comparison"
                >
                  <X className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                </button>
                <div className="text-left pr-8">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                    {watch.brand?.name || 'Unknown'}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{watch.model}</p>
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {/* Images */}
          <ComparisonRow
            label="Image"
            values={watches.map((w) => w.images?.[0]?.url || null)}
            renderer={(url) =>
              url ? (
                <img
                  src={url}
                  alt="Watch"
                  className="h-40 w-40 object-cover rounded-md mx-auto"
                />
              ) : (
                <div className="h-40 w-40 bg-gray-100 dark:bg-gray-700 rounded-md mx-auto flex items-center justify-center">
                  <svg
                    className="w-12 h-12 text-gray-400 dark:text-gray-500"
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
              )
            }
          />

          {/* Basic Information Section */}
          <ComparisonSectionHeader title="Basic Information" />
          <ComparisonRow label="Brand" values={watches.map((w) => w.brand?.name)} />
          <ComparisonRow label="Model" values={watches.map((w) => w.model)} />
          <ComparisonRow
            label="Reference Number"
            values={watches.map((w) => w.reference_number)}
          />
          <ComparisonRow label="Serial Number" values={watches.map((w) => w.serial_number)} />
          <ComparisonRow
            label="Collection"
            values={watches.map((w) => w.collection)}
            renderer={(collection) =>
              collection ? (
                <span
                  className="inline-flex items-center px-2 py-1 rounded text-xs font-medium"
                  style={{
                    backgroundColor: `${collection.color}20`,
                    color: collection.color,
                    borderColor: collection.color,
                    borderWidth: '1px',
                  }}
                >
                  {collection.name}
                </span>
              ) : null
            }
          />

          {/* Purchase Information Section */}
          <ComparisonSectionHeader title="Purchase Information" />
          <ComparisonRow
            label="Purchase Date"
            values={watches.map((w) => formatDate(w.purchase_date))}
          />
          <ComparisonRow
            label="Purchase Price"
            values={watches.map((w) => formatCurrency(w.purchase_price, w.purchase_currency))}
          />
          <ComparisonRow label="Retailer" values={watches.map((w) => w.retailer)} />
          <ComparisonRow label="Condition" values={watches.map((w) => w.condition)} />

          {/* Specifications Section */}
          <ComparisonSectionHeader title="Specifications" />
          <ComparisonRow
            label="Case Diameter"
            values={watches.map((w) => (w.case_diameter ? `${w.case_diameter} mm` : null))}
          />
          <ComparisonRow
            label="Case Thickness"
            values={watches.map((w) => (w.case_thickness ? `${w.case_thickness} mm` : null))}
          />
          <ComparisonRow
            label="Lug Width"
            values={watches.map((w) => (w.lug_width ? `${w.lug_width} mm` : null))}
          />
          <ComparisonRow
            label="Water Resistance"
            values={watches.map((w) => (w.water_resistance ? `${w.water_resistance} m` : null))}
          />
          <ComparisonRow
            label="Power Reserve"
            values={watches.map((w) => (w.power_reserve ? `${w.power_reserve} hours` : null))}
          />
          <ComparisonRow label="Case Material" values={watches.map((w) => w.case_material)} />
          <ComparisonRow label="Dial Color" values={watches.map((w) => w.dial_color)} />
          <ComparisonRow label="Strap Material" values={watches.map((w) => w.strap_material)} />

          {/* Movement Section */}
          <ComparisonSectionHeader title="Movement" />
          <ComparisonRow
            label="Movement Type"
            values={watches.map((w) => w.movement_type?.name)}
          />
          <ComparisonRow
            label="Complications"
            values={watches.map((w) =>
              w.complications?.length ? w.complications.map((c) => c.name).join(', ') : null
            )}
          />

          {/* Market Value Section */}
          <ComparisonSectionHeader title="Market Value" />
          <ComparisonRow
            label="Current Value"
            values={watches.map((w) =>
              formatCurrency(w.current_market_value, w.current_market_currency || w.purchase_currency)
            )}
          />
          <ComparisonRow
            label="Gain/Loss"
            values={watches.map((w) => calculateGainLoss(w))}
            renderer={(value) =>
              value !== null ? (
                <span
                  className={
                    value >= 0
                      ? 'text-green-600 dark:text-green-400 font-medium'
                      : 'text-red-600 dark:text-red-400 font-medium'
                  }
                >
                  {value >= 0 ? '+' : ''}
                  {formatCurrency(value, 'USD')}
                </span>
              ) : null
            }
          />
          <ComparisonRow
            label="ROI"
            values={watches.map((w) => calculateROI(w))}
            renderer={(value) =>
              value !== null ? (
                <span
                  className={
                    value >= 0
                      ? 'text-green-600 dark:text-green-400 font-medium'
                      : 'text-red-600 dark:text-red-400 font-medium'
                  }
                >
                  {value >= 0 ? '+' : ''}
                  {value.toFixed(2)}%
                </span>
              ) : null
            }
          />

          {/* Service History Section */}
          <ComparisonSectionHeader title="Service History" />
          <ComparisonRow
            label="Total Services"
            values={watches.map((w) => w.service_history?.length || 0)}
          />
          <ComparisonRow
            label="Last Service"
            values={watches.map((w) =>
              w.service_history?.length
                ? formatDate(w.service_history[0].service_date)
                : null
            )}
          />
          <ComparisonRow
            label="Next Service Due"
            values={watches.map((w) =>
              w.service_history?.length
                ? formatDate(w.service_history[0].next_service_due)
                : null
            )}
          />
        </tbody>
      </table>
    </div>
  )
}

import { X } from 'lucide-react'
import type { Watch } from '@/types'
import { format } from 'date-fns'

interface ComparisonTableProps {
  watches: Watch[]
  onRemoveWatch: (id: string) => void
}

interface ComparisonRowProps {
  label: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  values: any[]
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  renderer?: (value: any, index: number) => React.ReactNode
}

function ComparisonRow({ label, values, renderer }: ComparisonRowProps) {
  return (
    <tr className="border-b border-border">
      <td className="sticky left-0 bg-muted p-4 font-medium text-foreground">
        {label}
      </td>
      {values.map((value, idx) => (
        <td key={idx} className="p-4 text-center text-foreground">
          {renderer ? (
            renderer(value, idx)
          ) : value !== null && value !== undefined && value !== '' ? (
            value
          ) : (
            <span className="text-muted-foreground italic">N/A</span>
          )}
        </td>
      ))}
    </tr>
  )
}

function ComparisonSectionHeader({ title }: { title: string }) {
  return (
    <tr className="bg-muted">
      <td colSpan={100} className="p-3 font-bold text-foreground">
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
    <div className="overflow-x-auto bg-card rounded-sm shadow">
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="border-b-2 border-border">
            <th className="sticky left-0 bg-card p-4"></th>
            {watches.map((watch) => (
              <th key={watch.id} className="p-4 relative min-w-[250px]">
                <button
                  onClick={() => onRemoveWatch(watch.id)}
                  className="absolute top-2 right-2 p-1 hover:bg-accent rounded-full transition-colors"
                  title="Remove from comparison"
                >
                  <X className="h-4 w-4 text-muted-foreground" />
                </button>
                <div className="text-left pr-8">
                  <h3 className="text-lg font-light tracking-wide text-foreground">
                    {watch.brand?.name || 'Unknown'}
                  </h3>
                  <p className="text-sm text-muted-foreground">{watch.model}</p>
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
                  className="h-40 w-40 object-cover rounded-sm mx-auto"
                />
              ) : (
                <div className="h-40 w-40 bg-muted rounded-sm mx-auto flex items-center justify-center">
                  <svg
                    className="w-12 h-12 text-muted-foreground"
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
                  className="inline-flex items-center px-2 py-1 rounded text-xs font-medium dark:!text-gray-100"
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
          <ComparisonRow label="Caliber" values={watches.map((w) => w.caliber)} />
          <ComparisonRow label="Crystal" values={watches.map((w) => w.crystal)} />
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
              w.complications?.length ? w.complications.join(', ') : null
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
                      ? 'text-positive font-medium'
                      : 'text-negative font-medium'
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
                      ? 'text-positive font-medium'
                      : 'text-negative font-medium'
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

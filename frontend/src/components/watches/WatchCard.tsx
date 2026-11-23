import { memo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { MoreHorizontal, Pencil, Trash2 } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import { formatMoney, formatPercent, gainPercent } from '@/lib/money'
import WatchDial from './WatchDial'
import type { WatchListItem } from '@/types'

interface WatchCardProps {
  watch: WatchListItem
  isCompareMode?: boolean
  isSelected?: boolean
  onSelectionToggle?: (id: string) => void
  onEdit?: (watch: WatchListItem) => void
  onDelete?: (watch: WatchListItem) => void
}

/**
 * One watch in the collection grid (Collector's Vault): photo or drawn dial,
 * brand, model, then current value and gain since purchase. Delete lives in
 * the card's menu, not on the card face.
 */
const WatchCard = memo(function WatchCard({
  watch,
  isCompareMode = false,
  isSelected = false,
  onSelectionToggle,
  onEdit,
  onDelete,
}: WatchCardProps) {
  const navigate = useNavigate()
  const name = `${watch.brand?.name ?? 'Unknown Brand'} ${watch.model}`

  const hasValue = watch.current_market_value !== null && watch.current_market_value !== undefined
  const shownAmount = hasValue ? watch.current_market_value : watch.purchase_price
  const shownCurrency = (hasValue ? watch.current_market_currency : null) || watch.purchase_currency
  const gain = hasValue
    ? gainPercent(watch.current_market_value, watch.purchase_price, watch.current_market_currency, watch.purchase_currency)
    : null

  const open = useCallback(() => {
    if (isCompareMode) onSelectionToggle?.(watch.id)
    else navigate(`/watches/${watch.id}`)
  }, [isCompareMode, navigate, onSelectionToggle, watch.id])

  return (
    <article
      className={cn(
        'group relative flex h-full flex-col bg-card p-4 transition-colors hover:bg-accent sm:p-5',
        isSelected && 'bg-accent ring-2 ring-inset ring-ring'
      )}
    >
      {/* The whole card opens the watch; the name link is the accessible target */}
      <button
        type="button"
        onClick={open}
        className="absolute inset-0 z-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
        aria-label={isCompareMode ? `${isSelected ? 'Remove' : 'Add'} ${name} ${isSelected ? 'from' : 'to'} comparison` : `Open ${name}`}
        tabIndex={-1}
      />

      {isCompareMode && (
        <label className="absolute left-3 top-3 z-10 flex items-center">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onSelectionToggle?.(watch.id)}
            className="h-5 w-5 cursor-pointer rounded-sm border-input accent-[hsl(var(--gold))]"
            aria-label={`Compare ${name}`}
          />
        </label>
      )}

      {watch.collection && (
        <span className="absolute right-3 top-3 z-10 hidden max-w-[50%] truncate border border-border px-2 py-0.5 text-[10px] uppercase tracking-[0.16em] text-muted-foreground sm:block">
          {watch.collection.name}
        </span>
      )}

      <div className="pointer-events-none relative flex aspect-[4/3] items-center justify-center overflow-hidden">
        {watch.primary_image ? (
          <img
            src={watch.primary_image.url}
            alt={name}
            className="h-full w-full object-cover"
            loading="lazy"
            decoding="async"
          />
        ) : (
          <WatchDial accent={watch.collection?.color} className="h-24 w-24 sm:h-36 sm:w-36" />
        )}
      </div>

      <div className="pointer-events-none relative mt-3 flex flex-1 flex-col">
        <p className="truncate text-[10px] uppercase tracking-[0.28em] text-gold">{watch.brand?.name || 'Unknown Brand'}</p>
        <h3 className="mt-1 truncate text-[15px] font-normal text-foreground sm:text-[17px]">
          <a
            href={`/watches/${watch.id}`}
            onClick={(e) => {
              e.preventDefault()
              open()
            }}
            className="pointer-events-auto focus-visible:outline-none focus-visible:underline"
          >
            {watch.model}
          </a>
        </h3>
        {watch.reference_number && (
          <p className="truncate text-xs text-muted-foreground">Ref. {watch.reference_number}</p>
        )}

        <div className="min-h-3 flex-1" />
        <div className="flex items-baseline justify-between gap-2 border-t border-border pt-3">
          <div className="min-w-0">
            <span className="block truncate text-base text-foreground">{formatMoney(shownAmount, shownCurrency)}</span>
            {!hasValue && shownAmount !== null && shownAmount !== undefined && (
              <span className="text-[10px] uppercase tracking-[0.16em] text-muted-foreground">Paid</span>
            )}
          </div>
          {gain !== null && (
            <span
              className={cn('text-xs tabular-nums', gain >= 0 ? 'text-positive' : 'text-negative')}
              aria-label={`${gain >= 0 ? 'Gain' : 'Loss'} ${formatPercent(gain)} since purchase`}
            >
              {formatPercent(gain)}
            </span>
          )}
        </div>
      </div>

      {(onEdit || onDelete) && !isCompareMode && (
        <div className="absolute left-2 top-2 z-10">
          <DropdownMenu>
            <DropdownMenuTrigger
              aria-label={`Actions for ${name}`}
              className="inline-flex h-8 w-8 items-center justify-center rounded-sm text-muted-foreground opacity-100 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:opacity-0 sm:group-hover:opacity-100 sm:focus-visible:opacity-100 data-[state=open]:opacity-100"
            >
              <MoreHorizontal className="h-4 w-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              {onEdit && (
                <DropdownMenuItem onSelect={() => onEdit(watch)}>
                  <Pencil className="mr-2 h-4 w-4" /> Edit
                </DropdownMenuItem>
              )}
              {onEdit && onDelete && <DropdownMenuSeparator />}
              {onDelete && (
                <DropdownMenuItem onSelect={() => onDelete(watch)} className="text-destructive focus:text-destructive">
                  <Trash2 className="mr-2 h-4 w-4" /> Delete
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      )}
    </article>
  )
})

export default WatchCard

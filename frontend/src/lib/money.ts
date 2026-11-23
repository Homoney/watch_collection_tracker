/** Money helpers shared by the watch grid, cards and headers. */

export function formatMoney(amount: number | string | null | undefined, currency = 'USD', whole = true): string {
  if (amount === null || amount === undefined || amount === '') return '—'
  const n = Number(amount)
  if (!Number.isFinite(n)) return '—'
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      maximumFractionDigits: whole ? 0 : 2,
      minimumFractionDigits: whole ? 0 : 2,
    }).format(n)
  } catch {
    // unknown currency code
    return `${n.toLocaleString('en-US')} ${currency}`
  }
}

/** Percentage gain from paid to value, or null when it cannot be compared. */
export function gainPercent(
  value: number | string | null | undefined,
  paid: number | string | null | undefined,
  valueCurrency?: string | null,
  paidCurrency?: string | null
): number | null {
  if (value === null || value === undefined || paid === null || paid === undefined) return null
  if (valueCurrency && paidCurrency && valueCurrency !== paidCurrency) return null
  const v = Number(value)
  const p = Number(paid)
  if (!Number.isFinite(v) || !Number.isFinite(p) || p <= 0) return null
  return ((v - p) / p) * 100
}

export function formatPercent(pct: number): string {
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%`
}

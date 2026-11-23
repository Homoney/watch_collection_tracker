import { useState } from 'react'
import { Search, ExternalLink } from 'lucide-react'
import Button from '@/components/common/Button'
import { specLookupApi } from '@/lib/api'
import type { SpecLookupResult, SpecSource } from '@/types'

interface ReferenceLookupProps {
  /** Current form values the look-up needs */
  getContext: () => { reference: string; brand_id?: string; caliber?: string }
  /** Put the answer into the form's empty fields */
  onResult: (result: SpecLookupResult) => void
}

function ExtLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-0.5 text-gold underline underline-offset-2 hover:opacity-80"
    >
      {children}
      <ExternalLink className="h-3 w-3" aria-hidden="true" />
    </a>
  )
}

/** "From WatchBase" under a field the look-up filled */
export function SourceNote({ source }: { source?: SpecSource }) {
  if (!source) return null
  return (
    <p className="mt-1 text-xs text-muted-foreground">
      Filled from <ExtLink href={source.url}>{source.name}</ExtLink>
    </p>
  )
}

export default function ReferenceLookup({ getContext, onResult }: ReferenceLookupProps) {
  const [result, setResult] = useState<SpecLookupResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = async (watchbaseId?: number) => {
    const { reference, brand_id, caliber } = getContext()
    if (!reference || reference.trim().length < 2) {
      setError('Type a reference number first.')
      return
    }
    setIsLoading(true)
    setError(null)
    try {
      const answer = await specLookupApi.lookup({
        reference: reference.trim(),
        brand_id: brand_id || undefined,
        caliber: caliber || undefined,
        watchbase_id: watchbaseId,
      })
      setResult(answer)
      onResult(answer)
    } catch (err: unknown) {
      const e = err as { response?: { status?: number } }
      setError(
        e.response?.status === 429
          ? 'Too many look-ups in a row. Wait a minute and try again.'
          : 'The look-up did not work. Try again later.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  const movement = result?.movement
  const movementFacts = movement
    ? [
        movement.caliber && `cal. ${movement.caliber}`,
        movement.jewels && `${movement.jewels} jewels`,
        movement.frequency,
        movement.power_reserve && `${movement.power_reserve} h power reserve`,
      ].filter(Boolean)
    : []

  // display: contents, so the form can put the button beside the reference
  // field and the result on the row below (it spans the full width)
  return (
    <div className="contents">
      <Button
        type="button"
        variant="secondary"
        onClick={() => run()}
        disabled={isLoading}
        className="h-10 self-end whitespace-nowrap"
        title="Fill empty fields from the reference number"
      >
        <Search className="h-4 w-4" aria-hidden="true" />
        {isLoading ? 'Looking up...' : 'Look up'}
      </Button>

      {(error || result) && (
        <div
          role="status"
          className="col-span-full space-y-2 rounded-sm border border-border bg-muted p-3 text-sm"
        >
          <p className="text-foreground">{error || result?.message}</p>

          {result?.status === 'choices' && (
            <ul className="space-y-1">
              {result.choices.map((c) => (
                <li key={c.id}>
                  <button
                    type="button"
                    onClick={() => run(c.id)}
                    disabled={isLoading}
                    className="w-full rounded-sm border border-input px-2 py-1 text-left text-foreground hover:bg-card"
                  >
                    <span className="font-medium">{c.reference}</span>
                    {' · '}
                    {c.name}
                    <span className="text-muted-foreground">
                      {' '}
                      ({[c.brand, c.family].filter(Boolean).join(', ')})
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}

          {movementFacts.length > 0 && (
            <p className="text-muted-foreground">
              Movement: {movementFacts.join(' · ')}
              {movement?.source && (
                <>
                  {' '}
                  (source: <ExtLink href={movement.source.url}>{movement.source.name}</ExtLink>)
                </>
              )}
            </p>
          )}

          {result && result.links.length > 0 && (
            <p className="text-muted-foreground">
              Look it up yourself:{' '}
              {result.links.map((link, i) => (
                <span key={link.url}>
                  {i > 0 && ' · '}
                  <ExtLink href={link.url}>{link.label}</ExtLink>
                </span>
              ))}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

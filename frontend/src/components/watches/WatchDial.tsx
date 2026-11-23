/**
 * Drawn dial used when a watch has no photo. The bezel takes the collection
 * colour (if any) so cards without photos still differ from one another.
 */
interface WatchDialProps {
  accent?: string | null
  className?: string
}

export default function WatchDial({ accent, className = 'h-36 w-36' }: WatchDialProps) {
  const ticks = Array.from({ length: 12 }, (_, i) => i * 30)
  return (
    <svg viewBox="0 0 120 120" className={className} aria-hidden="true" focusable="false">
      <rect x="45" y="2" width="30" height="20" rx="3" className="fill-muted" />
      <rect x="45" y="98" width="30" height="20" rx="3" className="fill-muted" />
      <circle cx="60" cy="60" r="42" className="fill-muted-foreground/40" style={accent ? { fill: accent, opacity: 0.75 } : undefined} />
      <circle cx="60" cy="60" r="36" className="fill-background" />
      {ticks.map((deg) => (
        <line
          key={deg}
          x1="60"
          y1={deg % 90 === 0 ? 27 : 28}
          x2="60"
          y2={deg % 90 === 0 ? 34 : 31}
          transform={`rotate(${deg} 60 60)`}
          className="stroke-muted-foreground"
          strokeWidth={deg % 90 === 0 ? 2 : 1}
        />
      ))}
      <line x1="60" y1="60" x2="60" y2="38" transform="rotate(-35 60 60)" className="stroke-foreground" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="60" y1="60" x2="60" y2="31" transform="rotate(62 60 60)" className="stroke-foreground" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="60" y1="64" x2="60" y2="30" transform="rotate(155 60 60)" className="stroke-gold" strokeWidth="0.9" />
      <circle cx="60" cy="60" r="2" className="fill-gold" />
    </svg>
  )
}

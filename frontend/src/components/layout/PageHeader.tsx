import { ReactNode } from 'react'

interface PageHeaderProps {
  eyebrow?: string
  title: string
  description?: ReactNode
  /** Buttons or figures shown on the right (below the title on phones) */
  actions?: ReactNode
}

/** The one page heading used across screens (Collector's Vault). */
export default function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div className="min-w-0">
        {eyebrow && <p className="mb-2 text-[11px] uppercase tracking-[0.3em] text-gold">{eyebrow}</p>}
        <h1 className="text-3xl font-light tracking-wide text-foreground sm:text-4xl">{title}</h1>
        {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  )
}

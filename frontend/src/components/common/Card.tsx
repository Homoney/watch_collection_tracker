import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface CardProps {
  children: ReactNode
  className?: string
  onClick?: () => void
}

/** A panel: card surface with a hairline border, no shadow (Collector's Vault). */
export default function Card({ children, className = '', onClick }: CardProps) {
  return (
    <div
      className={cn(
        'bg-card text-card-foreground border border-border rounded-sm',
        onClick && 'cursor-pointer hover:bg-accent transition-colors',
        className
      )}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
    >
      {children}
    </div>
  )
}

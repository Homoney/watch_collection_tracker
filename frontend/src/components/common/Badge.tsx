import type { ConditionEnum } from '@/types'

interface BadgeProps {
  condition: ConditionEnum
}

const conditionColors = {
  mint: 'bg-green-100 text-green-800 border-green-200',
  excellent: 'bg-blue-100 text-blue-800 border-blue-200',
  good: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  fair: 'bg-orange-100 text-orange-800 border-orange-200',
  poor: 'bg-red-100 text-red-800 border-red-200',
}

const conditionLabels = {
  mint: 'Mint',
  excellent: 'Excellent',
  good: 'Good',
  fair: 'Fair',
  poor: 'Poor',
}

export default function Badge({ condition }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${conditionColors[condition]}`}
    >
      {conditionLabels[condition]}
    </span>
  )
}

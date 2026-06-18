import { clsx } from 'clsx'

type Variant = 'success' | 'warning' | 'error' | 'default' | 'accent'

interface Props {
  children: React.ReactNode
  variant?: Variant
  className?: string
}

const variants: Record<Variant, string> = {
  success: 'bg-success/10 text-success border-success/20',
  warning: 'bg-warning/10 text-warning border-warning/20',
  error: 'bg-error/10 text-error border-error/20',
  accent: 'bg-accent/10 text-accent border-accent/20',
  default: 'bg-elevated text-secondary border-border',
}

export default function Badge({ children, variant = 'default', className }: Props) {
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
        variants[variant],
        className,
      )}
    >
      {children}
    </span>
  )
}

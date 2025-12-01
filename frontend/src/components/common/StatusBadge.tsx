import { cn } from '../../utils/helpers'

interface StatusBadgeProps {
  status: 'online' | 'warning' | 'offline' | 'pending'
  label?: string
  pulse?: boolean
}

export default function StatusBadge({ status, label, pulse = true }: StatusBadgeProps) {
  const colors = {
    online: 'bg-green-500',
    warning: 'bg-yellow-500',
    offline: 'bg-red-500',
    pending: 'bg-slate-500',
  }

  return (
    <div className="flex items-center gap-2">
      <span className="relative flex h-3 w-3">
        {pulse && status !== 'offline' && (
          <span className={cn(
            "animate-ping absolute inline-flex h-full w-full rounded-full opacity-75",
            colors[status]
          )} />
        )}
        <span className={cn(
          "relative inline-flex rounded-full h-3 w-3",
          colors[status]
        )} />
      </span>
      {label && (
        <span className="text-sm text-slate-400">{label}</span>
      )}
    </div>
  )
}

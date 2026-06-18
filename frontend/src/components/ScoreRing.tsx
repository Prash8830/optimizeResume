interface Props {
  score: number
  size?: number
}

export default function ScoreRing({ score, size = 120 }: Props) {
  const pct = Math.round(score * 100)
  const r = 46
  const circ = 2 * Math.PI * r
  const offset = circ - (pct / 100) * circ
  const color = pct >= 80 ? '#10b981' : pct >= 65 ? '#f59e0b' : '#ef4444'

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox="0 0 100 100" className="-rotate-90">
        <circle cx="50" cy="50" r={r} fill="none" stroke="#1e1f2e" strokeWidth="8" />
        <circle
          cx="50"
          cy="50"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-2xl font-black" style={{ color }}>
          {pct}%
        </div>
        <div className="text-xs text-muted -mt-0.5">ATS</div>
      </div>
    </div>
  )
}

import { Check, Loader2, Circle } from 'lucide-react'
import { clsx } from 'clsx'

const NODES = [
  { id: 'jd_analyzer', label: 'Analyzing JD', desc: 'Extracting keywords & requirements' },
  { id: 'profile_scorer', label: 'Scoring Profile', desc: 'Semantic matching against your profile' },
  { id: 'content_selector', label: 'Selecting Content', desc: 'Picking the best-fit experience' },
  { id: 'resume_writer', label: 'Writing Resume', desc: 'Crafting tailored content' },
  { id: 'ats_checker', label: 'ATS Validation', desc: 'Checking keyword coverage' },
  { id: 'report_generator', label: 'Generating Report', desc: 'Building optimization report' },
]

type NodeStatus = 'waiting' | 'active' | 'done'

interface Props {
  nodeStates: Record<string, NodeStatus>
  atsScore?: number
}

export default function PipelineProgress({ nodeStates, atsScore }: Props) {
  return (
    <div className="space-y-2">
      {NODES.map((node) => {
        const status = nodeStates[node.id] ?? 'waiting'
        return (
          <div
            key={node.id}
            className={clsx(
              'flex items-center gap-3 px-4 py-3 rounded-xl border transition-all',
              status === 'done' && 'bg-success/5 border-success/20',
              status === 'active' && 'bg-accent/5 border-accent/20',
              status === 'waiting' && 'bg-elevated border-border opacity-50',
            )}
          >
            <div className="flex-shrink-0">
              {status === 'done' && <Check size={16} className="text-success" />}
              {status === 'active' && <Loader2 size={16} className="text-accent animate-spin" />}
              {status === 'waiting' && <Circle size={16} className="text-muted" />}
            </div>
            <div className="flex-1 min-w-0">
              <div
                className={clsx(
                  'text-sm font-medium',
                  status === 'done'
                    ? 'text-success'
                    : status === 'active'
                      ? 'text-primary'
                      : 'text-muted',
                )}
              >
                {node.label}
              </div>
              <div className="text-xs text-muted truncate">{node.desc}</div>
            </div>
            {node.id === 'ats_checker' && status === 'done' && atsScore !== undefined && (
              <span className="text-xs font-bold text-success">{Math.round(atsScore * 100)}%</span>
            )}
          </div>
        )
      })}
    </div>
  )
}

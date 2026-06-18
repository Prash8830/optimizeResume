import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { FileText, FileDown, Clock, Sparkles } from 'lucide-react'
import { api } from '../lib/api'
import Badge from '../components/ui/Badge'
import type { ResumeVersion } from '../types'

export default function History() {
  const navigate = useNavigate()

  const { data: versions, isLoading, error } = useQuery<ResumeVersion[]>({
    queryKey: ['versions'],
    queryFn: () => api.listVersions(),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-secondary text-sm">Loading history...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <p className="text-error text-sm">
          {error instanceof Error ? error.message : 'Failed to load history'}
        </p>
      </div>
    )
  }

  const sorted = [...(versions ?? [])].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
  )

  if (sorted.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <Clock size={48} className="text-muted mb-4" />
        <h2 className="text-xl font-bold text-primary mb-2">No resumes yet</h2>
        <p className="text-secondary text-sm mb-6">
          Generate your first tailored resume to see it here.
        </p>
        <button onClick={() => navigate('/generate')} className="btn-primary flex items-center gap-2">
          <Sparkles size={16} />
          Generate Resume
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-primary">History</h1>
        <p className="text-secondary text-sm mt-1">{sorted.length} resume{sorted.length !== 1 ? 's' : ''} generated</p>
      </div>

      <div className="space-y-3">
        {sorted.map((v) => {
          const score = v.ats_score
          const scoreVariant = score >= 0.8 ? 'success' : score >= 0.65 ? 'warning' : 'error'
          const date = new Date(v.created_at).toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
          })

          return (
            <div
              key={v.id}
              onClick={() => navigate(`/results/${v.id}`)}
              className="card p-5 flex items-center gap-4 cursor-pointer hover:border-accent/30 transition-colors group"
            >
              <div className="w-10 h-10 bg-elevated border border-border rounded-xl flex items-center justify-center flex-shrink-0 group-hover:border-accent/30 transition-colors">
                <FileText size={18} className="text-secondary" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-bold text-primary text-sm truncate">
                    {v.role_title || 'Untitled Role'}
                  </span>
                  {v.company && (
                    <span className="text-secondary text-xs">@ {v.company}</span>
                  )}
                </div>
                <div className="flex items-center gap-2 text-xs text-muted">
                  <Clock size={11} />
                  {date}
                  {v.optimization_report?.word_count && (
                    <>
                      <span>·</span>
                      <span>{v.optimization_report.word_count} words</span>
                    </>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Badge variant={scoreVariant}>{Math.round(score * 100)}% ATS</Badge>

                <a
                  href={api.getPdfUrl(v.id)}
                  download
                  onClick={(e) => e.stopPropagation()}
                  className="btn-ghost p-2 rounded-lg"
                  title="Download PDF"
                >
                  <FileDown size={15} />
                </a>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

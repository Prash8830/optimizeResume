import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { FileText, BarChart2, Download, ArrowLeft, FileDown, AlertCircle, Calendar, Hash, RefreshCw, type LucideProps } from 'lucide-react'
import type { ForwardRefExoticComponent, RefAttributes } from 'react'
import { api } from '../lib/api'
import ScoreRing from '../components/ScoreRing'
import ResumePreview from '../components/ResumePreview'
import Badge from '../components/ui/Badge'
import type { ResumeVersion } from '../types'
import { clsx } from 'clsx'

type Tab = 'resume' | 'analysis' | 'download'
type LucideIcon = ForwardRefExoticComponent<Omit<LucideProps, 'ref'> & RefAttributes<SVGSVGElement>>

export default function Results() {
  const { versionId } = useParams<{ versionId: string }>()
  const [activeTab, setActiveTab] = useState<Tab>('resume')

  const { data: version, isLoading, error } = useQuery<ResumeVersion>({
    queryKey: ['version', versionId],
    queryFn: () => api.getVersion(versionId!),
    enabled: !!versionId,
  })

  if (!versionId) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <FileText size={48} className="text-muted mb-4" />
        <h2 className="text-xl font-bold text-primary mb-2">No resume generated yet</h2>
        <p className="text-secondary text-sm mb-6">
          Generate a tailored resume from a job description to see results here.
        </p>
        <Link to="/generate" className="btn-primary">
          Generate Resume
        </Link>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-secondary text-sm">Loading results...</p>
        </div>
      </div>
    )
  }

  if (error || !version) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <AlertCircle size={48} className="text-error mb-4" />
        <h2 className="text-xl font-bold text-primary mb-2">Could not load results</h2>
        <p className="text-secondary text-sm mb-6">
          {error instanceof Error ? error.message : 'Unknown error'}
        </p>
        <Link to="/history" className="btn-secondary">
          Back to History
        </Link>
      </div>
    )
  }

  const report = version.optimization_report
  const score = version.ats_score
  const scoreVariant = score >= 0.8 ? 'success' : score >= 0.65 ? 'warning' : 'error'
  const createdAt = new Date(version.created_at).toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })

  const TABS: Array<{ id: Tab; label: string; icon: LucideIcon }> = [
    { id: 'resume', label: 'Resume', icon: FileText },
    { id: 'analysis', label: 'Analysis', icon: BarChart2 },
    { id: 'download', label: 'Download', icon: Download },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Link to="/history" className="btn-ghost p-2 mt-1">
          <ArrowLeft size={16} />
        </Link>
        <div className="flex-1">
          <div className="flex items-center gap-4">
            <ScoreRing score={score} size={100} />
            <div>
              <h1 className="text-2xl font-black text-primary">
                {version.role_title || 'Resume'}
                {version.company && (
                  <span className="text-secondary font-normal"> @ {version.company}</span>
                )}
              </h1>
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                <Badge variant={scoreVariant}>{Math.round(score * 100)}% ATS</Badge>
                {report?.word_count && (
                  <Badge variant="default">
                    <Hash size={10} className="mr-1" />
                    {report.word_count} words
                  </Badge>
                )}
                {report?.iteration_count && (
                  <Badge variant="default">
                    <RefreshCw size={10} className="mr-1" />
                    {report.iteration_count} iterations
                  </Badge>
                )}
                <Badge variant="default">
                  <Calendar size={10} className="mr-1" />
                  {createdAt}
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-elevated border border-border rounded-xl p-1 w-fit">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
              activeTab === id
                ? 'bg-surface text-primary shadow-sm border border-border'
                : 'text-secondary hover:text-primary',
            )}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'resume' && (
        <ResumePreview text={version.resume_text} />
      )}

      {activeTab === 'analysis' && (
        <div className="space-y-6">
          {report?.required_keyword_coverage && (
            <>
              <div className="card p-6">
                <h3 className="text-sm font-bold text-primary mb-4">
                  Keyword Coverage —{' '}
                  <span className="text-success">
                    {Math.round(report.required_keyword_coverage.coverage * 100)}%
                  </span>
                </h3>
                <div className="space-y-4">
                  <div>
                    <p className="section-title">Matched keywords</p>
                    <div className="flex flex-wrap gap-2">
                      {report.required_keyword_coverage.matched.map((kw) => (
                        <span
                          key={kw}
                          className="bg-success/10 text-success border border-success/20 text-xs px-2.5 py-1 rounded-full font-medium"
                        >
                          {kw}
                        </span>
                      ))}
                      {report.required_keyword_coverage.matched.length === 0 && (
                        <span className="text-xs text-muted">None matched</span>
                      )}
                    </div>
                  </div>
                  <div>
                    <p className="section-title">Missing keywords</p>
                    <div className="flex flex-wrap gap-2">
                      {report.required_keyword_coverage.missing.map((kw) => (
                        <span
                          key={kw}
                          className="bg-error/10 text-error border border-error/20 text-xs px-2.5 py-1 rounded-full font-medium"
                        >
                          {kw}
                        </span>
                      ))}
                      {report.required_keyword_coverage.missing.length === 0 && (
                        <span className="text-xs text-success">All keywords matched!</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {report.gap_skills && report.gap_skills.length > 0 && (
                <div className="card p-6">
                  <h3 className="text-sm font-bold text-primary mb-3">Gap Skills to Develop</h3>
                  <div className="flex flex-wrap gap-2">
                    {report.gap_skills.map((skill) => (
                      <span
                        key={skill}
                        className="bg-warning/10 text-warning border border-warning/20 text-xs px-2.5 py-1 rounded-full font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'download' && (
        <div className="grid grid-cols-2 gap-4">
          <a
            href={api.getPdfUrl(version.id)}
            download
            className="card p-8 flex flex-col items-center text-center hover:border-accent/40 transition-colors group"
          >
            <FileDown size={32} className="text-accent mb-4 group-hover:scale-110 transition-transform" />
            <h3 className="text-lg font-bold text-primary mb-2">Download PDF</h3>
            <p className="text-xs text-secondary leading-relaxed mb-4">
              Standard PDF format. Best for emailing directly to recruiters or uploading to ATS
              portals.
            </p>
            <span className="btn-primary text-sm">Download PDF</span>
          </a>

          <a
            href={api.getDocxUrl(version.id)}
            download
            className="card p-8 flex flex-col items-center text-center hover:border-accent/40 transition-colors group"
          >
            <FileDown size={32} className="text-secondary mb-4 group-hover:scale-110 transition-transform" />
            <h3 className="text-lg font-bold text-primary mb-2">Download DOCX</h3>
            <p className="text-xs text-secondary leading-relaxed mb-4">
              Word document format. Easy to edit further in Microsoft Word or Google Docs before
              sending.
            </p>
            <span className="btn-secondary text-sm">Download DOCX</span>
          </a>
        </div>
      )}
    </div>
  )
}

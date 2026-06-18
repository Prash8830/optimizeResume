import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Briefcase, ExternalLink, Plus, Trash2, FileText,
  Sparkles, X, ChevronRight, Check,
} from 'lucide-react'
import { clsx } from 'clsx'
import { api } from '../lib/api'
import type { JobApplication, JobStatus } from '../types'

// ── Company Directory ──────────────────────────────────────────────────────

const COMPANIES = [
  {
    name: 'Google',
    url: 'https://careers.google.com/jobs/results/?category=SOFTWARE_ENGINEERING&category=DATA_CENTER_OPERATIONS&category=HARDWARE_ENGINEERING&category=INFORMATION_TECHNOLOGY',
    color: '#4285F4',
    bg: 'rgba(66,133,244,0.08)',
    border: 'rgba(66,133,244,0.2)',
    roles: 'Software Engineer · AI/ML Engineer · Research Scientist',
  },
  {
    name: 'Amazon',
    url: 'https://www.amazon.jobs/en/search?base_query=machine+learning+engineer&loc_query=India',
    color: '#FF9900',
    bg: 'rgba(255,153,0,0.08)',
    border: 'rgba(255,153,0,0.2)',
    roles: 'Applied Scientist · SDE · ML Engineer',
  },
  {
    name: 'Mastercard',
    url: 'https://careers.mastercard.com/us/en/search-results?keywords=AI+machine+learning',
    color: '#EB001B',
    bg: 'rgba(235,0,27,0.08)',
    border: 'rgba(235,0,27,0.2)',
    roles: 'AI Engineer · Data Scientist · Software Engineer',
  },
  {
    name: 'JPMorgan Chase',
    url: 'https://careers.jpmorgan.com/us/en/home#jobs?search=artificial+intelligence&tags=location--India',
    color: '#003087',
    bg: 'rgba(0,48,135,0.08)',
    border: 'rgba(0,48,135,0.2)',
    roles: 'AI/ML Engineer · Quant Researcher · Software Engineer',
  },
  {
    name: 'Amex',
    url: 'https://aexp.eightfold.ai/careers?query=machine+learning&location=India',
    color: '#016FD0',
    bg: 'rgba(1,111,208,0.08)',
    border: 'rgba(1,111,208,0.2)',
    roles: 'ML Engineer · Data Engineer · Software Engineer',
  },
]

// ── Status config ──────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<JobStatus, { label: string; color: string; bg: string; border: string }> = {
  bookmarked: { label: 'Bookmarked', color: '#8a8eb8', bg: 'rgba(138,142,184,0.1)', border: 'rgba(138,142,184,0.2)' },
  applied:    { label: 'Applied',    color: '#3b82f6', bg: 'rgba(59,130,246,0.1)',  border: 'rgba(59,130,246,0.2)' },
  interview:  { label: 'Interview',  color: '#f59e0b', bg: 'rgba(245,158,11,0.1)',  border: 'rgba(245,158,11,0.2)' },
  offer:      { label: 'Offer',      color: '#10b981', bg: 'rgba(16,185,129,0.1)',  border: 'rgba(16,185,129,0.2)' },
  rejected:   { label: 'Rejected',   color: '#e05252', bg: 'rgba(224,82,82,0.1)',   border: 'rgba(224,82,82,0.2)' },
}

const STATUS_ORDER: JobStatus[] = ['bookmarked', 'applied', 'interview', 'offer', 'rejected']

function StatusBadge({ status }: { status: JobStatus }) {
  const c = STATUS_CONFIG[status]
  return (
    <span
      className="text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider"
      style={{ color: c.color, background: c.bg, border: `1px solid ${c.border}` }}
    >
      {c.label}
    </span>
  )
}

// ── Add Job Modal ──────────────────────────────────────────────────────────

function AddJobModal({ onClose, prefillCompany = '' }: { onClose: () => void; prefillCompany?: string }) {
  const queryClient = useQueryClient()
  const [company, setCompany] = useState(prefillCompany)
  const [roleTitle, setRoleTitle] = useState('')
  const [jobUrl, setJobUrl] = useState('')
  const [jdText, setJdText] = useState('')
  const [notes, setNotes] = useState('')
  const [generateNow, setGenerateNow] = useState(true)

  const navigate = useNavigate()

  const mutation = useMutation({
    mutationFn: () =>
      api.createJob({
        company,
        role_title: roleTitle,
        job_url: jobUrl || undefined,
        jd_text: jdText || undefined,
        notes: notes || undefined,
        status: 'bookmarked',
      }),
    onSuccess: (job) => {
      void queryClient.invalidateQueries({ queryKey: ['jobs'] })
      onClose()
      if (generateNow && jdText) {
        navigate('/generate', {
          state: { jd: jdText, company, role: roleTitle, jobId: job.id },
        })
      }
    },
  })

  const valid = company.trim() && roleTitle.trim()

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-surface border border-border rounded-2xl w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="text-sm font-bold text-primary">Track a Job</h2>
          <button onClick={onClose} className="btn-ghost p-1.5 rounded-lg"><X size={16} /></button>
        </div>

        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-secondary mb-1.5">Company *</label>
              <input value={company} onChange={e => setCompany(e.target.value)} className="input w-full" placeholder="Google" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-secondary mb-1.5">Role Title *</label>
              <input value={roleTitle} onChange={e => setRoleTitle(e.target.value)} className="input w-full" placeholder="AI Engineer" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-secondary mb-1.5">Job URL</label>
            <input value={jobUrl} onChange={e => setJobUrl(e.target.value)} className="input w-full" placeholder="https://careers.google.com/jobs/..." />
          </div>

          <div>
            <label className="block text-xs font-semibold text-secondary mb-1.5">Job Description (paste here)</label>
            <textarea
              value={jdText}
              onChange={e => setJdText(e.target.value)}
              className="input w-full resize-none"
              rows={5}
              placeholder="Paste the full job description to generate a tailored resume…"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-secondary mb-1.5">Notes</label>
            <input value={notes} onChange={e => setNotes(e.target.value)} className="input w-full" placeholder="Referral from John, apply before July 15…" />
          </div>

          {jdText && (
            <label className="flex items-center gap-2.5 cursor-pointer select-none">
              <div
                onClick={() => setGenerateNow(!generateNow)}
                className={clsx(
                  'w-4 h-4 rounded flex items-center justify-center flex-shrink-0 border transition-colors',
                  generateNow ? 'bg-accent border-accent' : 'bg-transparent border-border',
                )}
              >
                {generateNow && <Check size={10} className="text-white" />}
              </div>
              <span className="text-xs text-secondary">Generate tailored resume immediately after saving</span>
            </label>
          )}
        </div>

        <div className="px-6 pb-6 flex gap-3">
          <button onClick={onClose} className="btn-secondary flex-1">Cancel</button>
          <button
            onClick={() => mutation.mutate()}
            disabled={!valid || mutation.isPending}
            className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {mutation.isPending ? 'Saving…' : (
              <>
                {generateNow && jdText ? <><Sparkles size={14} />Save & Generate</> : <><Plus size={14} />Save Job</>}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Job Card ───────────────────────────────────────────────────────────────

function JobCard({ job }: { job: JobApplication }) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [showStatusMenu, setShowStatusMenu] = useState(false)

  const updateMutation = useMutation({
    mutationFn: (status: JobStatus) => api.updateJob(job.id, { status }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['jobs'] })
      setShowStatusMenu(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => api.deleteJob(job.id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  })

  const company = COMPANIES.find(c => c.name.toLowerCase() === job.company.toLowerCase())
  const accentColor = company?.color ?? '#e05252'

  return (
    <div className="card p-4 space-y-3 hover:border-accent/20 transition-colors relative">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <p className="text-sm font-bold text-primary truncate">{job.role_title}</p>
          <p className="text-xs font-semibold mt-0.5" style={{ color: accentColor }}>{job.company}</p>
        </div>
        <StatusBadge status={job.status} />
      </div>

      {/* Notes */}
      {job.notes && (
        <p className="text-xs text-muted leading-relaxed line-clamp-2">{job.notes}</p>
      )}

      {/* Applied date */}
      {job.applied_at && (
        <p className="text-[10px] text-muted">
          Applied {new Date(job.applied_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
        </p>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 pt-1 border-t border-border/50">
        {job.job_url && (
          <a
            href={job.job_url}
            target="_blank"
            rel="noreferrer"
            className="btn-ghost py-1 px-2 text-xs flex items-center gap-1 rounded-lg"
          >
            <ExternalLink size={11} />
            Open Job
          </a>
        )}

        {job.resume_version_id ? (
          <button
            onClick={() => navigate(`/results/${job.resume_version_id}`)}
            className="btn-ghost py-1 px-2 text-xs flex items-center gap-1 rounded-lg"
          >
            <FileText size={11} />
            Resume
          </button>
        ) : job.jd_text ? (
          <button
            onClick={() => navigate('/generate', { state: { jd: job.jd_text, company: job.company, role: job.role_title, jobId: job.id } })}
            className="btn-ghost py-1 px-2 text-xs flex items-center gap-1 rounded-lg text-accent"
          >
            <Sparkles size={11} />
            Generate
          </button>
        ) : null}

        <div className="ml-auto flex items-center gap-1">
          <div className="relative">
            <button
              onClick={() => setShowStatusMenu(!showStatusMenu)}
              className="btn-ghost py-1 px-2 text-xs flex items-center gap-1 rounded-lg"
            >
              Status <ChevronRight size={10} />
            </button>
            {showStatusMenu && (
              <div className="absolute right-0 bottom-full mb-1 bg-surface border border-border rounded-xl shadow-xl z-10 overflow-hidden min-w-[130px]">
                {STATUS_ORDER.map(s => (
                  <button
                    key={s}
                    onClick={() => updateMutation.mutate(s)}
                    className={clsx(
                      'w-full text-left px-3 py-2 text-xs hover:bg-elevated transition-colors flex items-center gap-2',
                      job.status === s && 'bg-elevated',
                    )}
                  >
                    <span
                      className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                      style={{ background: STATUS_CONFIG[s].color }}
                    />
                    {STATUS_CONFIG[s].label}
                  </button>
                ))}
              </div>
            )}
          </div>

          <button
            onClick={() => deleteMutation.mutate()}
            className="btn-ghost py-1 px-1.5 rounded-lg text-error/60 hover:text-error"
          >
            <Trash2 size={12} />
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function Jobs() {
  const [showModal, setShowModal] = useState(false)
  const [prefillCompany, setPrefillCompany] = useState('')

  const { data: jobs = [], isLoading } = useQuery<JobApplication[]>({
    queryKey: ['jobs'],
    queryFn: () => api.listJobs(),
  })

  const byStatus = STATUS_ORDER.reduce<Record<string, JobApplication[]>>((acc, s) => {
    acc[s] = jobs.filter(j => j.status === s)
    return acc
  }, {})

  const openModal = (company = '') => {
    setPrefillCompany(company)
    setShowModal(true)
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-primary">Job Tracker</h1>
          <p className="text-secondary text-sm mt-1">
            {jobs.length} tracked · {byStatus.applied?.length ?? 0} applied · {byStatus.interview?.length ?? 0} interviews
          </p>
        </div>
        <button onClick={() => openModal()} className="btn-primary flex items-center gap-2">
          <Plus size={16} />
          Track Job
        </button>
      </div>

      {/* Company Directory */}
      <div>
        <p className="section-title mb-3">Career Portals</p>
        <div className="grid grid-cols-5 gap-3">
          {COMPANIES.map(company => (
            <div
              key={company.name}
              className="card p-4 flex flex-col gap-3"
              style={{ borderColor: company.border, background: company.bg }}
            >
              <div>
                <p className="text-sm font-black" style={{ color: company.color }}>{company.name}</p>
                <p className="text-[10px] text-muted mt-0.5 leading-relaxed">{company.roles}</p>
              </div>
              <div className="flex gap-2 mt-auto">
                <a
                  href={company.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-lg transition-colors"
                  style={{ color: company.color, background: `${company.color}15` }}
                >
                  <ExternalLink size={10} />
                  Open Jobs
                </a>
                <button
                  onClick={() => openModal(company.name)}
                  className="flex items-center gap-1 text-[10px] font-semibold px-2 py-1 rounded-lg bg-elevated border border-border text-secondary hover:text-primary transition-colors"
                >
                  <Plus size={10} />
                  Track
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Kanban tracker */}
      {isLoading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
        </div>
      ) : jobs.length === 0 ? (
        <div className="card p-12 flex flex-col items-center text-center">
          <Briefcase size={40} className="text-muted mb-4" />
          <h3 className="text-lg font-bold text-primary mb-2">No jobs tracked yet</h3>
          <p className="text-secondary text-sm mb-6 max-w-sm">
            Browse the career portals above and paste a JD to generate a tailored resume for each role.
          </p>
          <button onClick={() => openModal()} className="btn-primary flex items-center gap-2">
            <Plus size={16} />
            Track First Job
          </button>
        </div>
      ) : (
        <div>
          <p className="section-title mb-3">Pipeline</p>
          <div className="grid grid-cols-5 gap-4">
            {STATUS_ORDER.map(status => {
              const cfg = STATUS_CONFIG[status]
              const cols = byStatus[status] ?? []
              return (
                <div key={status} className="space-y-2">
                  {/* Column header */}
                  <div className="flex items-center justify-between px-1">
                    <span
                      className="text-xs font-bold uppercase tracking-wider"
                      style={{ color: cfg.color }}
                    >
                      {cfg.label}
                    </span>
                    <span
                      className="text-[10px] font-bold px-1.5 py-0.5 rounded-full min-w-[20px] text-center"
                      style={{ background: cfg.bg, color: cfg.color }}
                    >
                      {cols.length}
                    </span>
                  </div>

                  {/* Cards */}
                  <div className="space-y-2 min-h-[100px]">
                    {cols.map(job => <JobCard key={job.id} job={job} />)}
                    {cols.length === 0 && (
                      <div
                        className="border border-dashed rounded-xl p-4 text-center text-xs text-muted"
                        style={{ borderColor: cfg.border }}
                      >
                        No jobs
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {showModal && (
        <AddJobModal
          onClose={() => setShowModal(false)}
          prefillCompany={prefillCompany}
        />
      )}
    </div>
  )
}

import { Link } from 'react-router-dom'
import { Sparkles, Zap, Target, ArrowRight, CheckCircle } from 'lucide-react'

const PIPELINE_NODES = [
  { name: 'JD Analyzer', desc: 'Extracts must-have keywords and requirements from the job post' },
  { name: 'Profile Scorer', desc: 'Semantically matches your experience against the JD' },
  { name: 'Content Selector', desc: 'Picks the highest-scoring projects and roles for this job' },
  { name: 'Resume Writer', desc: 'Writes tailored bullet points aligned to the role' },
  { name: 'ATS Checker', desc: 'Validates keyword coverage and scores the draft' },
  { name: 'Report Generator', desc: 'Builds a gap analysis and optimization report' },
]

const STEPS = [
  {
    num: '01',
    title: 'Build your master profile',
    desc: 'Chat with our AI consultant to capture your full experience — roles, projects, skills, education.',
  },
  {
    num: '02',
    title: 'Paste the job description',
    desc: 'Drop in any JD. Our pipeline analyzes requirements and selects the best content from your profile.',
  },
  {
    num: '03',
    title: 'Download your tailored resume',
    desc: 'Get a one-page resume optimized for ATS, plus a gap analysis report. Export as PDF or DOCX.',
  },
]

export default function Landing() {
  return (
    <div className="space-y-12">
      {/* Hero */}
      <div className="relative rounded-3xl border border-border bg-gradient-to-br from-surface via-elevated to-surface p-10 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-accent/5 via-transparent to-transparent pointer-events-none" />
        <div className="relative">
          <div className="inline-flex items-center gap-2 bg-accent/10 border border-accent/20 rounded-full px-4 py-1.5 mb-6">
            <Sparkles size={12} className="text-accent" />
            <span className="text-xs font-semibold text-accent">6-node LangGraph pipeline</span>
          </div>
          <h1 className="text-4xl font-black text-primary mb-4 leading-tight max-w-2xl">
            Tailor your resume to any job —{' '}
            <span className="text-accent">in seconds.</span>
          </h1>
          <p className="text-secondary text-lg max-w-xl mb-8 leading-relaxed">
            AI reads the job description, selects your best experience, writes tailored bullets, and
            validates ATS coverage. One page. Ready to send.
          </p>
          <div className="flex items-center gap-4">
            <Link to="/profile" className="btn-primary flex items-center gap-2">
              Build Profile
              <ArrowRight size={16} />
            </Link>
            <Link to="/generate" className="btn-secondary flex items-center gap-2">
              <Sparkles size={16} />
              Generate Resume
            </Link>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'ATS scores', value: '82%+', sub: 'average coverage', icon: Target },
          { label: 'Generation time', value: '<10s', sub: 'end-to-end pipeline', icon: Zap },
          { label: 'Pipeline nodes', value: '6', sub: 'specialized AI agents', icon: Sparkles },
        ].map(({ label, value, sub, icon: Icon }) => (
          <div key={label} className="card p-6">
            <Icon size={20} className="text-accent mb-3" />
            <div className="text-3xl font-black text-primary mb-1">{value}</div>
            <div className="text-sm font-semibold text-secondary">{label}</div>
            <div className="text-xs text-muted mt-0.5">{sub}</div>
          </div>
        ))}
      </div>

      {/* How it works */}
      <div>
        <p className="section-title">How it works</p>
        <div className="grid grid-cols-3 gap-4">
          {STEPS.map((step) => (
            <div key={step.num} className="card p-6">
              <div className="text-3xl font-black text-accent/30 mb-3">{step.num}</div>
              <div className="text-sm font-bold text-primary mb-2">{step.title}</div>
              <div className="text-xs text-secondary leading-relaxed">{step.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Pipeline nodes */}
      <div>
        <p className="section-title">The pipeline</p>
        <div className="card divide-y divide-border">
          {PIPELINE_NODES.map((node, idx) => (
            <div key={node.name} className="flex items-center gap-4 px-6 py-4">
              <div className="w-6 h-6 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center flex-shrink-0">
                <span className="text-[10px] font-bold text-accent">{idx + 1}</span>
              </div>
              <div className="flex-1">
                <span className="text-sm font-semibold text-primary">{node.name}</span>
                <span className="text-xs text-muted ml-3">{node.desc}</span>
              </div>
              <CheckCircle size={14} className="text-success/40" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

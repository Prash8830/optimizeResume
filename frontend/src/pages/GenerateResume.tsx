import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sparkles, Lightbulb, AlertCircle } from 'lucide-react'
import { streamGenerate } from '../lib/api'
import PipelineProgress from '../components/PipelineProgress'

type NodeStatus = 'waiting' | 'active' | 'done'

export default function GenerateResume() {
  const navigate = useNavigate()
  const [company, setCompany] = useState('')
  const [roleTitle, setRoleTitle] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [nodeStates, setNodeStates] = useState<Record<string, NodeStatus>>({})
  const [atsScore, setAtsScore] = useState<number | undefined>()
  const [error, setError] = useState<string | null>(null)

  const handleGenerate = useCallback(() => {
    if (!jobDescription.trim() || isGenerating) return
    setError(null)
    setNodeStates({})
    setAtsScore(undefined)
    setIsGenerating(true)

    const cancel = streamGenerate(
      { job_description: jobDescription, company, role_title: roleTitle },
      (event) => {
        const type = event.type as string
        const node = event.node as string | undefined
        const status = event.status as string | undefined

        if (type === 'progress' && node) {
          setNodeStates((prev) => ({
            ...prev,
            [node]: status === 'started' ? 'active' : status === 'done' ? 'done' : prev[node] ?? 'waiting',
          }))
        }
        if (type === 'progress' && event.ats_score !== undefined) {
          setAtsScore(event.ats_score as number)
        }
        if (type === 'complete') {
          const versionId = event.resume_version_id as string | undefined
          setIsGenerating(false)
          if (versionId) {
            navigate(`/results/${versionId}`)
          }
        }
      },
      () => {
        setIsGenerating(false)
      },
      (err) => {
        setError(err.message)
        setIsGenerating(false)
      },
    )

    return cancel
  }, [company, roleTitle, jobDescription, isGenerating, navigate])

  const canGenerate = jobDescription.trim().length > 50

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-primary">Generate Resume</h1>
        <p className="text-secondary text-sm mt-1">
          Paste a job description and our 6-node pipeline will tailor your resume.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Form */}
        <div className="space-y-5">
          <div className="card p-6 space-y-4">
            <div>
              <label className="label">Company</label>
              <input
                type="text"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                placeholder="e.g. Google, Atlassian, Microsoft"
                className="input"
              />
            </div>
            <div>
              <label className="label">Role Title</label>
              <input
                type="text"
                value={roleTitle}
                onChange={(e) => setRoleTitle(e.target.value)}
                placeholder="e.g. Software Engineer, AI Engineer"
                className="input"
              />
            </div>
            <div>
              <label className="label">Job Description *</label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the full job description here..."
                rows={14}
                className="input resize-none"
              />
              <p className="text-xs text-muted mt-1">{jobDescription.length} chars · minimum 50</p>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-error text-sm bg-error/5 border border-error/20 rounded-xl px-4 py-3">
                <AlertCircle size={16} />
                {error}
              </div>
            )}

            <button
              onClick={handleGenerate}
              disabled={!canGenerate || isGenerating}
              className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Sparkles size={16} />
              {isGenerating ? 'Generating...' : 'Generate Resume'}
            </button>
          </div>

          {/* Tip card */}
          <div className="card p-5 flex gap-3">
            <Lightbulb size={16} className="text-warning flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-primary mb-1">How the pipeline works</p>
              <p className="text-xs text-secondary leading-relaxed">
                The AI analyzes your JD for must-have keywords, scores your profile content
                semantically, selects the highest-value experience, writes ATS-optimized bullets,
                then validates coverage before generating a gap analysis report.
              </p>
            </div>
          </div>
        </div>

        {/* Pipeline progress */}
        <div>
          <div className="card p-6">
            <h2 className="text-sm font-bold text-primary mb-4">Pipeline Progress</h2>
            <PipelineProgress nodeStates={nodeStates} atsScore={atsScore} />
            {!isGenerating && Object.keys(nodeStates).length === 0 && (
              <p className="text-xs text-muted mt-4 text-center">
                Progress will appear here once you start generating.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

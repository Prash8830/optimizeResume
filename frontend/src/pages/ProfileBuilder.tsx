import React, { useEffect, useRef, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Send, Upload, User, Bot, CheckCircle, Loader2,
  Briefcase, Code2, GraduationCap, ChevronDown, ChevronUp, PencilLine,
} from 'lucide-react'
import { api } from '../lib/api'
import type { ChatMessage } from '../types'

interface SavedProfile {
  profile: {
    name: string; email: string; phone: string;
    linkedin: string; github: string; summary: string;
  }
  experiences: Array<{ company: string; role: string; start_date: string; end_date: string; bullets: string[] }>
  projects: Array<{ title: string; description: string; tech_stack: string[]; outcomes: string[] }>
  skills: Array<{ name: string; category: string; proficiency: string }>
  education: Array<{ degree: string; institution: string; year: string }>
}

function Section({ title, icon: Icon, children }: {
  title: string; icon: React.ElementType; children: React.ReactNode
}) {
  const [open, setOpen] = useState(true)
  return (
    <div className="border border-border rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-elevated hover:bg-elevated/80 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon size={14} className="text-accent" />
          <span className="text-xs font-bold text-primary uppercase tracking-wider">{title}</span>
        </div>
        {open ? <ChevronUp size={14} className="text-muted" /> : <ChevronDown size={14} className="text-muted" />}
      </button>
      {open && <div className="p-4 space-y-3">{children}</div>}
    </div>
  )
}

export default function ProfileBuilder() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isChatLoading, setIsChatLoading] = useState(false)
  const [resumeContext, setResumeContext] = useState('')
  const [profileComplete, setProfileComplete] = useState(false)
  const [extractedProfile, setExtractedProfile] = useState<Record<string, unknown> | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [showChat, setShowChat] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Load existing profile
  const { data: savedProfile, isLoading: profileLoading } = useQuery<SavedProfile>({
    queryKey: ['profile'],
    queryFn: () => api.getProfile() as unknown as Promise<SavedProfile>,
    retry: false,
  })

  const hasProfile = !!savedProfile?.profile?.name

  // Start chat when showChat is activated (only once)
  useEffect(() => {
    if (!showChat || messages.length > 0) return
    setIsChatLoading(true)
    api
      .chat([], '')
      .then((res) => setMessages([{ role: 'assistant', content: res.reply }]))
      .catch(console.error)
      .finally(() => setIsChatLoading(false))
  }, [showChat, messages.length])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = useCallback(async () => {
    const text = input.trim()
    if (!text || isChatLoading) return
    const newMessages: ChatMessage[] = [...messages, { role: 'user', content: text }]
    setMessages(newMessages)
    setInput('')
    setIsChatLoading(true)
    try {
      const res = await api.chat(newMessages, resumeContext)
      setMessages((prev) => [...prev, { role: 'assistant', content: res.reply }])
      if (res.profile_complete && !profileComplete) {
        setProfileComplete(true)
        const profile = await api.extractProfile([
          ...newMessages,
          { role: 'assistant', content: res.reply },
        ])
        setExtractedProfile(profile)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setIsChatLoading(false)
    }
  }, [input, messages, resumeContext, isChatLoading, profileComplete])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void sendMessage()
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => setResumeContext((ev.target?.result as string).slice(0, 5000))
    reader.readAsText(file)
  }

  const handleSaveProfile = async () => {
    if (!extractedProfile) return
    setIsSaving(true)
    try {
      await api.saveProfile(extractedProfile)
      setSaveSuccess(true)
      void queryClient.invalidateQueries({ queryKey: ['profile'] })
      setTimeout(() => { setShowChat(false); setSaveSuccess(false) }, 1500)
    } catch (err) {
      console.error(err)
    } finally {
      setIsSaving(false)
    }
  }

  const groupedSkills = (savedProfile?.skills ?? []).reduce<Record<string, string[]>>((acc, s) => {
    const cat = s.category || 'Other'
    acc[cat] = [...(acc[cat] ?? []), s.name]
    return acc
  }, {})

  if (profileLoading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-secondary text-sm">Loading profile…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-black text-primary">
            {hasProfile ? `${savedProfile.profile.name}` : 'Build Your Profile'}
          </h1>
          <p className="text-secondary text-sm mt-1">
            {hasProfile
              ? `${savedProfile.experiences.length} experiences · ${savedProfile.projects.length} projects · ${savedProfile.skills.length} skills`
              : 'Chat with the AI consultant to capture your complete professional story.'}
          </p>
        </div>
        <div className="flex gap-2">
          {hasProfile && (
            <button onClick={() => navigate('/generate')} className="btn-primary flex items-center gap-2">
              <Send size={14} />
              Generate Resume
            </button>
          )}
          <button
            onClick={() => setShowChat(!showChat)}
            className="btn-secondary flex items-center gap-2"
          >
            <PencilLine size={14} />
            {hasProfile ? (showChat ? 'View Profile' : 'Update via Chat') : 'Start Chat'}
          </button>
        </div>
      </div>

      {/* Chat mode */}
      {showChat && (
        <div className="grid grid-cols-5 gap-6 h-[calc(100vh-250px)]">
          <div className="col-span-3 card flex flex-col overflow-hidden">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
                    msg.role === 'user' ? 'bg-accent/20' : 'bg-elevated border border-border'}`}>
                    {msg.role === 'user'
                      ? <User size={14} className="text-accent" />
                      : <Bot size={14} className="text-secondary" />}
                  </div>
                  <div className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-accent text-white rounded-tr-sm'
                      : 'bg-elevated text-primary border border-border rounded-tl-sm'}`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {isChatLoading && (
                <div className="flex gap-3">
                  <div className="w-7 h-7 rounded-full bg-elevated border border-border flex items-center justify-center">
                    <Bot size={14} className="text-secondary" />
                  </div>
                  <div className="bg-elevated border border-border px-4 py-3 rounded-2xl rounded-tl-sm">
                    <Loader2 size={14} className="text-muted animate-spin" />
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>
            {resumeContext && (
              <div className="px-4 py-2 bg-success/5 border-t border-success/20 text-xs text-success flex items-center gap-2">
                <CheckCircle size={12} />
                Resume uploaded ({resumeContext.length} chars)
              </div>
            )}
            <div className="p-4 border-t border-border">
              <div className="flex gap-2">
                <button onClick={() => fileInputRef.current?.click()} className="btn-ghost p-2.5 rounded-xl flex-shrink-0" title="Upload resume">
                  <Upload size={16} />
                </button>
                <input ref={fileInputRef} type="file" accept=".txt,.md,.pdf" className="hidden" onChange={handleFileUpload} />
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Type your answer…"
                  rows={2}
                  className="input resize-none flex-1"
                />
                <button
                  onClick={() => void sendMessage()}
                  disabled={!input.trim() || isChatLoading}
                  className="btn-primary px-3 flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send size={16} />
                </button>
              </div>
            </div>
          </div>

          {/* Extracted profile panel */}
          <div className="col-span-2 card flex flex-col overflow-hidden">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <h2 className="text-sm font-bold text-primary">Extracted Profile</h2>
              {profileComplete && (
                <span className="inline-flex items-center gap-1.5 text-xs text-success">
                  <CheckCircle size={12} /> Complete
                </span>
              )}
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {extractedProfile ? (
                <pre className="text-xs text-secondary font-mono whitespace-pre-wrap break-words leading-relaxed">
                  {JSON.stringify(extractedProfile, null, 2)}
                </pre>
              ) : (
                <div className="h-full flex items-center justify-center text-center">
                  <div>
                    <User size={32} className="text-muted mx-auto mb-3" />
                    <p className="text-sm text-muted">Profile will appear when conversation is complete</p>
                  </div>
                </div>
              )}
            </div>
            {extractedProfile && (
              <div className="p-4 border-t border-border">
                <button
                  onClick={() => void handleSaveProfile()}
                  disabled={isSaving || saveSuccess}
                  className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {isSaving ? <><Loader2 size={16} className="animate-spin" />Saving…</>
                    : saveSuccess ? <><CheckCircle size={16} />Saved!</>
                    : 'Save & Update Profile'}
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Profile view mode */}
      {!showChat && hasProfile && (
        <div className="grid grid-cols-3 gap-6">
          {/* Left column: contact + summary */}
          <div className="space-y-4">
            <div className="card p-5">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center flex-shrink-0">
                  <User size={22} className="text-accent" />
                </div>
                <div>
                  <p className="font-black text-primary">{savedProfile.profile.name}</p>
                  <p className="text-xs text-muted">{savedProfile.experiences[0]?.role ?? 'Engineer'}</p>
                </div>
              </div>
              <div className="space-y-1.5 text-xs text-secondary">
                {savedProfile.profile.email && <p>{savedProfile.profile.email}</p>}
                {savedProfile.profile.phone && <p>{savedProfile.profile.phone}</p>}
                {savedProfile.profile.linkedin && (
                  <a href={savedProfile.profile.linkedin} target="_blank" rel="noreferrer" className="text-accent hover:underline block truncate">
                    LinkedIn
                  </a>
                )}
                {savedProfile.profile.github && (
                  <a href={savedProfile.profile.github} target="_blank" rel="noreferrer" className="text-accent hover:underline block truncate">
                    GitHub
                  </a>
                )}
              </div>
            </div>

            {savedProfile.profile.summary && (
              <div className="card p-4">
                <p className="text-xs font-bold text-primary uppercase tracking-wider mb-2">Summary</p>
                <p className="text-xs text-secondary leading-relaxed">{savedProfile.profile.summary}</p>
              </div>
            )}

            {/* Education */}
            {savedProfile.education.length > 0 && (
              <Section title="Education" icon={GraduationCap}>
                {savedProfile.education.map((ed, i) => (
                  <div key={i}>
                    <p className="text-xs font-bold text-primary">{ed.degree}</p>
                    <p className="text-xs text-secondary">{ed.institution}</p>
                    {ed.year && <p className="text-xs text-muted">{ed.year}</p>}
                  </div>
                ))}
              </Section>
            )}
          </div>

          {/* Middle column: experience + skills */}
          <div className="space-y-4">
            {savedProfile.experiences.length > 0 && (
              <Section title="Experience" icon={Briefcase}>
                {savedProfile.experiences.map((ex, i) => (
                  <div key={i} className="space-y-2">
                    <div>
                      <p className="text-xs font-bold text-primary">{ex.role}</p>
                      <p className="text-xs text-accent">{ex.company}</p>
                      <p className="text-xs text-muted">{ex.start_date} – {ex.end_date}</p>
                    </div>
                    <ul className="space-y-1">
                      {ex.bullets.slice(0, 5).map((b, j) => (
                        <li key={j} className="text-xs text-secondary leading-relaxed flex gap-2">
                          <span className="text-accent/60 flex-shrink-0 mt-0.5">·</span>
                          <span>{b}</span>
                        </li>
                      ))}
                      {ex.bullets.length > 5 && (
                        <li className="text-xs text-muted italic">+{ex.bullets.length - 5} more bullets</li>
                      )}
                    </ul>
                  </div>
                ))}
              </Section>
            )}

            {Object.keys(groupedSkills).length > 0 && (
              <Section title="Skills" icon={Code2}>
                {Object.entries(groupedSkills).map(([cat, skills]) => (
                  <div key={cat}>
                    <p className="text-[10px] font-bold text-muted uppercase tracking-wider mb-1.5">{cat}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {skills.map((s) => (
                        <span key={s} className="bg-elevated border border-border text-xs text-secondary px-2 py-0.5 rounded-full">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </Section>
            )}
          </div>

          {/* Right column: projects */}
          <div className="space-y-4">
            {savedProfile.projects.length > 0 && (
              <Section title={`Projects (${savedProfile.projects.length})`} icon={Code2}>
                {savedProfile.projects.map((p, i) => (
                  <div key={i} className="border-b border-border/50 pb-3 last:border-0 last:pb-0">
                    <p className="text-xs font-bold text-primary mb-1">{p.title}</p>
                    {p.description && (
                      <p className="text-xs text-secondary leading-relaxed mb-1.5 line-clamp-2">{p.description}</p>
                    )}
                    {p.tech_stack?.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {p.tech_stack.slice(0, 4).map((t) => (
                          <span key={t} className="bg-accent/10 text-accent text-[10px] px-1.5 py-0.5 rounded font-medium">
                            {t}
                          </span>
                        ))}
                        {p.tech_stack.length > 4 && (
                          <span className="text-[10px] text-muted">+{p.tech_stack.length - 4}</span>
                        )}
                      </div>
                    )}
                    {p.outcomes?.length > 0 && (
                      <p className="text-[10px] text-success mt-1">{p.outcomes[0]}</p>
                    )}
                  </div>
                ))}
              </Section>
            )}
          </div>
        </div>
      )}

      {/* No profile yet — show prompt */}
      {!showChat && !hasProfile && (
        <div className="flex flex-col items-center justify-center h-[50vh] text-center">
          <User size={48} className="text-muted mb-4" />
          <h2 className="text-xl font-bold text-primary mb-2">No profile yet</h2>
          <p className="text-secondary text-sm mb-6">Chat with the AI consultant to build your master profile.</p>
          <button onClick={() => setShowChat(true)} className="btn-primary flex items-center gap-2">
            <PencilLine size={16} /> Start Building
          </button>
        </div>
      )}
    </div>
  )
}

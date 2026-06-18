import React, { useEffect, useRef, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Send, Upload, User, Bot, CheckCircle, Loader2 } from 'lucide-react'
import { api } from '../lib/api'
import type { ChatMessage } from '../types'

export default function ProfileBuilder() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [resumeContext, setResumeContext] = useState('')
  const [profileComplete, setProfileComplete] = useState(false)
  const [extractedProfile, setExtractedProfile] = useState<Record<string, unknown> | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Get opening message on mount
  useEffect(() => {
    setIsLoading(true)
    api
      .chat([], '')
      .then((res) => {
        setMessages([{ role: 'assistant', content: res.reply }])
      })
      .catch(console.error)
      .finally(() => setIsLoading(false))
  }, [])

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = useCallback(async () => {
    const text = input.trim()
    if (!text || isLoading) return

    const newMessages: ChatMessage[] = [...messages, { role: 'user', content: text }]
    setMessages(newMessages)
    setInput('')
    setIsLoading(true)

    try {
      const res = await api.chat(newMessages, resumeContext)
      setMessages((prev) => [...prev, { role: 'assistant', content: res.reply }])
      if (res.profile_complete && !profileComplete) {
        setProfileComplete(true)
        // Auto-extract
        const profile = await api.extractProfile([
          ...newMessages,
          { role: 'assistant', content: res.reply },
        ])
        setExtractedProfile(profile)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }, [input, messages, resumeContext, isLoading, profileComplete])

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
    reader.onload = (ev) => {
      const text = ev.target?.result as string
      setResumeContext(text.slice(0, 5000))
    }
    reader.readAsText(file)
  }

  const handleSaveProfile = async () => {
    if (!extractedProfile) return
    setIsSaving(true)
    try {
      await api.saveProfile(extractedProfile)
      setSaveSuccess(true)
      setTimeout(() => navigate('/generate'), 1500)
    } catch (err) {
      console.error(err)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-black text-primary">Build Your Profile</h1>
        <p className="text-secondary text-sm mt-1">
          Chat with the AI consultant to capture your complete professional story.
        </p>
      </div>

      <div className="grid grid-cols-5 gap-6 h-[calc(100vh-220px)]">
        {/* Chat panel */}
        <div className="col-span-3 card flex flex-col overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
                    msg.role === 'user' ? 'bg-accent/20' : 'bg-elevated border border-border'
                  }`}
                >
                  {msg.role === 'user' ? (
                    <User size={14} className="text-accent" />
                  ) : (
                    <Bot size={14} className="text-secondary" />
                  )}
                </div>
                <div
                  className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-accent text-white rounded-tr-sm'
                      : 'bg-elevated text-primary border border-border rounded-tl-sm'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isLoading && (
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

          {/* File upload strip */}
          {resumeContext && (
            <div className="px-4 py-2 bg-success/5 border-t border-success/20 text-xs text-success flex items-center gap-2">
              <CheckCircle size={12} />
              Resume uploaded as context ({resumeContext.length} chars)
            </div>
          )}

          {/* Input area */}
          <div className="p-4 border-t border-border">
            <div className="flex gap-2">
              <button
                onClick={() => fileInputRef.current?.click()}
                className="btn-ghost p-2.5 rounded-xl flex-shrink-0"
                title="Upload resume for context"
              >
                <Upload size={16} />
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.md,.pdf"
                className="hidden"
                onChange={handleFileUpload}
              />
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your answer..."
                rows={2}
                className="input resize-none flex-1"
              />
              <button
                onClick={() => void sendMessage()}
                disabled={!input.trim() || isLoading}
                className="btn-primary px-3 flex-shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* Profile preview panel */}
        <div className="col-span-2 card flex flex-col overflow-hidden">
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-primary">Extracted Profile</h2>
              {profileComplete && (
                <span className="inline-flex items-center gap-1.5 text-xs text-success">
                  <CheckCircle size={12} />
                  Complete
                </span>
              )}
            </div>
            {!profileComplete && (
              <p className="text-xs text-muted mt-1">
                Profile will appear here once the conversation is complete.
              </p>
            )}
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {extractedProfile ? (
              <pre className="text-xs text-secondary font-mono whitespace-pre-wrap break-words leading-relaxed">
                {JSON.stringify(extractedProfile, null, 2)}
              </pre>
            ) : (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <User size={32} className="text-muted mx-auto mb-3" />
                  <p className="text-sm text-muted">No profile yet</p>
                  <p className="text-xs text-muted/60 mt-1">
                    Answer the consultant's questions to build your profile
                  </p>
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
                {isSaving ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Saving...
                  </>
                ) : saveSuccess ? (
                  <>
                    <CheckCircle size={16} />
                    Saved! Redirecting...
                  </>
                ) : (
                  'Save Profile & Continue'
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

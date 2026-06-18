import type { AdminStats, ResumeVersion, LLMLog } from '../types'

const BASE = '/api'

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  // Profile
  getProfile: () => req<Record<string, unknown>>('/profile/'),
  saveProfile: (data: unknown) =>
    req<{ message: string; profile_id: string }>('/profile/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  chat: (messages: Array<{ role: string; content: string }>, resume_context = '') =>
    req<{ reply: string; profile_complete: boolean }>('/profile/chat', {
      method: 'POST',
      body: JSON.stringify({ messages, resume_context }),
    }),
  extractProfile: (messages: Array<{ role: string; content: string }>) =>
    req<Record<string, unknown>>('/profile/extract', {
      method: 'POST',
      body: JSON.stringify({ messages }),
    }),

  // Resume
  listVersions: () => req<ResumeVersion[]>('/resume/versions'),
  getVersion: (id: string) => req<ResumeVersion>(`/resume/versions/${id}`),

  // Export
  getPdfUrl: (id: string) => `${BASE}/export/pdf/${id}`,
  getDocxUrl: (id: string) => `${BASE}/export/docx/${id}`,

  // Admin
  getAdminStats: () => req<AdminStats>('/admin/stats'),
}

export function streamGenerate(
  body: { job_description: string; company: string; role_title: string },
  onEvent: (e: Record<string, unknown>) => void,
  onDone: () => void,
  onError: (e: Error) => void,
): () => void {
  const controller = new AbortController()

  fetch(`${BASE}/resume/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify(body),
    signal: controller.signal,
  })
    .then(async (res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6)) as Record<string, unknown>
              onEvent(data)
            } catch {
              // ignore parse errors
            }
          }
        }
      }
      onDone()
    })
    .catch((e: unknown) => {
      if (e instanceof Error && e.name !== 'AbortError') onError(e)
    })

  return () => controller.abort()
}

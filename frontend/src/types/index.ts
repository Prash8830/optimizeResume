export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ResumeVersion {
  id: string;
  user_id: string;
  company: string;
  role_title: string;
  job_description: string;
  resume_text: string;
  ats_score: number;
  optimization_report: OptimizationReport;
  created_at: string;
}

export interface OptimizationReport {
  word_count: number;
  iteration_count: number;
  required_keyword_coverage: {
    matched: string[];
    missing: string[];
    coverage: number;
  };
  gap_skills: string[];
  swappable_items: Array<{ content: string; score: number }>;
}

export interface PipelineEvent {
  type: 'progress' | 'complete';
  node?: string;
  status?: 'started' | 'done';
  ats_score?: number;
  iteration?: number;
  resume_version_id?: string;
  optimization_report?: OptimizationReport;
}

export type JobStatus = 'bookmarked' | 'applied' | 'interview' | 'offer' | 'rejected'

export interface JobApplication {
  id: string
  company: string
  role_title: string
  job_url: string | null
  jd_text: string | null
  resume_version_id: string | null
  status: JobStatus
  notes: string | null
  applied_at: string | null
  created_at: string
}

export interface AdminStats {
  total_24h: number;
  total_7d: number;
  total_all: number;
  providers_24h: Record<string, number>;
  endpoints_24h: Record<string, number>;
  error_rate_24h: number;
  avg_duration_ms: number;
  timeline: Array<{ hour: number; count: number }>;
  recent: LLMLog[];
}

export interface LLMLog {
  id: string;
  provider: string;
  model: string;
  endpoint: string;
  prompt_chars: number;
  response_chars: number;
  duration_ms: number;
  success: boolean;
  error?: string;
  timestamp: number;
}

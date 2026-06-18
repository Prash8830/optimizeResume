import { useQuery } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'
import { Activity, Clock, AlertTriangle, BarChart3, type LucideProps } from 'lucide-react'
import type { ForwardRefExoticComponent, RefAttributes } from 'react'
import { api } from '../lib/api'
import type { AdminStats, LLMLog } from '../types'

type LucideIcon = ForwardRefExoticComponent<Omit<LucideProps, 'ref'> & RefAttributes<SVGSVGElement>>

const COLORS: Record<string, string> = {
  groq: '#e05252',
  gemini: '#6366f1',
}

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  variant = 'default',
}: {
  label: string
  value: string | number
  sub?: string
  icon: LucideIcon
  variant?: 'default' | 'success' | 'warning' | 'error'
}) {
  const colors = {
    default: 'text-secondary',
    success: 'text-success',
    warning: 'text-warning',
    error: 'text-error',
  }
  return (
    <div className="card p-5">
      <div className="flex items-start justify-between mb-3">
        <Icon size={18} className={colors[variant]} />
      </div>
      <div className={`text-2xl font-black mb-1 ${colors[variant]}`}>{value}</div>
      <div className="text-xs font-semibold text-secondary">{label}</div>
      {sub && <div className="text-xs text-muted mt-0.5">{sub}</div>}
    </div>
  )
}

function formatTime(ts: number) {
  return new Date(ts * 1000).toLocaleTimeString('en-IN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export default function Admin() {
  const { data: stats, isLoading, error, refetch } = useQuery<AdminStats>({
    queryKey: ['admin-stats'],
    queryFn: () => api.getAdminStats(),
    refetchInterval: 30000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-secondary text-sm">Loading stats...</p>
        </div>
      </div>
    )
  }

  if (error || !stats) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <p className="text-error text-sm">Failed to load admin stats</p>
      </div>
    )
  }

  // Prepare endpoint chart data
  const endpointData = Object.entries(stats.endpoints_24h).map(([name, count]) => ({
    name,
    count,
  }))

  // Prepare provider pie data
  const providerData = Object.entries(stats.providers_24h).map(([name, value]) => ({
    name,
    value,
  }))

  const errorVariant = stats.error_rate_24h > 0.1 ? 'error' : stats.error_rate_24h > 0.05 ? 'warning' : 'success'

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-black text-primary">LLM Observability</h1>
          <p className="text-secondary text-sm mt-1">Real-time API usage and performance metrics</p>
        </div>
        <button onClick={() => void refetch()} className="btn-ghost text-xs flex items-center gap-1.5">
          <Activity size={14} />
          Refresh
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Calls (24h)" value={stats.total_24h} icon={Activity} />
        <StatCard label="Calls (7d)" value={stats.total_7d} sub="all time: all requests" icon={BarChart3} />
        <StatCard
          label="Avg Response"
          value={`${stats.avg_duration_ms}ms`}
          icon={Clock}
          variant={stats.avg_duration_ms > 5000 ? 'warning' : 'default'}
        />
        <StatCard
          label="Error Rate"
          value={`${(stats.error_rate_24h * 100).toFixed(1)}%`}
          sub="last 24 hours"
          icon={AlertTriangle}
          variant={errorVariant}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-2 gap-6">
        {/* Timeline */}
        <div className="card p-6">
          <h3 className="text-sm font-bold text-primary mb-4">Requests — Last 24h</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={stats.timeline}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e1f2e" />
              <XAxis
                dataKey="hour"
                tick={{ fontSize: 10, fill: '#4e5270' }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis tick={{ fontSize: 10, fill: '#4e5270' }} tickLine={false} axisLine={false} />
              <Tooltip
                contentStyle={{ background: '#12131c', border: '1px solid #1e1f2e', borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: '#8a8eb8' }}
                itemStyle={{ color: '#e05252' }}
              />
              <Line
                type="monotone"
                dataKey="count"
                stroke="#e05252"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: '#e05252' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Provider breakdown */}
        <div className="card p-6">
          <h3 className="text-sm font-bold text-primary mb-4">Provider Breakdown (24h)</h3>
          {providerData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={providerData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {providerData.map((entry) => (
                    <Cell key={entry.name} fill={COLORS[entry.name] ?? '#4e5270'} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#12131c', border: '1px solid #1e1f2e', borderRadius: 8, fontSize: 12 }}
                  itemStyle={{ color: '#f0f2ff' }}
                />
                <Legend
                  formatter={(value) => (
                    <span style={{ fontSize: 12, color: '#8a8eb8', textTransform: 'capitalize' }}>{value}</span>
                  )}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-muted text-sm">
              No data yet
            </div>
          )}
        </div>
      </div>

      {/* Endpoints chart */}
      {endpointData.length > 0 && (
        <div className="card p-6">
          <h3 className="text-sm font-bold text-primary mb-4">Endpoint Usage (24h)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={endpointData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#1e1f2e" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10, fill: '#4e5270' }} tickLine={false} axisLine={false} />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fontSize: 11, fill: '#8a8eb8' }}
                tickLine={false}
                axisLine={false}
                width={120}
              />
              <Tooltip
                contentStyle={{ background: '#12131c', border: '1px solid #1e1f2e', borderRadius: 8, fontSize: 12 }}
                itemStyle={{ color: '#e05252' }}
              />
              <Bar dataKey="count" fill="#e05252" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Recent calls table */}
      <div className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="text-sm font-bold text-primary">Recent Calls</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-border">
                {['Time', 'Provider', 'Model', 'Endpoint', 'Prompt', 'Response', 'Duration', 'Status'].map(
                  (h) => (
                    <th key={h} className="text-left px-4 py-3 text-muted font-semibold uppercase tracking-wider">
                      {h}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {stats.recent.map((log: LLMLog) => (
                <tr key={log.id} className="border-b border-border/50 hover:bg-elevated/30 transition-colors">
                  <td className="px-4 py-3 text-muted font-mono">{formatTime(log.timestamp)}</td>
                  <td className="px-4 py-3">
                    <span
                      className="font-semibold capitalize"
                      style={{ color: COLORS[log.provider] ?? '#8a8eb8' }}
                    >
                      {log.provider}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-secondary font-mono truncate max-w-[120px]" title={log.model}>
                    {log.model.split('-').slice(0, 3).join('-')}
                  </td>
                  <td className="px-4 py-3 text-secondary">{log.endpoint}</td>
                  <td className="px-4 py-3 text-muted">{log.prompt_chars.toLocaleString()}</td>
                  <td className="px-4 py-3 text-muted">{log.response_chars.toLocaleString()}</td>
                  <td className="px-4 py-3 text-secondary">{log.duration_ms}ms</td>
                  <td className="px-4 py-3">
                    {log.success ? (
                      <span className="text-success font-semibold">OK</span>
                    ) : (
                      <span className="text-error font-semibold" title={log.error}>
                        ERR
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              {stats.recent.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-muted">
                    No calls recorded yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

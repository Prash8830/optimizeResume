import { NavLink } from 'react-router-dom'
import { Home, User, Sparkles, Clock, BarChart3, Briefcase, type LucideProps } from 'lucide-react'
import { clsx } from 'clsx'
import type { ForwardRefExoticComponent, RefAttributes } from 'react'

type LucideIcon = ForwardRefExoticComponent<Omit<LucideProps, 'ref'> & RefAttributes<SVGSVGElement>>

const NAV: Array<{ to: string; icon: LucideIcon; label: string }> = [
  { to: '/', icon: Home, label: 'Home' },
  { to: '/profile', icon: User, label: 'Profile Builder' },
  { to: '/generate', icon: Sparkles, label: 'Generate Resume' },
  { to: '/history', icon: Clock, label: 'History' },
  { to: '/jobs', icon: Briefcase, label: 'Job Tracker' },
]

const ADMIN_NAV: Array<{ to: string; icon: LucideIcon; label: string }> = [
  { to: '/admin', icon: BarChart3, label: 'Admin' },
]

interface NavItemProps {
  to: string
  icon: LucideIcon
  label: string
}

function NavItem({ to, icon: Icon, label }: NavItemProps) {
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className={({ isActive }) =>
        clsx(
          'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all',
          isActive
            ? 'bg-accent/10 text-accent border border-accent/20'
            : 'text-secondary hover:text-primary hover:bg-elevated border border-transparent',
        )
      }
    >
      <Icon size={16} />
      {label}
    </NavLink>
  )
}

export default function Sidebar() {
  return (
    <aside className="w-60 flex-shrink-0 border-r border-border flex flex-col bg-surface/50">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-border">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-accent rounded-lg flex items-center justify-center">
            <Sparkles size={14} className="text-white" />
          </div>
          <span className="font-bold text-primary text-sm tracking-tight">OptimizeResume</span>
        </div>
        <p className="text-xs text-muted mt-1 pl-9">AI Resume Tailoring</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map((item) => (
          <NavItem key={item.to} {...item} />
        ))}
        <div className="pt-3 pb-1">
          <p className="section-title px-3">Admin</p>
        </div>
        {ADMIN_NAV.map((item) => (
          <NavItem key={item.to} {...item} />
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-border">
        <p className="text-xs text-muted">Powered by Groq · LangGraph</p>
        <p className="text-xs text-muted/60 mt-0.5">llama-3.3-70b-versatile</p>
      </div>
    </aside>
  )
}

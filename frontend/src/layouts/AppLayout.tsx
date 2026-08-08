import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderGit2,
  Rocket,
  Activity,
  AlertTriangle,
  Settings,
  LogOut,
  ChevronDown,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useAuth } from '@/hooks/useAuth';

interface NavItem {
  to: string;
  label: string;
  icon: React.ElementType;
  disabled?: boolean;
  badge?: string;
}

const navItems: NavItem[] = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/projects', label: 'Projects', icon: FolderGit2 },
  { to: '/deployments', label: 'Deployments', icon: Rocket, disabled: true, badge: 'Phase 5' },
  { to: '/monitoring', label: 'Monitoring', icon: Activity, disabled: true, badge: 'Phase 6' },
  { to: '/incidents', label: 'Incidents', icon: AlertTriangle, disabled: true, badge: 'Phase 9' },
];

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <aside className="w-56 flex-shrink-0 flex flex-col bg-surface-raised border-r border-surface-border">
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-4 h-14 border-b border-surface-border">
          <div className="w-7 h-7 rounded-md bg-brand flex items-center justify-center flex-shrink-0">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M8 2L14 5.5V10.5L8 14L2 10.5V5.5L8 2Z" stroke="white" strokeWidth="1.5" strokeLinejoin="round"/>
              <circle cx="8" cy="8" r="2" fill="white"/>
            </svg>
          </div>
          <span className="font-semibold text-sm text-text-primary tracking-tight">CloudPilot</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-3 px-2">
          <p className="section-header px-2 mb-3">Navigation</p>
          {navItems.map((item) => {
            const Icon = item.icon;
            if (item.disabled) {
              return (
                <div
                  key={item.to}
                  className="sidebar-item opacity-40 cursor-not-allowed select-none"
                >
                  <Icon size={15} />
                  <span className="flex-1">{item.label}</span>
                  {item.badge && (
                    <span className="text-[10px] text-text-muted bg-surface-border rounded px-1.5 py-0.5">
                      {item.badge}
                    </span>
                  )}
                </div>
              );
            }
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  clsx('sidebar-item', isActive && 'sidebar-item-active')
                }
              >
                <Icon size={15} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Bottom: Settings + User */}
        <div className="border-t border-surface-border py-2 px-2 space-y-1">
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              clsx('sidebar-item', isActive && 'sidebar-item-active')
            }
          >
            <Settings size={15} />
            <span>Settings</span>
          </NavLink>
          <button
            onClick={handleLogout}
            className="sidebar-item w-full text-accent-red/70 hover:text-accent-red hover:bg-accent-red/5"
          >
            <LogOut size={15} />
            <span>Logout</span>
          </button>
        </div>

        {/* User info */}
        <div className="border-t border-surface-border px-3 py-3">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-brand/20 border border-brand/30 flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-semibold text-brand-light">
                {user?.name?.charAt(0).toUpperCase() ?? 'U'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-text-primary truncate">{user?.name}</p>
              <p className="text-[11px] text-text-muted truncate">{user?.email}</p>
            </div>
          </div>
        </div>
      </aside>

      {/* ── Main content ────────────────────────────────────────────── */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}

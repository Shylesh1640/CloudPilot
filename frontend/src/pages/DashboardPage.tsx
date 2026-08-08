import { Link } from 'react-router-dom';
import { FolderGit2, Rocket, Activity, AlertTriangle, ArrowRight } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useProjects } from '@/hooks/useProjects';
import { Card } from '@/components/ui/Card';
import { StatusBadge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

interface StatCardProps {
  label: string;
  value: number | string;
  icon: React.ElementType;
  comingSoon?: boolean;
}

function StatCard({ label, value, icon: Icon, comingSoon }: StatCardProps) {
  return (
    <div className="card p-4">
      <div className="flex items-start justify-between mb-3">
        <p className="data-label">{label}</p>
        <div className="w-7 h-7 rounded-md bg-surface-overlay border border-surface-border flex items-center justify-center">
          <Icon size={13} className="text-text-muted" />
        </div>
      </div>
      {comingSoon ? (
        <div>
          <p className="text-2xl font-semibold text-text-muted">—</p>
          <p className="text-[11px] text-text-muted mt-1">Coming Soon</p>
        </div>
      ) : (
        <p className="text-2xl font-semibold text-text-primary">{value}</p>
      )}
    </div>
  );
}

export function DashboardPage() {
  const { user } = useAuth();
  const { projects, isLoading } = useProjects();

  const recentProjects = projects.slice(0, 5);

  return (
    <div className="p-6 max-w-5xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-text-primary">
          Welcome back, {user?.name?.split(' ')[0] ?? 'Developer'}
        </h1>
        <p className="text-sm text-text-muted mt-0.5">
          CloudPilot Dashboard — Phase 1
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        <StatCard
          label="Projects"
          value={isLoading ? '...' : projects.length}
          icon={FolderGit2}
        />
        <StatCard
          label="Deployments"
          value={0}
          icon={Rocket}
          comingSoon
        />
        <StatCard
          label="Services Running"
          value={0}
          icon={Activity}
          comingSoon
        />
        <StatCard
          label="Open Incidents"
          value={0}
          icon={AlertTriangle}
          comingSoon
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Recent Projects */}
        <div className="lg:col-span-2">
          <Card>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold">Recent Projects</h2>
              <Link
                to="/projects"
                className="text-xs text-brand-light hover:underline flex items-center gap-1"
              >
                View all
                <ArrowRight size={11} />
              </Link>
            </div>

            {isLoading ? (
              <div className="flex justify-center py-8">
                <LoadingSpinner size="sm" />
              </div>
            ) : recentProjects.length === 0 ? (
              <div className="text-center py-8">
                <FolderGit2 size={28} className="text-text-muted mx-auto mb-2" />
                <p className="text-sm text-text-muted">No projects yet.</p>
                <Link
                  to="/projects"
                  className="text-xs text-brand-light hover:underline mt-1 inline-block"
                >
                  Create your first project →
                </Link>
              </div>
            ) : (
              <div className="space-y-2">
                {recentProjects.map((project) => (
                  <Link
                    key={project.id}
                    to={`/projects/${project.id}`}
                    className="flex items-center justify-between p-2.5 rounded-md hover:bg-surface-overlay transition-colors group"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-7 h-7 rounded-md bg-surface-overlay border border-surface-border flex items-center justify-center flex-shrink-0 group-hover:border-surface-border/80">
                        <FolderGit2 size={13} className="text-text-muted" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-text-primary truncate">
                          {project.name}
                        </p>
                        {project.description && (
                          <p className="text-xs text-text-muted truncate">{project.description}</p>
                        )}
                      </div>
                    </div>
                    <StatusBadge status={project.status} />
                  </Link>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Activity / Coming Soon */}
        <div className="space-y-4">
          <Card>
            <h2 className="text-sm font-semibold mb-3">Recent Activity</h2>
            <div className="text-center py-6">
              <Activity size={24} className="text-text-muted mx-auto mb-2" />
              <p className="text-xs text-text-muted">No activity yet.</p>
              <p className="text-[11px] text-text-muted mt-0.5">
                Deployment events will appear here.
              </p>
            </div>
          </Card>

          <Card>
            <h2 className="text-sm font-semibold mb-3">System Status</h2>
            <div className="space-y-2">
              {[
                { label: 'API', status: 'Operational', color: 'bg-accent-green' },
                { label: 'Database', status: 'Operational', color: 'bg-accent-green' },
                { label: 'Container Engine', status: 'Coming Soon', color: 'bg-text-muted' },
                { label: 'Metrics', status: 'Coming Soon', color: 'bg-text-muted' },
              ].map((item) => (
                <div key={item.label} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`status-dot ${item.color}`} />
                    <span className="text-xs text-text-secondary">{item.label}</span>
                  </div>
                  <span className="text-[11px] text-text-muted">{item.status}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

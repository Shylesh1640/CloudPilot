import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Globe,
  GitBranch,
  Activity,
  AlertTriangle,
  Settings,
  Calendar,
  Edit2,
  Check,
  X,
} from 'lucide-react';
import { projectService } from '@/services/projectService';
import { getErrorMessage } from '@/services/api';
import { StatusBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { Project } from '@/types';

type Tab = 'overview' | 'architecture' | 'deployments' | 'observability' | 'incidents' | 'settings';

const tabs: { id: Tab; label: string; available: boolean; phase?: string }[] = [
  { id: 'overview', label: 'Overview', available: true },
  { id: 'architecture', label: 'Architecture', available: false, phase: 'Phase 3' },
  { id: 'deployments', label: 'Deployments', available: false, phase: 'Phase 5' },
  { id: 'observability', label: 'Observability', available: false, phase: 'Phase 6' },
  { id: 'incidents', label: 'Incidents', available: false, phase: 'Phase 9' },
  { id: 'settings', label: 'Settings', available: true },
];

function ComingSoon({ phase, feature }: { phase: string; feature: string }) {
  return (
    <div className="card p-12 text-center">
      <div className="w-10 h-10 rounded-lg bg-surface-overlay border border-surface-border flex items-center justify-center mx-auto mb-3">
        <Activity size={18} className="text-text-muted" />
      </div>
      <h3 className="text-sm font-semibold mb-1">{feature}</h3>
      <p className="text-xs text-text-muted mb-2">Coming in {phase}</p>
      <span className="tag bg-surface-border text-text-muted">{phase}</span>
    </div>
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<Tab>('overview');

  // Edit state
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState('');

  useEffect(() => {
    const load = async () => {
      if (!projectId) return;
      try {
        const p = await projectService.get(projectId);
        setProject(p);
        setEditName(p.name);
        setEditDesc(p.description ?? '');
      } catch {
        setError('Project not found or access denied.');
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [projectId]);

  const handleSave = async () => {
    if (!project || !editName.trim()) return;
    setSaveError('');
    setIsSaving(true);
    try {
      const updated = await projectService.update(project.id, {
        name: editName.trim(),
        description: editDesc.trim() || undefined,
      });
      setProject(updated);
      setIsEditing(false);
    } catch (err) {
      setSaveError(getErrorMessage(err));
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="card p-8 text-center">
          <p className="text-sm text-accent-red mb-3">{error || 'Project not found.'}</p>
          <Link to="/projects" className="text-sm text-brand-light hover:underline">
            ← Back to Projects
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto animate-fade-in">
      {/* Breadcrumb */}
      <Link
        to="/projects"
        className="inline-flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary mb-4 transition-colors"
      >
        <ArrowLeft size={12} />
        Projects
      </Link>

      {/* Project Header */}
      <div className="flex items-start justify-between mb-5">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-xl font-semibold">{project.name}</h1>
            <StatusBadge status={project.status} />
          </div>
          {project.description && (
            <p className="text-sm text-text-muted">{project.description}</p>
          )}
          <p className="text-xs text-text-muted mt-1 flex items-center gap-1">
            <Calendar size={11} />
            Created {formatDate(project.created_at)}
          </p>
        </div>
        <Button
          variant="secondary"
          onClick={() => { setIsEditing(!isEditing); setSaveError(''); }}
          className="gap-1.5 flex-shrink-0"
        >
          <Edit2 size={13} />
          Edit
        </Button>
      </div>

      {/* Inline Edit */}
      {isEditing && (
        <div className="card p-4 mb-4 animate-fade-in">
          <h3 className="text-sm font-semibold mb-3">Edit Project</h3>
          {saveError && (
            <div className="bg-accent-red/10 border border-accent-red/20 rounded-md px-3 py-2 mb-3">
              <p className="text-sm text-accent-red">{saveError}</p>
            </div>
          )}
          <div className="space-y-3">
            <Input
              id="edit-project-name"
              label="Name"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              required
            />
            <Textarea
              id="edit-project-desc"
              label="Description"
              value={editDesc}
              onChange={(e) => setEditDesc(e.target.value)}
              rows={2}
            />
            <div className="flex gap-2">
              <Button id="save-project-btn" onClick={handleSave} isLoading={isSaving} className="gap-1.5">
                <Check size={13} />
                Save
              </Button>
              <Button
                variant="secondary"
                onClick={() => { setIsEditing(false); setSaveError(''); }}
              >
                <X size={13} />
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-surface-border mb-5">
        <nav className="flex gap-0" aria-label="Project tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => tab.available && setActiveTab(tab.id)}
              className={`
                px-4 py-2.5 text-xs font-medium border-b-2 transition-colors
                ${activeTab === tab.id
                  ? 'border-brand text-text-primary'
                  : 'border-transparent text-text-muted'}
                ${tab.available
                  ? 'hover:text-text-secondary cursor-pointer'
                  : 'opacity-40 cursor-not-allowed'}
              `}
              disabled={!tab.available}
              aria-selected={activeTab === tab.id}
            >
              {tab.label}
              {tab.phase && (
                <span className="ml-1.5 text-[10px] bg-surface-border rounded px-1">
                  {tab.phase}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-fade-in">
          {/* Project Info */}
          <div className="card p-4">
            <h3 className="text-sm font-semibold mb-3">Project Details</h3>
            <dl className="space-y-2">
              <div className="flex justify-between">
                <dt className="data-label">ID</dt>
                <dd className="text-xs font-mono text-text-secondary truncate max-w-[60%]">
                  {project.id}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="data-label">Status</dt>
                <dd><StatusBadge status={project.status} /></dd>
              </div>
              <div className="flex justify-between">
                <dt className="data-label">Created</dt>
                <dd className="text-xs text-text-secondary">{formatDate(project.created_at)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="data-label">Updated</dt>
                <dd className="text-xs text-text-secondary">{formatDate(project.updated_at)}</dd>
              </div>
            </dl>
          </div>

          {/* Next Steps */}
          <div className="card p-4">
            <h3 className="text-sm font-semibold mb-3">Next Steps</h3>
            <div className="space-y-2">
              {[
                { label: 'Connect GitHub repository', phase: 'Phase 2', icon: GitBranch },
                { label: 'Generate infrastructure plan', phase: 'Phase 3', icon: Globe },
                { label: 'Deploy containers', phase: 'Phase 4', icon: Activity },
              ].map((step) => {
                const Icon = step.icon;
                return (
                  <div key={step.label} className="flex items-center gap-2.5 p-2 rounded-md bg-surface-overlay">
                    <Icon size={13} className="text-text-muted flex-shrink-0" />
                    <span className="text-xs text-text-secondary flex-1">{step.label}</span>
                    <span className="text-[10px] text-text-muted bg-surface-border rounded px-1.5 py-0.5">
                      {step.phase}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'architecture' && (
        <ComingSoon phase="Phase 3" feature="Infrastructure Architecture" />
      )}
      {activeTab === 'deployments' && (
        <ComingSoon phase="Phase 5" feature="Deployment History" />
      )}
      {activeTab === 'observability' && (
        <ComingSoon phase="Phase 6" feature="Real-Time Observability" />
      )}
      {activeTab === 'incidents' && (
        <ComingSoon phase="Phase 9" feature="Incident Management" />
      )}
      {activeTab === 'settings' && (
        <div className="card p-4 animate-fade-in">
          <h3 className="text-sm font-semibold mb-4">Project Settings</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-3 border-b border-surface-border">
              <div>
                <p className="text-sm font-medium">GitHub Integration</p>
                <p className="text-xs text-text-muted">Connect a repository — available in Phase 2</p>
              </div>
              <Button variant="secondary" disabled className="text-xs gap-1.5">
                <GitBranch size={12} />
                Connect
              </Button>
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="text-sm font-medium text-accent-red">Delete Project</p>
                <p className="text-xs text-text-muted">Permanently remove this project and all data</p>
              </div>
              <Link to="/projects">
                <Button variant="danger" className="text-xs">
                  Delete
                </Button>
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

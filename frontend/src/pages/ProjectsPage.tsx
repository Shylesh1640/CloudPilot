import { useState } from 'react';
import { Link } from 'react-router-dom';
import { FolderGit2, Plus, Search, Trash2, ExternalLink } from 'lucide-react';
import { useProjects } from '@/hooks/useProjects';
import { getErrorMessage } from '@/services/api';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { StatusBadge } from '@/components/ui/Badge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function ProjectsPage() {
  const { projects, isLoading, error, createProject, deleteProject } = useProjects();
  const [search, setSearch] = useState('');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createDesc, setCreateDesc] = useState('');
  const [createError, setCreateError] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const filtered = projects.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      (p.description ?? '').toLowerCase().includes(search.toLowerCase())
  );

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createName.trim()) return;
    setCreateError('');
    setIsCreating(true);
    try {
      await createProject({ name: createName.trim(), description: createDesc.trim() || undefined });
      setIsCreateOpen(false);
      setCreateName('');
      setCreateDesc('');
    } catch (err) {
      setCreateError(getErrorMessage(err));
    } finally {
      setIsCreating(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete project "${name}"? This cannot be undone.`)) return;
    setDeletingId(id);
    try {
      await deleteProject(id);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Projects</h1>
          <p className="text-sm text-text-muted mt-0.5">
            {projects.length} project{projects.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Button
          id="create-project-btn"
          onClick={() => setIsCreateOpen(true)}
          className="gap-1.5"
        >
          <Plus size={14} />
          New Project
        </Button>
      </div>

      {/* Search */}
      {projects.length > 0 && (
        <div className="relative mb-4">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            id="project-search"
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search projects..."
            className="input-base text-sm pl-8"
          />
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <div className="card p-6 text-center">
          <p className="text-sm text-accent-red">{error}</p>
        </div>
      ) : filtered.length === 0 && search ? (
        <div className="card p-8 text-center">
          <Search size={28} className="text-text-muted mx-auto mb-2" />
          <p className="text-sm text-text-muted">No projects match "{search}"</p>
        </div>
      ) : projects.length === 0 ? (
        <div className="card p-12 text-center">
          <FolderGit2 size={36} className="text-text-muted mx-auto mb-3" />
          <h2 className="text-sm font-semibold mb-1">No projects yet</h2>
          <p className="text-sm text-text-muted mb-4">
            Connect a GitHub repository to get started.
          </p>
          <Button
            id="create-first-project-btn"
            onClick={() => setIsCreateOpen(true)}
            className="gap-1.5"
          >
            <Plus size={14} />
            Create Project
          </Button>
          <p className="text-xs text-text-muted mt-3">
            GitHub integration is available in Phase 2.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((project) => (
            <div
              key={project.id}
              className="card p-4 flex items-center justify-between gap-3 hover:border-surface-border/80 transition-colors group"
            >
              <div className="flex items-center gap-3 min-w-0 flex-1">
                <div className="w-8 h-8 rounded-md bg-surface-overlay border border-surface-border flex items-center justify-center flex-shrink-0">
                  <FolderGit2 size={14} className="text-text-muted" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <Link
                      to={`/projects/${project.id}`}
                      className="text-sm font-medium text-text-primary hover:text-brand-light transition-colors"
                    >
                      {project.name}
                    </Link>
                    <StatusBadge status={project.status} />
                  </div>
                  {project.description && (
                    <p className="text-xs text-text-muted truncate">{project.description}</p>
                  )}
                  <p className="text-[11px] text-text-muted mt-0.5">
                    Created {formatDate(project.created_at)}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-1 flex-shrink-0">
                <Link
                  to={`/projects/${project.id}`}
                  className="btn-ghost text-xs gap-1 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <ExternalLink size={12} />
                  Open
                </Link>
                <button
                  onClick={() => handleDelete(project.id, project.name)}
                  disabled={deletingId === project.id}
                  className="p-1.5 rounded-md text-text-muted hover:text-accent-red hover:bg-accent-red/10 transition-colors opacity-0 group-hover:opacity-100 disabled:opacity-50"
                  aria-label={`Delete ${project.name}`}
                >
                  {deletingId === project.id ? (
                    <LoadingSpinner size="sm" />
                  ) : (
                    <Trash2 size={13} />
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => { setIsCreateOpen(false); setCreateError(''); }}
        title="New Project"
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => setIsCreateOpen(false)}
            >
              Cancel
            </Button>
            <Button
              id="create-project-submit"
              isLoading={isCreating}
              onClick={handleCreate as never}
              type="submit"
              form="create-project-form"
            >
              Create Project
            </Button>
          </>
        }
      >
        {createError && (
          <div className="bg-accent-red/10 border border-accent-red/20 rounded-md px-3 py-2 mb-4">
            <p className="text-sm text-accent-red">{createError}</p>
          </div>
        )}
        <form id="create-project-form" onSubmit={handleCreate} className="space-y-4">
          <Input
            id="new-project-name"
            label="Project Name"
            value={createName}
            onChange={(e) => setCreateName(e.target.value)}
            placeholder="my-web-app"
            required
            autoFocus
          />
          <Textarea
            id="new-project-description"
            label="Description (optional)"
            value={createDesc}
            onChange={(e) => setCreateDesc(e.target.value)}
            placeholder="A brief description of this project..."
            rows={3}
          />
        </form>
      </Modal>
    </div>
  );
}

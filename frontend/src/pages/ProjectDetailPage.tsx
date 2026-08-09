import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  GitBranch,
  Activity,
  Calendar,
  Edit2,
  Check,
  X,
  Search,
  Play,
  Square,
  Sparkles,
  Radio,
} from 'lucide-react';
import { projectService } from '@/services/projectService';
import { getErrorMessage } from '@/services/api';
import { useAnalysis } from '@/hooks/useAnalysis';
import { usePlan } from '@/hooks/usePlan';
import { useDeployment } from '@/hooks/useDeployment';
import { useHealth } from '@/hooks/useHealth';
import { StatusBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input, Textarea } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ArchitectureGraphView } from '@/components/plan/ArchitectureGraphView';
import { ServiceDetailPanel } from '@/components/plan/ServiceDetailPanel';
import { PlanSummaryView } from '@/components/plan/PlanSummaryView';
import { DeploymentProgressTracker } from '@/components/deployment/DeploymentProgressTracker';
import { ServiceLogsModal } from '@/components/deployment/ServiceLogsModal';
import { DeploymentHealthCard } from '@/components/health/DeploymentHealthCard';
import { HealthEventsTimeline } from '@/components/health/HealthEventsTimeline';
import { ObservabilitySummaryCards } from '@/components/observability/ObservabilitySummaryCards';
import { MetricsChart } from '@/components/observability/MetricsChart';
import { LogViewer } from '@/components/observability/LogViewer';
import { ServiceMetricsGrid } from '@/components/observability/ServiceMetricsGrid';
import { ReadmeGeneratorPanel } from '@/components/readme/ReadmeGeneratorPanel';
import { useObservabilitySocket } from '@/hooks/useObservabilitySocket';
import type { Project, ServiceDefinition } from '@/types';

type Tab = 'overview' | 'architecture' | 'deployments' | 'observability' | 'incidents' | 'settings';

const tabs: { id: Tab; label: string; available: boolean; phase?: string }[] = [
  { id: 'overview', label: 'Overview', available: true },
  { id: 'architecture', label: 'Architecture', available: true },
  { id: 'deployments', label: 'Deployments', available: false, phase: 'Phase 5' },
  { id: 'observability', label: 'Observability', available: true },
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

function ArchitectureTab({ projectId }: { projectId: string }) {
  const [repoUrl, setRepoUrl] = useState('');
  const [selectedServiceId, setSelectedServiceId] = useState<string | null>(null);
  const [logsModalService, setLogsModalService] = useState<{ id: string; name: string } | null>(null);

  const { analysis, isLoading: isAnalyzing, error: analysisError, startAnalysis } = useAnalysis();
  const { planResult, isLoading: isPlanning, error: planError, generatePlan, regeneratePlan } = usePlan();
  const { deployment, services: deploymentServices, isLoading: isDeploying, error: deployError, triggerDeployment, stopDeployment, restartService } = useDeployment();
  const { health, events: healthEvents } = useHealth(deployment?.id ?? null);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    try {
      await startAnalysis(projectId, repoUrl.trim());
    } catch {}
  };

  const handleGeneratePlan = async () => {
    if (!analysis) return;
    try {
      await generatePlan(analysis.id);
    } catch {}
  };

  const handleRegeneratePlan = async () => {
    if (!planResult) return;
    try {
      await regeneratePlan(planResult.id);
    } catch {}
  };

  const handleDeploy = async () => {
    if (!planResult) return;
    try {
      await triggerDeployment(planResult.id);
    } catch {}
  };

  const isAnalysisActive = analysis && ['PENDING', 'CLONING', 'SCANNING', 'ANALYZING'].includes(analysis.status);
  const isPlanActive = isPlanning || (planResult && ['PENDING', 'GENERATING', 'VALIDATING'].includes(planResult.status));

  const plan = planResult?.plan_data;
  const selectedService: ServiceDefinition | undefined = plan?.services.find((s) => s.id === selectedServiceId);
  const selectedDeploymentService = deploymentServices.find((s) => s.service_id === selectedServiceId);
  const selectedHealthStatus = health?.services[selectedServiceId || ''];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 1. Repository Connection Form */}
      {!analysis && (
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-2">
            <GitBranch size={16} className="text-brand-light" />
            <h2 className="text-sm font-semibold">Connect GitHub Repository</h2>
          </div>
          <p className="text-xs text-text-muted mb-4">
            Enter a public GitHub repository URL to inspect code, frameworks, and generate an AI infrastructure plan.
          </p>

          <form onSubmit={handleAnalyze} className="space-y-4">
            <div className="flex gap-2">
              <Input
                id="github-repo-url"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/user/repository"
                className="flex-1"
                disabled={isAnalysisActive || isAnalyzing}
              />
              <Button
                id="analyze-repo-btn"
                type="submit"
                isLoading={isAnalyzing || isAnalysisActive}
                disabled={!repoUrl.trim()}
                className="gap-2 flex-shrink-0"
              >
                <Search size={14} />
                Analyze Repository
              </Button>
            </div>
            {analysisError && (
              <div className="bg-accent-red/10 border border-accent-red/20 rounded-md p-3">
                <p className="text-xs text-accent-red">{analysisError}</p>
              </div>
            )}
          </form>
        </div>
      )}

      {/* 2. Analysis Progress */}
      {analysis && isAnalysisActive && (
        <div className="card p-6 space-y-4 animate-fade-in">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <LoadingSpinner size="sm" />
              <h3 className="text-sm font-semibold text-text-primary">Analyzing Repository...</h3>
            </div>
            <span className="text-xs font-mono text-brand-light">{analysis.progress}%</span>
          </div>

          <div className="w-full bg-surface-overlay h-2 rounded-full overflow-hidden border border-surface-border">
            <div
              className="bg-brand h-full transition-all duration-300 ease-out"
              style={{ width: `${analysis.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* 3. Analysis Completed & Trigger AI Plan Button */}
      {analysis && analysis.status === 'COMPLETED' && !planResult && (
        <div className="card p-6 space-y-4 border-brand/30 animate-fade-in">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-semibold text-text-primary">
                  {analysis.repository_name || 'Repository Profile'}
                </h3>
                <span className="tag bg-accent-green/10 text-accent-green border border-accent-green/20">
                  Analysis Complete
                </span>
              </div>
              <p className="text-xs text-text-muted mt-0.5">{analysis.repository_url}</p>
            </div>
            <Button
              id="generate-ai-plan-btn"
              onClick={handleGeneratePlan}
              isLoading={isPlanActive}
              className="gap-2 bg-brand hover:bg-brand-hover"
            >
              <Sparkles size={14} />
              Generate Infrastructure Plan
            </Button>
          </div>

          {planError && (
            <div className="bg-accent-red/10 border border-accent-red/20 rounded-md p-3">
              <p className="text-xs text-accent-red">{planError}</p>
            </div>
          )}
        </div>
      )}

      {/* 3b. README Generator — shown once analysis is complete */}
      {analysis && analysis.status === 'COMPLETED' && (
        <ReadmeGeneratorPanel
          analysisId={analysis.id}
          repoName={analysis.repository_name || 'repository'}
        />
      )}

      {/* 4. Plan Generation Progress */}
      {isPlanActive && (
        <div className="card p-6 space-y-4 animate-fade-in border-brand/30">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <LoadingSpinner size="sm" />
              <h3 className="text-sm font-semibold text-text-primary">AI Architecture Planning in Progress...</h3>
            </div>
          </div>
        </div>
      )}

      {/* 5. Phase 3 & 4: Plan View + Deploy Action Header */}
      {planResult && planResult.status === 'COMPLETED' && plan && (
        <div className="space-y-6 animate-fade-in">

          {/* Deploy Action Control Header */}
          <div className="card p-5 border-brand/40 flex items-center justify-between bg-surface-overlay">
            <div>
              <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
                <Play size={16} className="text-accent-green" />
                Container Service Orchestrator (Phase 4)
              </h3>
              <p className="text-xs text-text-muted mt-0.5">
                Execute validated topology plan directly on the Docker Engine host.
              </p>
            </div>

            <div className="flex items-center gap-3">
              {deployment && deployment.status === 'RUNNING' && (
                <Button
                  variant="danger"
                  onClick={stopDeployment}
                  className="gap-1.5 text-xs"
                >
                  <Square size={13} />
                  Stop Deployment
                </Button>
              )}

              <Button
                id="deploy-application-btn"
                onClick={handleDeploy}
                isLoading={isDeploying}
                className="gap-2 bg-accent-green hover:bg-accent-green/90 text-black font-bold"
              >
                <Play size={14} />
                Deploy Application
              </Button>
            </div>
          </div>

          {deployError && (
            <div className="bg-accent-red/10 border border-accent-red/20 rounded-md p-3">
              <p className="text-xs text-accent-red">{deployError}</p>
            </div>
          )}

          {/* Live Deployment Progress Timeline */}
          {deployment && <DeploymentProgressTracker deployment={deployment} />}

          {/* Phase 5: Deployment Health Engine Summary Card */}
          {health && <DeploymentHealthCard health={health} />}

          {/* Phase 5: Health Events Timeline */}
          {healthEvents.length > 0 && <HealthEventsTimeline events={healthEvents} />}

          {/* Plan Summary View */}
          <PlanSummaryView
            plan={plan}
            version={planResult.version}
            aiProvider={planResult.ai_provider}
            aiModel={planResult.ai_model}
            durationMs={planResult.generation_duration_ms}
            onRegenerate={handleRegeneratePlan}
            isRegenerating={isPlanActive}
          />

          {/* Interactive Topology Graph with Live Container & Health Badges */}
          <ArchitectureGraphView
            graph={plan.graph}
            services={plan.services}
            deploymentServices={deploymentServices}
            healthMap={health?.services}
            selectedServiceId={selectedServiceId}
            onSelectService={(id) => setSelectedServiceId(id)}
          />

          {/* Service Detail Panel with Restart, Logs & Health Actions */}
          {selectedService && (
            <ServiceDetailPanel
              service={selectedService}
              plan={plan}
              deploymentService={selectedDeploymentService}
              healthStatus={selectedHealthStatus}
              onClose={() => setSelectedServiceId(null)}
              onRestartService={(sid) => restartService(sid)}
              onOpenLogs={(sid, sname) => setLogsModalService({ id: sid, name: sname })}
            />
          )}

          {/* Container Logs Viewer Modal */}
          {logsModalService && deployment && (
            <ServiceLogsModal
              deploymentId={deployment.id}
              serviceId={logsModalService.id}
              serviceName={logsModalService.name}
              onClose={() => setLogsModalService(null)}
            />
          )}
        </div>
      )}
    </div>
  );
}

function ObservabilityTab({ projectId }: { projectId: string }) {
  const { deployment } = useDeployment();
  const { health } = useHealth(deployment?.id ?? null);
  const { metrics, socketStatus } = useObservabilitySocket(deployment?.id ?? null);
  const [selectedServiceId, setSelectedServiceId] = useState<string | null>(null);

  if (!deployment) {
    return (
      <div className="card p-12 text-center space-y-3">
        <Activity size={32} className="text-text-muted mx-auto" />
        <h3 className="text-base font-bold text-text-primary">No Active Deployment Found</h3>
        <p className="text-xs text-text-muted max-w-md mx-auto">
          Deploy your application under the Architecture tab first to view real-time container CPU, Memory, Network telemetry, and logs.
        </p>
      </div>
    );
  }

  const activeServiceId = selectedServiceId || Object.keys(metrics?.services || {})[0] || 'api';

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 1. Real-Time Telemetry Summary Cards */}
      <ObservabilitySummaryCards metrics={metrics} socketStatus={socketStatus} />

      {/* 2. Service Telemetry Matrix */}
      <ServiceMetricsGrid
        metrics={metrics}
        healthMap={health?.services}
        selectedServiceId={activeServiceId}
        onSelectService={(sid) => setSelectedServiceId(sid)}
      />

      {/* 3. Recharts Time-Series Chart */}
      {deployment && activeServiceId && (
        <MetricsChart deploymentId={deployment.id} serviceId={activeServiceId} />
      )}

      {/* 4. Terminal Log Viewer */}
      {deployment && activeServiceId && (
        <LogViewer deploymentId={deployment.id} serviceId={activeServiceId} />
      )}
    </div>
  );
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
    <div className="p-6 max-w-6xl mx-auto animate-fade-in">
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

          {/* Roadmap */}
          <div className="card p-4">
            <h3 className="text-sm font-semibold mb-3">Phase Roadmap</h3>
            <div className="space-y-2">
              {[
                { label: 'Connect & Analyze GitHub repository', phase: 'Phase 2', icon: GitBranch, active: true },
                { label: 'Generate AI infrastructure plan', phase: 'Phase 3', icon: Sparkles, active: true },
                { label: 'Container & Service Orchestrator', phase: 'Phase 4', icon: Play, active: true },
                { label: 'Health Check & Monitoring Engine', phase: 'Phase 5', icon: Activity, active: true },
                { label: 'Real-Time Observability Platform', phase: 'Phase 6', icon: Radio, active: true },
              ].map((step) => {
                const Icon = step.icon;
                return (
                  <div key={step.label} className={`flex items-center gap-2.5 p-2 rounded-md ${step.active ? 'bg-brand/10 border border-brand/20 text-brand-light' : 'bg-surface-overlay'}`}>
                    <Icon size={13} className={step.active ? 'text-brand-light' : 'text-text-muted'} />
                    <span className="text-xs flex-1">{step.label}</span>
                    <span className="text-[10px] bg-surface-border rounded px-1.5 py-0.5">
                      {step.phase}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'architecture' && <ArchitectureTab projectId={project.id} />}

      {activeTab === 'deployments' && (
        <ComingSoon phase="Phase 5" feature="Deployment History & Health Monitoring" />
      )}
      {activeTab === 'observability' && <ObservabilityTab projectId={project.id} />}
      {activeTab === 'incidents' && (
        <ComingSoon phase="Phase 9" feature="Incident Management" />
      )}
      {activeTab === 'settings' && (
        <div className="card p-4 animate-fade-in">
          <h3 className="text-sm font-semibold mb-4">Project Settings</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-3 border-b border-surface-border">
              <div>
                <p className="text-sm font-medium">GitHub Repository Integration</p>
                <p className="text-xs text-text-muted">Connect public repositories under Architecture tab</p>
              </div>
              <Button
                variant="secondary"
                onClick={() => setActiveTab('architecture')}
                className="text-xs gap-1.5"
              >
                <GitBranch size={12} />
                Connect
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

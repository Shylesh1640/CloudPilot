import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  GitBranch,
  Layers,
  Database,
  Cpu,
  Terminal,
  Shield,
  FileCode,
  Box,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import { analysisService } from '@/services/analysisService';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { RepositoryAnalysis, RepositoryProfile } from '@/types';

function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  let color = 'bg-accent-green/10 text-accent-green border-accent-green/20';
  let label = 'High Confidence';

  if (confidence < 0.7 && confidence >= 0.4) {
    color = 'bg-accent-yellow/10 text-accent-yellow border-accent-yellow/20';
    label = 'Medium Confidence';
  } else if (confidence < 0.4) {
    color = 'bg-surface-border text-text-muted border-surface-border';
    label = 'Low Confidence';
  }

  return (
    <span className={`tag border ${color}`}>
      {pct}% · {label}
    </span>
  );
}

export function AnalysisResultPage() {
  const { projectId, analysisId } = useParams<{ projectId: string; analysisId: string }>();
  const [analysis, setAnalysis] = useState<RepositoryAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'dependencies' | 'services' | 'infrastructure' | 'ports' | 'env'>('overview');

  useEffect(() => {
    const load = async () => {
      if (!analysisId) return;
      try {
        const data = await analysisService.getResult(analysisId);
        setAnalysis(data);
      } catch (err) {
        setError('Failed to load repository analysis report.');
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [analysisId]);

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !analysis || !analysis.analysis_result) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="card p-8 text-center">
          <p className="text-sm text-accent-red mb-3">{error || 'Analysis report not found.'}</p>
          <Link to={`/projects/${projectId}`} className="text-sm text-brand-light hover:underline">
            ← Back to Project
          </Link>
        </div>
      </div>
    );
  }

  const profile: RepositoryProfile = analysis.analysis_result;

  return (
    <div className="p-6 max-w-6xl mx-auto animate-fade-in space-y-6">
      {/* Header Breadcrumb */}
      <Link
        to={`/projects/${projectId}`}
        className="inline-flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary transition-colors"
      >
        <ArrowLeft size={12} />
        Back to Project
      </Link>

      {/* Main Title & Repository Overview */}
      <div className="card p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-xl font-bold text-text-primary">
                {profile.repository.owner}/{profile.repository.name}
              </h1>
              {profile.is_monorepo && (
                <span className="tag bg-accent-purple/10 text-accent-purple border border-accent-purple/20">
                  Monorepo Detected
                </span>
              )}
            </div>
            <p className="text-xs text-text-muted font-mono mb-3">{profile.repository.url}</p>
            {profile.repository.commit_sha && (
              <p className="text-[11px] text-text-muted font-mono">
                Analyzed Commit: {profile.repository.commit_sha.slice(0, 8)}
              </p>
            )}
          </div>
          <span className="tag bg-accent-green/10 text-accent-green border border-accent-green/20">
            Phase 2 Report
          </span>
        </div>

        {/* Primary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5 pt-5 border-t border-surface-border">
          <div>
            <p className="data-label">Primary Language</p>
            <p className="text-sm font-semibold text-brand-light mt-0.5">
              {profile.languages.primary}
            </p>
          </div>
          <div>
            <p className="data-label">Frameworks</p>
            <p className="text-sm font-semibold mt-0.5">
              {profile.frameworks.map((f) => f.name).join(', ') || 'None'}
            </p>
          </div>
          <div>
            <p className="data-label">Inferred Services</p>
            <p className="text-sm font-semibold mt-0.5">{profile.services.length} services</p>
          </div>
          <div>
            <p className="data-label">Docker Support</p>
            <p className="text-sm font-semibold mt-0.5">
              {profile.containers.detected ? (
                <span className="text-accent-green">✓ Detected</span>
              ) : (
                <span className="text-text-muted">Not Found</span>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-surface-border">
        <nav className="flex gap-4">
          {[
            { id: 'overview', label: 'Overview & Languages' },
            { id: 'frameworks', label: 'Frameworks' },
            { id: 'services', label: 'Services' },
            { id: 'infrastructure', label: 'Infrastructure' },
            { id: 'dependencies', label: 'Dependencies' },
            { id: 'ports', label: 'Ports' },
            { id: 'env', label: 'Environment' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`pb-2 text-xs font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-brand text-text-primary'
                  : 'border-transparent text-text-muted hover:text-text-secondary'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab 1: Overview & Languages */}
      {activeTab === 'overview' && (
        <div className="space-y-6 animate-fade-in">
          {/* Languages card */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold mb-3">Language Distribution</h3>
            {Object.keys(profile.languages.distribution).length === 0 ? (
              <p className="text-xs text-text-muted">No language statistics available.</p>
            ) : (
              <div className="space-y-3">
                {/* Distribution Bar */}
                <div className="w-full h-3 rounded-full overflow-hidden flex bg-surface-overlay border border-surface-border">
                  {Object.entries(profile.languages.distribution).map(([lang, pct], idx) => {
                    const colors = ['bg-brand', 'bg-accent-purple', 'bg-accent-green', 'bg-accent-yellow', 'bg-accent-red'];
                    return (
                      <div
                        key={lang}
                        className={`${colors[idx % colors.length]} h-full`}
                        style={{ width: `${pct}%` }}
                        title={`${lang}: ${pct}%`}
                      />
                    );
                  })}
                </div>

                {/* Legend grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                  {Object.entries(profile.languages.distribution).map(([lang, pct], idx) => {
                    const colors = ['bg-brand', 'bg-accent-purple', 'bg-accent-green', 'bg-accent-yellow', 'bg-accent-red'];
                    return (
                      <div key={lang} className="flex items-center gap-2">
                        <span className={`w-2.5 h-2.5 rounded-full ${colors[idx % colors.length]}`} />
                        <span className="text-xs text-text-secondary">{lang}</span>
                        <span className="text-xs font-mono text-text-muted ml-auto">{pct}%</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* README Summary */}
          {profile.readme_summary && (
            <div className="card p-5">
              <h3 className="text-sm font-semibold mb-2">README Insight</h3>
              <p className="text-xs text-text-secondary leading-relaxed font-mono bg-surface-overlay p-3 rounded-md border border-surface-border whitespace-pre-wrap">
                {profile.readme_summary}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Frameworks */}
      {activeTab === 'frameworks' && (
        <div className="space-y-4 animate-fade-in">
          {profile.frameworks.length === 0 ? (
            <div className="card p-8 text-center text-xs text-text-muted">
              No known framework signatures detected.
            </div>
          ) : (
            profile.frameworks.map((fw) => (
              <div key={fw.name} className="card p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-semibold text-text-primary">{fw.name}</h3>
                  <ConfidenceBadge confidence={fw.confidence} />
                </div>
                <div>
                  <p className="data-label mb-1">Evidence</p>
                  <ul className="space-y-1">
                    {fw.evidence.map((ev, i) => (
                      <li key={i} className="text-xs text-text-secondary flex items-center gap-2">
                        <span className="text-brand-light">•</span>
                        <span>{ev}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Tab 3: Services */}
      {activeTab === 'services' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-fade-in">
          {profile.services.map((svc) => (
            <div key={svc.name} className="card p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Box size={16} className="text-brand-light" />
                  <h3 className="text-sm font-semibold text-text-primary">{svc.name}</h3>
                </div>
                <span className="tag bg-surface-border text-text-secondary capitalize">
                  {svc.type}
                </span>
              </div>

              <dl className="space-y-1.5 text-xs">
                {svc.runtime && (
                  <div className="flex justify-between">
                    <dt className="text-text-muted">Runtime:</dt>
                    <dd className="font-medium text-text-primary capitalize">{svc.runtime}</dd>
                  </div>
                )}
                {svc.port && (
                  <div className="flex justify-between">
                    <dt className="text-text-muted">Port:</dt>
                    <dd className="font-mono text-brand-light">{svc.port}</dd>
                  </div>
                )}
              </dl>

              {svc.evidence.length > 0 && (
                <div className="pt-2 border-t border-surface-border">
                  <p className="text-[11px] text-text-muted mb-1">Evidence:</p>
                  <ul className="space-y-0.5">
                    {svc.evidence.map((ev, i) => (
                      <li key={i} className="text-[11px] text-text-secondary truncate">
                        • {ev}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Tab 4: Infrastructure */}
      {activeTab === 'infrastructure' && (
        <div className="space-y-6 animate-fade-in">
          {/* Databases */}
          <div className="card p-5">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Database size={15} className="text-brand-light" />
              Databases
            </h3>
            {profile.databases.length === 0 ? (
              <p className="text-xs text-text-muted">No databases detected.</p>
            ) : (
              <div className="space-y-3">
                {profile.databases.map((db) => (
                  <div key={db.name} className="p-3 bg-surface-overlay rounded-md border border-surface-border">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-semibold">{db.name}</span>
                      <span className="tag bg-brand/10 text-brand-light">{db.certainty}</span>
                    </div>
                    <p className="text-xs text-text-muted">Evidence: {db.evidence.join(', ')}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Caches & Queues */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="card p-5">
              <h3 className="text-sm font-semibold mb-3">Caches</h3>
              {profile.caches.length === 0 ? (
                <p className="text-xs text-text-muted">No cache servers detected.</p>
              ) : (
                profile.caches.map((c) => (
                  <div key={c.name} className="p-2 bg-surface-overlay rounded mb-2 text-xs">
                    <span className="font-semibold text-text-primary">{c.name}</span>
                    <p className="text-text-muted text-[11px]">{c.evidence.join(', ')}</p>
                  </div>
                ))
              )}
            </div>

            <div className="card p-5">
              <h3 className="text-sm font-semibold mb-3">Message Queues</h3>
              {profile.queues.length === 0 ? (
                <p className="text-xs text-text-muted">No message queues detected.</p>
              ) : (
                profile.queues.map((q) => (
                  <div key={q.name} className="p-2 bg-surface-overlay rounded mb-2 text-xs">
                    <span className="font-semibold text-text-primary">{q.name}</span>
                    <p className="text-text-muted text-[11px]">{q.evidence.join(', ')}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: Dependencies */}
      {activeTab === 'dependencies' && (
        <div className="space-y-4 animate-fade-in">
          {Object.keys(profile.dependencies).length === 0 ? (
            <div className="card p-8 text-center text-xs text-text-muted">
              No dependency manifest files found.
            </div>
          ) : (
            Object.entries(profile.dependencies).map(([manager, pkgs]) => (
              <div key={manager} className="card p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold capitalize text-text-primary">
                    {manager} ({pkgs.length} packages)
                  </h3>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {pkgs.map((pkg) => (
                    <span key={pkg} className="tag bg-surface-overlay text-text-secondary border border-surface-border font-mono text-[11px]">
                      {pkg}
                    </span>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Tab 6: Ports */}
      {activeTab === 'ports' && (
        <div className="card p-5 animate-fade-in">
          <h3 className="text-sm font-semibold mb-3">Detected Application Ports</h3>
          {profile.ports.length === 0 ? (
            <p className="text-xs text-text-muted">No ports explicitly configured or detected.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-surface-border text-text-muted">
                    <th className="py-2 px-3">Port</th>
                    <th className="py-2 px-3">Service</th>
                    <th className="py-2 px-3">Type</th>
                    <th className="py-2 px-3">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.ports.map((p, idx) => (
                    <tr key={idx} className="border-b border-surface-border/50">
                      <td className="py-2.5 px-3 font-mono font-bold text-brand-light">{p.port}</td>
                      <td className="py-2.5 px-3 text-text-primary capitalize">{p.service}</td>
                      <td className="py-2.5 px-3 text-text-muted">{p.port_type}</td>
                      <td className="py-2.5 px-3 text-text-muted font-mono">{p.source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Tab 7: Environment Variables */}
      {activeTab === 'env' && (
        <div className="card p-5 animate-fade-in">
          <h3 className="text-sm font-semibold mb-3">Environment Variable Declarations</h3>
          {profile.environment_variables.length === 0 ? (
            <p className="text-xs text-text-muted">No sample environment files (.env.example) found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-surface-border text-text-muted">
                    <th className="py-2 px-3">Variable Name</th>
                    <th className="py-2 px-3">Security Level</th>
                    <th className="py-2 px-3">Source File</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.environment_variables.map((env, idx) => (
                    <tr key={idx} className="border-b border-surface-border/50">
                      <td className="py-2.5 px-3 font-mono font-semibold text-text-primary">{env.name}</td>
                      <td className="py-2.5 px-3">
                        {env.sensitive ? (
                          <span className="tag bg-accent-red/10 text-accent-red border border-accent-red/20">
                            Sensitive Secret
                          </span>
                        ) : (
                          <span className="tag bg-surface-border text-text-muted">Standard</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-text-muted font-mono">{env.source}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

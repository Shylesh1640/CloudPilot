import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, Play, RefreshCw, ShieldAlert } from 'lucide-react';
import { useParams } from 'react-router-dom';
import { deploymentService } from '@/services/deploymentService';
import { reliabilityService } from '@/services/reliabilityService';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { DeploymentServiceInfo, FailureScenario, IncidentAIAnalysis, IncidentRead, RecoveryEventRead } from '@/types';

const format = (time: string) => new Date(time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

export function ReliabilityPage() {
  const { deploymentId } = useParams<{ deploymentId: string }>();
  const [services, setServices] = useState<DeploymentServiceInfo[]>([]);
  const [incidents, setIncidents] = useState<IncidentRead[]>([]);
  const [selected, setSelected] = useState('');
  const [scenario, setScenario] = useState<FailureScenario>('CONTAINER_STOP');
  const [simulation, setSimulation] = useState(false);
  const [timeline, setTimeline] = useState<RecoveryEventRead[]>([]);
  const [analysis, setAnalysis] = useState<IncidentAIAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');

  const refresh = async () => {
    if (!deploymentId) return;
    const [nextServices, nextIncidents] = await Promise.all([deploymentService.getServices(deploymentId), reliabilityService.incidents(deploymentId)]);
    setServices(nextServices); setIncidents(nextIncidents); if (!selected) setSelected(nextServices[0]?.service_id || '');
    if (nextIncidents[0]) {
      setTimeline(await reliabilityService.timeline(nextIncidents[0].id));
      try { setAnalysis(await reliabilityService.aiAnalysis(nextIncidents[0].id)); }
      catch { setAnalysis(null); }
    } else { setTimeline([]); setAnalysis(null); }
  };
  useEffect(() => { refresh().catch(() => setMessage('Unable to load reliability data.')).finally(() => setLoading(false)); }, [deploymentId]); // eslint-disable-line react-hooks/exhaustive-deps
  const inject = async () => { if (!deploymentId || !selected) return; try { await reliabilityService.inject(deploymentId, { service_id: selected, scenario, duration_seconds: 30, simulation }); setMessage(simulation ? 'Simulation queued. No container will be modified.' : 'Controlled test queued. CloudPilot will detect and evaluate recovery.'); await refresh(); } catch { setMessage('Failure injection was rejected by safety controls.'); } };
  if (loading) return <div className="flex justify-center py-20"><LoadingSpinner /></div>;
  return <div className="p-6 max-w-6xl mx-auto space-y-6 animate-fade-in"><div><h1 className="text-xl font-semibold flex items-center gap-2"><ShieldAlert size={20} className="text-accent-yellow" />Reliability & Self-Healing</h1><p className="text-sm text-text-muted mt-1">Controlled reliability tests, incident history, and explainable recovery actions.</p></div>{message && <div className="card px-4 py-3 text-xs text-text-secondary">{message}</div>}<section className="grid grid-cols-1 lg:grid-cols-2 gap-5"><div className="card p-5 space-y-4"><div className="flex gap-2 items-center"><AlertTriangle size={16} className="text-accent-yellow" /><h2 className="text-sm font-semibold">Failure Injection</h2></div><p className="text-xs text-text-muted">Only active CloudPilot-managed services can be targeted. Real tests never accept an arbitrary container or command.</p><label className="text-xs block">Target service<select value={selected} onChange={(event) => setSelected(event.target.value)} className="mt-1 block w-full bg-surface-overlay border border-surface-border rounded px-2 py-2">{[...new Set(services.map((service) => service.service_id))].map((id) => <option key={id}>{id}</option>)}</select></label><label className="text-xs block">Scenario<select value={scenario} onChange={(event) => setScenario(event.target.value as FailureScenario)} className="mt-1 block w-full bg-surface-overlay border border-surface-border rounded px-2 py-2">{(['CONTAINER_STOP', 'CONTAINER_KILL', 'REPLICA_FAILURE', 'SERVICE_FAILURE', 'HEALTH_CHECK_FAILURE'] as FailureScenario[]).map((item) => <option key={item}>{item.replace(/_/g, ' ')}</option>)}</select></label><label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={simulation} onChange={(event) => setSimulation(event.target.checked)} />Simulation only — no infrastructure changes</label><Button onClick={inject} className="gap-1.5"><Play size={13} />{simulation ? 'Run simulation' : 'Inject controlled failure'}</Button></div><div className="card p-5"><h2 className="text-sm font-semibold flex gap-2 items-center"><Activity size={16} className="text-brand-light" />Active incidents</h2><div className="mt-3 space-y-3">{incidents.slice(0, 6).map((incident) => <div key={incident.id} className="border-l-2 border-accent-red pl-3 text-xs"><div className="flex justify-between"><span className="font-medium">{incident.service_id} · {incident.severity}</span><span>{incident.status}</span></div><p className="text-text-muted mt-1">Root: {incident.root_cause_service_id || 'Investigating'} · {incident.trigger}</p><Button size="sm" variant="secondary" className="mt-2" onClick={() => reliabilityService.recover(incident.id).then(refresh)}>Recover</Button></div>)}{!incidents.length && <p className="text-xs text-text-muted mt-3">No incidents recorded.</p>}</div></div></section>{analysis && <section className="card p-5"><div className="flex justify-between gap-3"><h2 className="text-sm font-semibold">AI Incident Intelligence</h2><span className="text-xs text-text-muted">{analysis.fallback ? 'Deterministic fallback' : analysis.status}</span></div><p className="text-sm mt-3">{analysis.summary}</p><div className="mt-3 text-xs"><p className="font-medium">Evidence</p><ul className="list-disc pl-4 text-text-muted">{analysis.evidence.map((item) => <li key={item}>{item}</li>)}</ul></div>{analysis.recommendations[0] && <div className="mt-3 text-xs border-t border-surface-border pt-3"><p className="font-medium">Safe recommendation</p><p className="text-text-muted">{analysis.recommendations[0].action} → {analysis.recommendations[0].target}: {analysis.recommendations[0].reason}</p></div>}<p className="mt-3 text-[11px] text-text-muted">Recommendations are advisory. Recovery still requires CloudPilot’s deterministic safety validation.</p></section>}<section className="card p-5"><h2 className="text-sm font-semibold flex gap-2 items-center"><RefreshCw size={16} />Recovery timeline</h2><div className="mt-4 space-y-3">{timeline.map((event) => <div className="border-l-2 border-brand pl-3 text-xs" key={event.id}><p className="font-medium">{event.event_type}</p><p className="text-text-muted">{event.message}</p><p className="text-text-muted">{format(event.created_at)}</p></div>)}{!timeline.length && <p className="text-xs text-text-muted">Select or trigger an incident to see the recovery audit trail.</p>}</div></section></div>;
}

import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Activity, ArrowLeft, Minus, Play, Plus, Square } from 'lucide-react';
import { autoscalingService } from '@/services/autoscalingService';
import { deploymentService } from '@/services/deploymentService';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import type { DeploymentServiceInfo, ScalingDecisionRead, ScalingEventRead, ScalingPolicyRead, TrafficRunRead, TrafficScenario } from '@/types';

const formatTime = (value: string) => new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

export function AutoscalingPage() {
  const { deploymentId } = useParams<{ deploymentId: string }>();
  const [services, setServices] = useState<DeploymentServiceInfo[]>([]);
  const [selected, setSelected] = useState('');
  const [policy, setPolicy] = useState<ScalingPolicyRead | null>(null);
  const [decisions, setDecisions] = useState<ScalingDecisionRead[]>([]);
  const [events, setEvents] = useState<ScalingEventRead[]>([]);
  const [runs, setRuns] = useState<TrafficRunRead[]>([]);
  const [replicas, setReplicas] = useState(1);
  const [scenario, setScenario] = useState<TrafficScenario>('constant');
  const [rps, setRps] = useState(20);
  const [duration, setDuration] = useState(60);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const current = useMemo(() => services.filter((service) => service.service_id === selected).length || 1, [services, selected]);
  const refresh = async () => {
    if (!deploymentId) return;
    const [allServices, nextDecisions, nextEvents, nextRuns] = await Promise.all([
      deploymentService.getServices(deploymentId), autoscalingService.decisions(deploymentId), autoscalingService.events(deploymentId), autoscalingService.traffic(deploymentId),
    ]);
    setServices(allServices); setDecisions(nextDecisions); setEvents(nextEvents); setRuns(nextRuns);
    const nextSelected = selected || allServices[0]?.service_id || '';
    setSelected(nextSelected);
    if (nextSelected) setPolicy(await autoscalingService.getPolicy(deploymentId, nextSelected));
  };

  useEffect(() => { refresh().catch(() => setError('Unable to load autoscaling data.')).finally(() => setLoading(false)); }, [deploymentId]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (deploymentId && selected) autoscalingService.getPolicy(deploymentId, selected).then(setPolicy).catch(() => setPolicy(null)); }, [deploymentId, selected]);
  useEffect(() => { if (!policy) return; setReplicas(Math.min(policy.max_replicas, Math.max(policy.min_replicas, current))); }, [policy, current]);

  const scale = async (target: number) => {
    if (!deploymentId || !policy) return;
    try { await autoscalingService.scale(deploymentId, selected, target, policy.dry_run); await refresh(); } catch { setError('Scaling request was rejected by the safety validator.'); }
  };
  const startTraffic = async () => {
    if (!deploymentId || !selected) return;
    try {
      const payload = scenario === 'constant' ? { service_id: selected, scenario, requests_per_second: rps, duration_seconds: duration } : { service_id: selected, scenario, start_rps: Math.max(1, Math.floor(rps / 4)), end_rps: rps, duration_seconds: duration };
      await autoscalingService.startTraffic(deploymentId, payload); await refresh();
    } catch { setError('Traffic test could not be started. Only active CloudPilot-managed public services are eligible.'); }
  };

  if (loading) return <div className="flex justify-center py-20"><LoadingSpinner /></div>;
  if (!deploymentId) return null;
  return <div className="p-6 max-w-6xl mx-auto space-y-6 animate-fade-in">
    <Link to="/projects" className="inline-flex items-center gap-1.5 text-xs text-text-muted hover:text-text-secondary"><ArrowLeft size={12} />Projects</Link>
    <div><h1 className="text-xl font-semibold flex gap-2 items-center"><Activity size={20} className="text-brand-light" />Autoscaling</h1><p className="text-sm text-text-muted mt-1">Deterministic policy decisions, replica controls, and safe managed traffic tests.</p></div>
    {error && <div className="bg-accent-red/10 border border-accent-red/20 rounded-md px-3 py-2 text-xs text-accent-red">{error}</div>}
    {!policy ? <div className="card p-8 text-center text-text-muted text-sm">This deployment has no scalable service selected.</div> : <>
      <section className="card p-5 space-y-5">
        <div className="flex flex-wrap items-start justify-between gap-4"><div><label className="data-label">Service</label><select value={selected} onChange={(event) => setSelected(event.target.value)} className="mt-1 block bg-surface-overlay border border-surface-border rounded px-3 py-2 text-sm"><>{[...new Set(services.map((service) => service.service_id))].map((id) => <option key={id}>{id}</option>)}</></select></div><Button variant={policy.enabled ? 'secondary' : 'primary'} onClick={async () => { const next = await autoscalingService.toggle(deploymentId, selected, !policy.enabled); setPolicy(next); }}>{policy.enabled ? 'Disable autoscaling' : 'Enable autoscaling'}</Button></div>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-sm"><div><p className="data-label">Current</p><p className="font-semibold">{current} replicas</p></div><div><p className="data-label">Desired</p><p className="font-semibold">{replicas} replicas</p></div><div><p className="data-label">Limits</p><p>{policy.min_replicas} – {policy.max_replicas}</p></div><div><p className="data-label">CPU target</p><p>{policy.target_cpu ?? 'Unavailable'}%</p></div><div><p className="data-label">Cooldown</p><p>{policy.cooldown_remaining_seconds ? `${policy.cooldown_remaining_seconds}s remaining` : 'Ready'}</p></div></div>
        <div className="flex items-center gap-3"><Button variant="secondary" onClick={() => scale(replicas - 1)} disabled={replicas <= policy.min_replicas}><Minus size={14} /></Button><input value={replicas} type="number" min={policy.min_replicas} max={policy.max_replicas} onChange={(event) => setReplicas(Number(event.target.value))} className="w-20 bg-surface-overlay border border-surface-border rounded px-2 py-2 text-center text-sm" /><Button variant="secondary" onClick={() => scale(replicas + 1)} disabled={replicas >= policy.max_replicas}><Plus size={14} /></Button><Button onClick={() => scale(replicas)}>Apply {policy.dry_run ? '(dry run)' : ''}</Button></div>
      </section>
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-5"><div className="card p-5 space-y-4"><h2 className="text-sm font-semibold">Traffic Testing</h2><div className="flex gap-2">{(['constant', 'ramp_up', 'ramp_down'] as TrafficScenario[]).map((item) => <button key={item} onClick={() => setScenario(item)} className={`text-xs px-2 py-1 rounded ${scenario === item ? 'bg-brand text-white' : 'bg-surface-overlay text-text-muted'}`}>{item.replace('_', ' ')}</button>)}</div><div className="grid grid-cols-2 gap-3"><label className="text-xs">Peak RPS<input type="number" value={rps} min="1" max="500" onChange={(event) => setRps(Number(event.target.value))} className="mt-1 w-full bg-surface-overlay border border-surface-border rounded px-2 py-2" /></label><label className="text-xs">Duration (s)<input type="number" value={duration} min="1" max="300" onChange={(event) => setDuration(Number(event.target.value))} className="mt-1 w-full bg-surface-overlay border border-surface-border rounded px-2 py-2" /></label></div><Button onClick={startTraffic} className="gap-1.5"><Play size={13} />Start managed test</Button>{runs.slice(0, 2).map((run) => <div key={run.id} className="border-t border-surface-border pt-2 flex justify-between text-xs"><span>{run.scenario} · {run.current_rps.toFixed(0)} RPS · {run.status}</span>{run.status === 'RUNNING' && <button onClick={() => autoscalingService.stopTraffic(run.id).then(refresh)} className="text-accent-red flex items-center gap-1"><Square size={10} />Stop</button>}</div>)}</div>
      <div className="card p-5"><h2 className="text-sm font-semibold mb-3">Scaling Events</h2><div className="space-y-3">{events.slice(0, 8).map((event) => <div key={event.id} className="text-xs border-l-2 border-brand pl-3"><p className="font-medium">{event.event_type}</p><p className="text-text-muted">{event.message}</p><p className="text-text-muted mt-0.5">{formatTime(event.created_at)}</p></div>)}{!events.length && <p className="text-xs text-text-muted">No scaling events yet.</p>}</div></div></section>
      <section className="card p-5"><h2 className="text-sm font-semibold mb-3">Decision history</h2><div className="space-y-2">{decisions.slice(0, 10).map((decision) => <div key={decision.id} className="flex justify-between gap-3 text-xs border-b border-surface-border pb-2"><span className="font-medium">{decision.action}: {decision.current_replicas} → {decision.recommended_replicas}</span><span className="flex-1 text-text-muted">{decision.reason}</span><span className="text-text-muted">{formatTime(decision.created_at)}</span></div>)}{!decisions.length && <p className="text-xs text-text-muted">No evaluations have been recorded yet.</p>}</div></section>
    </>}</div>;
}

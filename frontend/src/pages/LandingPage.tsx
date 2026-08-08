import { Link } from 'react-router-dom';
import {
  GitBranch,
  Brain,
  Activity,
  Zap,
  Shield,
  ArrowRight,
  Terminal,
} from 'lucide-react';

const features = [
  {
    icon: GitBranch,
    title: 'Automated Deployment',
    description:
      'Connect a GitHub repository and CloudPilot handles the rest — from analysis to running containers.',
    phase: 'Phase 2',
  },
  {
    icon: Brain,
    title: 'Infrastructure Intelligence',
    description:
      'AI-powered architecture planning generates an optimal infrastructure topology for your application.',
    phase: 'Phase 3',
  },
  {
    icon: Activity,
    title: 'Real-Time Observability',
    description:
      'Live metrics, request rates, and resource utilization across all your deployed services.',
    phase: 'Phase 6',
  },
  {
    icon: Zap,
    title: 'Autoscaling',
    description:
      'Services scale automatically based on traffic and resource thresholds — no manual intervention.',
    phase: 'Phase 7',
  },
  {
    icon: Shield,
    title: 'Self-Healing',
    description:
      'Failed services are detected and restarted automatically. Chaos engineering tools test resilience.',
    phase: 'Phase 8–9',
  },
  {
    icon: Terminal,
    title: 'AI Root-Cause Analysis',
    description:
      'When something breaks, the AI analyzes metrics, logs, and events to tell you exactly what happened.',
    phase: 'Phase 10',
  },
];

export function LandingPage() {
  return (
    <div className="min-h-screen bg-surface text-text-primary">
      {/* ── Navigation ──────────────────────────────────────────────── */}
      <header className="border-b border-surface-border">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-md bg-brand flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 2L14 5.5V10.5L8 14L2 10.5V5.5L8 2Z" stroke="white" strokeWidth="1.5" strokeLinejoin="round"/>
                <circle cx="8" cy="8" r="2" fill="white"/>
              </svg>
            </div>
            <span className="font-semibold text-sm tracking-tight">CloudPilot</span>
          </div>
          <nav className="flex items-center gap-2">
            <Link
              to="/login"
              id="nav-login"
              className="text-sm text-text-secondary hover:text-text-primary px-3 py-1.5 rounded-md transition-colors"
            >
              Login
            </Link>
            <Link
              to="/register"
              id="nav-get-started"
              className="btn-primary text-sm"
            >
              Get Started
            </Link>
          </nav>
        </div>
      </header>

      {/* ── Hero ────────────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 pt-24 pb-20 text-center">
        <div className="inline-flex items-center gap-2 bg-brand/10 border border-brand/20 rounded-full px-3 py-1 text-xs text-brand-light mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-brand-light animate-pulse-slow" />
          Phase 1 — Foundation
        </div>

        <h1 className="text-5xl font-bold tracking-tight text-text-primary leading-tight mb-5">
          AI-powered deployment and<br />
          <span className="text-brand">self-healing infrastructure</span> platform.
        </h1>

        <p className="text-lg text-text-secondary max-w-2xl mx-auto mb-10">
          CloudPilot analyzes your repository, generates infrastructure, deploys containers,
          monitors in real time, and heals itself automatically.
        </p>

        <div className="flex items-center justify-center gap-3">
          <Link to="/register" id="hero-get-started" className="btn-primary gap-2 text-sm px-5 py-2.5">
            Get Started
            <ArrowRight size={15} />
          </Link>
          <Link to="/login" id="hero-login" className="btn-secondary text-sm px-5 py-2.5">
            Login
          </Link>
        </div>
      </section>

      {/* ── Features ─────────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 pb-24">
        <div className="border-t border-surface-border pt-16">
          <p className="section-header text-center mb-2">Capabilities</p>
          <h2 className="text-2xl font-semibold text-center mb-12">
            Everything you need for production-grade deployments
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <div
                  key={feature.title}
                  className="card p-5 hover:border-surface-border/80 transition-colors group"
                >
                  <div className="flex items-start gap-3 mb-3">
                    <div className="w-8 h-8 rounded-md bg-surface-overlay border border-surface-border flex items-center justify-center flex-shrink-0 group-hover:border-brand/30 transition-colors">
                      <Icon size={15} className="text-text-secondary group-hover:text-brand transition-colors" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-sm font-semibold text-text-primary">{feature.title}</h3>
                        <span className="text-[10px] text-text-muted bg-surface-border rounded px-1.5 py-0.5 flex-shrink-0">
                          {feature.phase}
                        </span>
                      </div>
                    </div>
                  </div>
                  <p className="text-sm text-text-muted leading-relaxed">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="border-t border-surface-border">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between">
          <p className="text-xs text-text-muted">
            © 2026 CloudPilot. Phase 1 — Foundation.
          </p>
          <p className="text-xs text-text-muted">
            Built with FastAPI · React · PostgreSQL · Docker
          </p>
        </div>
      </footer>
    </div>
  );
}

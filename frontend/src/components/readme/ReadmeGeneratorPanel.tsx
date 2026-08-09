import { useState } from 'react';
import { Sparkles, Copy, Download, Check, AlertCircle, FileText, RefreshCw } from 'lucide-react';
import { readmeService } from '@/services/readmeService';
import { getErrorMessage } from '@/services/api';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { Button } from '@/components/ui/Button';

interface Props {
  analysisId: string;
  repoName: string;
}

type GenerateState = 'idle' | 'loading' | 'done' | 'error';

export function ReadmeGeneratorPanel({ analysisId, repoName }: Props) {
  const [state, setState] = useState<GenerateState>('idle');
  const [content, setContent] = useState('');
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const generate = async () => {
    setState('loading');
    setError('');
    try {
      const res = await readmeService.generate(analysisId);
      setContent(res.content);
      setState('done');
    } catch (err) {
      setError(getErrorMessage(err));
      setState('error');
    }
  };

  const copy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const download = () => {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `README-${repoName}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="card p-5 space-y-4 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-md bg-brand/15 border border-brand/30">
            <FileText size={15} className="text-brand-light" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-text-primary">AI README Generator</h3>
            <p className="text-xs text-text-muted">
              Generate a production-quality README.md from the analysis profile
            </p>
          </div>
        </div>

        {state === 'idle' && (
          <Button variant="primary" size="sm" onClick={generate} className="flex items-center gap-2">
            <Sparkles size={13} />
            Generate README
          </Button>
        )}

        {state === 'loading' && (
          <div className="flex items-center gap-2 text-xs text-text-muted">
            <LoadingSpinner size="sm" />
            <span>AI is writing your README…</span>
          </div>
        )}

        {state === 'done' && (
          <div className="flex items-center gap-2">
            <button
              onClick={generate}
              title="Regenerate"
              className="p-1.5 rounded-md text-text-muted hover:text-text-primary hover:bg-surface-overlay transition-all"
            >
              <RefreshCw size={14} />
            </button>
            <button
              onClick={copy}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-surface-overlay border border-surface-border hover:border-brand/40 text-text-secondary hover:text-text-primary transition-all"
            >
              {copied ? <Check size={13} className="text-accent-green" /> : <Copy size={13} />}
              {copied ? 'Copied!' : 'Copy'}
            </button>
            <button
              onClick={download}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-brand/10 border border-brand/30 text-brand-light hover:bg-brand/20 transition-all"
            >
              <Download size={13} />
              Download .md
            </button>
          </div>
        )}

        {state === 'error' && (
          <Button variant="ghost" size="sm" onClick={generate} className="flex items-center gap-1.5">
            <RefreshCw size={13} />
            Retry
          </Button>
        )}
      </div>

      {/* Error */}
      {state === 'error' && (
        <div className="flex items-start gap-2.5 p-3 rounded-md bg-accent-red/10 border border-accent-red/30">
          <AlertCircle size={14} className="text-accent-red mt-0.5 flex-shrink-0" />
          <p className="text-xs text-accent-red">{error}</p>
        </div>
      )}

      {/* Loading placeholder */}
      {state === 'loading' && (
        <div className="space-y-2 animate-pulse">
          {[80, 60, 90, 50, 70, 40, 85, 55].map((w, i) => (
            <div
              key={i}
              className="h-3 rounded bg-surface-overlay"
              style={{ width: `${w}%` }}
            />
          ))}
        </div>
      )}

      {/* Generated README */}
      {state === 'done' && content && (
        <div className="relative">
          {/* Markdown preview — raw code view */}
          <pre className="text-[11.5px] leading-relaxed font-mono text-text-secondary bg-surface-base border border-surface-border rounded-lg p-4 overflow-auto max-h-[520px] whitespace-pre-wrap break-words">
            {content}
          </pre>

          {/* Line count badge */}
          <div className="absolute bottom-2 right-3 text-[10px] text-text-muted bg-surface-base/80 px-1.5 py-0.5 rounded">
            {content.split('\n').length} lines · {(content.length / 1024).toFixed(1)} KB
          </div>
        </div>
      )}

      {/* Idle empty state */}
      {state === 'idle' && (
        <div className="flex flex-col items-center justify-center py-8 gap-3 border border-dashed border-surface-border rounded-lg">
          <div className="p-3 rounded-full bg-brand/10 border border-brand/20">
            <Sparkles size={20} className="text-brand-light" />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-text-primary">Generate README with AI</p>
            <p className="text-xs text-text-muted mt-1 max-w-xs">
              CloudPilot will analyse the detected tech stack, environment variables, and
              architecture to write a complete, production-quality README.md for{' '}
              <span className="text-brand-light font-mono">{repoName}</span>.
            </p>
          </div>
          <button
            onClick={generate}
            className="mt-1 px-4 py-2 rounded-md text-xs font-semibold bg-brand text-white hover:bg-brand/80 transition-all flex items-center gap-2 shadow-lg shadow-brand/20"
          >
            <Sparkles size={13} />
            Generate with OpenRouter AI
          </button>
        </div>
      )}
    </div>
  );
}

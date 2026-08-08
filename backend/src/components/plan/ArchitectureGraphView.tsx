import { useState } from 'react';
import { Box, Database, Cpu, Layers, Globe, Shield, ZoomIn, ZoomOut, RefreshCw } from 'lucide-react';
import type { ArchitectureGraph, GraphNode, ServiceDefinition } from '@/types';

interface Props {
  graph: ArchitectureGraph;
  services: ServiceDefinition[];
  selectedServiceId: string | null;
  onSelectService: (serviceId: string) => void;
}

const SERVICE_TYPE_COLORS: Record<string, { bg: string; text: string; border: string; icon: any }> = {
  application: { bg: 'bg-brand/10', text: 'text-brand-light', border: 'border-brand/30', icon: Layers },
  worker: { bg: 'bg-accent-yellow/10', text: 'text-accent-yellow', border: 'border-accent-yellow/30', icon: Cpu },
  database: { bg: 'bg-accent-purple/10', text: 'text-accent-purple', border: 'border-accent-purple/30', icon: Database },
  cache: { bg: 'bg-accent-green/10', text: 'text-accent-green', border: 'border-accent-green/30', icon: Box },
  queue: { bg: 'bg-accent-yellow/10', text: 'text-accent-yellow', border: 'border-accent-yellow/30', icon: Cpu },
};

export function ArchitectureGraphView({ graph, services, selectedServiceId, onSelectService }: Props) {
  const [zoom, setZoom] = useState(1);

  // Position nodes in horizontal ranks based on dependencies (Topological layout)
  const nodes = graph.nodes;
  const edges = graph.edges;

  // Group nodes into columns: Public App → Worker/Internal App → Databases/Caches
  const columns: { [col: number]: GraphNode[] } = { 0: [], 1: [], 2: [] };

  nodes.forEach((node) => {
    if (node.public || node.id.includes('front') || node.id.includes('ui')) {
      columns[0].push(node);
    } else if (node.type === 'database' || node.type === 'cache') {
      columns[2].push(node);
    } else {
      columns[1].push(node);
    }
  });

  // Re-balance if empty
  if (columns[0].length === 0 && columns[1].length > 0) {
    columns[0].push(columns[1].shift()!);
  }

  const nodePositions: Record<string, { x: number; y: number }> = {};
  const width = 800;
  const height = 360;

  [0, 1, 2].forEach((colIdx) => {
    const colNodes = columns[colIdx] || [];
    const x = 120 + colIdx * 280;
    colNodes.forEach((node, rowIdx) => {
      const totalInCol = colNodes.length;
      const y = (height / (totalInCol + 1)) * (rowIdx + 1);
      nodePositions[node.id] = { x, y };
    });
  });

  return (
    <div className="card p-5 relative overflow-hidden bg-surface-base border-surface-border">
      {/* Header & Zoom Controls */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-surface-border">
        <div>
          <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
            <Layers size={16} className="text-brand-light" />
            Infrastructure Topology Graph
          </h3>
          <p className="text-xs text-text-muted">Click any node to inspect service configuration & health rules.</p>
        </div>
        <div className="flex items-center gap-1.5 bg-surface-overlay p-1 rounded-md border border-surface-border">
          <button
            onClick={() => setZoom((z) => Math.max(0.7, z - 0.1))}
            className="p-1 text-text-muted hover:text-text-primary rounded transition-colors"
            title="Zoom Out"
          >
            <ZoomOut size={14} />
          </button>
          <span className="text-[11px] font-mono px-1.5 text-text-secondary">{Math.round(zoom * 100)}%</span>
          <button
            onClick={() => setZoom((z) => Math.min(1.4, z + 0.1))}
            className="p-1 text-text-muted hover:text-text-primary rounded transition-colors"
            title="Zoom In"
          >
            <ZoomIn size={14} />
          </button>
          <button
            onClick={() => setZoom(1)}
            className="p-1 text-text-muted hover:text-text-primary rounded transition-colors"
            title="Reset Zoom"
          >
            <RefreshCw size={12} />
          </button>
        </div>
      </div>

      {/* SVG Canvas Container */}
      <div className="relative w-full h-[360px] overflow-auto flex items-center justify-center bg-surface-base rounded-md border border-surface-border/50">
        <div
          className="transition-transform duration-200 ease-out origin-center"
          style={{ transform: `scale(${zoom})`, width: `${width}px`, height: `${height}px` }}
        >
          <svg className="w-full h-full absolute inset-0 pointer-events-none">
            <defs>
              <marker
                id="arrowhead"
                markerWidth="8"
                markerHeight="6"
                refX="6"
                refY="3"
                orient="auto"
              >
                <polygon points="0 0, 8 3, 0 6" fill="var(--brand-light, #6366f1)" opacity="0.6" />
              </marker>
            </defs>

            {/* Edge Connecting Lines */}
            {edges.map((edge) => {
              const src = nodePositions[edge.source];
              const tgt = nodePositions[edge.target];
              if (!src || !tgt) return null;

              // Curved cubic bezier paths between ranks
              const dx = tgt.x - src.x;
              const ctrl1X = src.x + dx * 0.5;
              const ctrl2X = tgt.x - dx * 0.5;
              const pathD = `M ${src.x + 75} ${src.y} C ${ctrl1X} ${src.y}, ${ctrl2X} ${tgt.y}, ${tgt.x - 75} ${tgt.y}`;

              return (
                <g key={`${edge.source}-${edge.target}`}>
                  <path
                    d={pathD}
                    fill="none"
                    stroke="#475569"
                    strokeWidth="1.5"
                    strokeDasharray="4 4"
                    markerEnd="url(#arrowhead)"
                  />
                  <text
                    x={(src.x + tgt.x) / 2}
                    y={(src.y + tgt.y) / 2 - 8}
                    fill="#94a3b8"
                    fontSize="10"
                    fontFamily="monospace"
                    textAnchor="middle"
                  >
                    {edge.label}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Render Graph Nodes */}
          {nodes.map((node) => {
            const pos = nodePositions[node.id] || { x: 400, y: 180 };
            const isSelected = selectedServiceId === node.id;
            const style = SERVICE_TYPE_COLORS[node.type.toLowerCase()] || SERVICE_TYPE_COLORS.application;
            const Icon = style.icon;

            return (
              <button
                key={node.id}
                onClick={() => onSelectService(node.id)}
                style={{ left: `${pos.x - 75}px`, top: `${pos.y - 32}px` }}
                className={`
                  absolute w-[150px] p-3 rounded-lg border text-left transition-all duration-150 shadow-md cursor-pointer
                  ${style.bg} ${style.border}
                  ${isSelected ? 'ring-2 ring-brand ring-offset-2 ring-offset-surface-base scale-105 z-10' : 'hover:scale-102 hover:shadow-lg'}
                `}
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-1.5 truncate">
                    <Icon size={14} className={style.text} />
                    <span className="text-xs font-semibold text-text-primary truncate">{node.label}</span>
                  </div>
                  {node.public && (
                    <span className="tag bg-accent-green/20 text-accent-green text-[9px] px-1 py-0.2" title="Public Entrypoint">
                      <Globe size={10} />
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between text-[10px] text-text-muted mt-1.5">
                  <span className="capitalize">{node.type}</span>
                  {node.replicas > 1 && (
                    <span className="font-mono bg-surface-overlay border border-surface-border rounded px-1">
                      {node.replicas}x
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

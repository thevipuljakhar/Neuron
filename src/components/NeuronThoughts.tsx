/**
 * NeuronThoughts.tsx
 * UI window into Neuron's autonomous thinking — reads thoughts, curiosities,
 * and resolved insights from the curiosity_engine endpoints.
 *
 * Endpoints (served by Flask / neuron.py — no auth required):
 *   GET /api/thoughts/today  → v24_thoughts
 *   GET /api/curiosities     → v24_curiosities
 *   GET /api/insights        → v24_insights
 *
 * Rules:
 *  - No Tailwind, no new npm packages, no styled-components.
 *  - Only CSS variables from index.css (mapped from neuron19 naming).
 *  - Each panel fetches independently; one failure never breaks the others.
 *  - Graceful degradation: endpoint error → quiet "thinking…" message.
 */

import React, { useEffect, useState, useCallback } from 'react';

// ── Types ─────────────────────────────────────────────────────────────────────

interface Thought {
  id?: number;
  thought: string;
  surprise_level?: number;       // 0.0 – 1.0
  timestamp?: string;
  created_at?: string;
}

interface Curiosity {
  id?: number;
  question: string;
  status?: 'SEARCHING' | 'OPEN' | 'RESOLVED' | string;
  priority?: number;             // 1 (high) – 5 (low)
  created_at?: string;
}

interface Insight {
  id?: number;
  question?: string;
  reasoning?: string;
  confidence?: number;           // 0–100
  sub_questions?: string[];
  created_at?: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function timeAgo(iso?: string): string {
  if (!iso) return '';
  try {
    const delta = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
    if (delta < 60)  return `${delta}s ago`;
    if (delta < 3600) return `${Math.floor(delta / 60)}m ago`;
    if (delta < 86400) return `${Math.floor(delta / 3600)}h ago`;
    return `${Math.floor(delta / 86400)}d ago`;
  } catch {
    return '';
  }
}

function surpriseGlow(level?: number): React.CSSProperties {
  if (!level || level < 0.6) return {};
  const alpha = Math.min(0.6, (level - 0.6) * 1.5);
  return {
    boxShadow: `0 0 0 1px rgba(234, 179, 8, ${alpha}), 0 0 12px rgba(234, 179, 8, ${alpha * 0.5})`,
    borderColor: `rgba(234, 179, 8, ${alpha + 0.1})`,
  };
}

function statusColor(status?: string): string {
  switch ((status || '').toUpperCase()) {
    case 'SEARCHING': return 'var(--accent-energy)';
    case 'RESOLVED':  return 'var(--accent-renewable)';
    default:          return 'var(--text-muted)';
  }
}

function priorityDots(priority?: number): string {
  const p = priority ?? 3;
  return '●'.repeat(Math.max(1, Math.min(5, 6 - p))) + '○'.repeat(Math.min(4, p - 1));
}

// ── Shared card style ─────────────────────────────────────────────────────────

const ITEM_BASE: React.CSSProperties = {
  padding: '10px 12px',
  borderRadius: '8px',
  border: '1px solid var(--border-color)',
  background: 'var(--bg-primary)',
  transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
  marginBottom: '8px',
};

const EMPTY_MSG: React.CSSProperties = {
  fontSize: '12px',
  color: 'var(--text-muted)',
  fontStyle: 'italic',
  padding: '16px 0',
  textAlign: 'center',
};

const PANEL: React.CSSProperties = {
  background: 'var(--bg-secondary)',
  border: '1px solid var(--border-color)',
  borderRadius: '8px',
  boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
  overflow: 'hidden',
  display: 'flex',
  flexDirection: 'column',
};

const PANEL_HEADER: React.CSSProperties = {
  padding: '11px 16px',
  borderBottom: '1px solid var(--border-color)',
  background: 'rgba(0,0,0,0.06)',
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
};

const PANEL_TITLE: React.CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontSize: '13px',
  fontWeight: 600,
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
  color: 'var(--text-primary)',
  display: 'flex',
  alignItems: 'center',
  gap: '7px',
};

const PANEL_BODY: React.CSSProperties = {
  padding: '14px 16px',
  overflowY: 'auto',
  maxHeight: '280px',
  flex: 1,
};

// ── Panel 1 — Thoughts ────────────────────────────────────────────────────────

const ThoughtsPanel: React.FC = () => {
  const [thoughts, setThoughts] = useState<Thought[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await fetch('/api/thoughts/today');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setThoughts(Array.isArray(data) ? data : (data.thoughts ?? []));
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div style={PANEL}>
      <div style={PANEL_HEADER}>
        <span style={PANEL_TITLE}>🧠 Neuron's Observations</span>
        <button
          onClick={load}
          title="Refresh"
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-muted)', fontSize: '14px', lineHeight: 1,
            padding: '2px 6px', borderRadius: '4px',
            transition: 'color 0.2s',
          }}
          aria-label="Refresh thoughts"
        >↻</button>
      </div>

      <div style={PANEL_BODY}>
        {loading && (
          <div style={EMPTY_MSG}>Neuron is warming up its mind…</div>
        )}
        {!loading && error && (
          <div style={EMPTY_MSG}>Neuron is thinking…</div>
        )}
        {!loading && !error && thoughts.length === 0 && (
          <div style={EMPTY_MSG}>Neuron is warming up its mind…</div>
        )}
        {!loading && !error && thoughts.map((t, i) => (
          <div
            key={t.id ?? i}
            style={{ ...ITEM_BASE, ...surpriseGlow(t.surprise_level) }}
          >
            <div style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: 1.5, marginBottom: '6px' }}>
              {t.thought}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              {typeof t.surprise_level === 'number' && (
                <span style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '10px',
                  color: t.surprise_level > 0.6 ? 'var(--accent-energy)' : 'var(--text-muted)',
                  fontWeight: 600,
                }}>
                  ⚡ {Math.round(t.surprise_level * 100)}% surprise
                </span>
              )}
              <span style={{
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '10px',
                color: 'var(--text-muted)',
                marginLeft: 'auto',
              }}>
                {timeAgo(t.timestamp ?? t.created_at)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ── Panel 2 — Curiosities ─────────────────────────────────────────────────────

const CuriositiesPanel: React.FC = () => {
  const [curiosities, setCuriosities] = useState<Curiosity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await fetch('/api/curiosities');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setCuriosities(Array.isArray(data) ? data : (data.curiosities ?? []));
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div style={PANEL}>
      <div style={PANEL_HEADER}>
        <span style={PANEL_TITLE}>🔍 Open Questions</span>
        <button
          onClick={load}
          title="Refresh"
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-muted)', fontSize: '14px', lineHeight: 1,
            padding: '2px 6px', borderRadius: '4px',
            transition: 'color 0.2s',
          }}
          aria-label="Refresh curiosities"
        >↻</button>
      </div>

      <div style={PANEL_BODY}>
        {loading && (
          <div style={EMPTY_MSG}>Neuron is thinking…</div>
        )}
        {!loading && error && (
          <div style={EMPTY_MSG}>Neuron is thinking…</div>
        )}
        {!loading && !error && curiosities.length === 0 && (
          <div style={EMPTY_MSG}>
            No open questions — Neuron is content with what it knows for now
          </div>
        )}
        {!loading && !error && curiosities.map((c, i) => (
          <div key={c.id ?? i} style={ITEM_BASE}>
            <div style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: 1.5, marginBottom: '7px' }}>
              {c.question}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {/* Status badge */}
              <span style={{
                padding: '1px 7px',
                borderRadius: '4px',
                fontSize: '10px',
                fontWeight: 700,
                fontFamily: 'JetBrains Mono, monospace',
                textTransform: 'uppercase' as const,
                color: statusColor(c.status),
                background: 'rgba(255,255,255,0.04)',
                border: `1px solid ${statusColor(c.status)}44`,
              }}>
                {c.status ?? 'OPEN'}
              </span>
              {/* Priority dots */}
              {c.priority != null && (
                <span style={{
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: '10px',
                  color: c.priority <= 2 ? 'var(--accent-energy)' : 'var(--text-muted)',
                  letterSpacing: '1px',
                }}>
                  {priorityDots(c.priority)}
                </span>
              )}
              <span style={{
                marginLeft: 'auto',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '10px',
                color: 'var(--text-muted)',
              }}>
                {timeAgo(c.created_at)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// ── Panel 3 — Insights ────────────────────────────────────────────────────────

const InsightsPanel: React.FC = () => {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(false);
      const res = await fetch('/api/insights');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setInsights(Array.isArray(data) ? data : (data.insights ?? []));
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div style={PANEL}>
      <div style={PANEL_HEADER}>
        <span style={PANEL_TITLE}>💡 Insights</span>
        <button
          onClick={load}
          title="Refresh"
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-muted)', fontSize: '14px', lineHeight: 1,
            padding: '2px 6px', borderRadius: '4px',
            transition: 'color 0.2s',
          }}
          aria-label="Refresh insights"
        >↻</button>
      </div>

      <div style={PANEL_BODY}>
        {loading && (
          <div style={EMPTY_MSG}>Neuron is thinking…</div>
        )}
        {!loading && error && (
          <div style={EMPTY_MSG}>Neuron is thinking…</div>
        )}
        {!loading && !error && insights.length === 0 && (
          <div style={EMPTY_MSG}>
            No insights yet — check back after the next thinking cycle
          </div>
        )}
        {!loading && !error && insights.map((ins, i) => {
          const confidence = typeof ins.confidence === 'number' ? ins.confidence : null;
          const reasoning  = (ins.reasoning ?? '').slice(0, 200);
          const subs       = Array.isArray(ins.sub_questions) ? ins.sub_questions : [];

          return (
            <div key={ins.id ?? i} style={ITEM_BASE}>
              {/* Spark question */}
              {ins.question && (
                <div style={{
                  fontSize: '10px',
                  fontFamily: 'JetBrains Mono, monospace',
                  color: 'var(--text-muted)',
                  marginBottom: '5px',
                  textTransform: 'uppercase' as const,
                  letterSpacing: '0.5px',
                }}>
                  Q: {ins.question}
                </div>
              )}

              {/* Reasoning summary */}
              {reasoning && (
                <div style={{
                  fontSize: '13px',
                  color: 'var(--text-primary)',
                  lineHeight: 1.5,
                  marginBottom: '8px',
                }}>
                  {reasoning}{ins.reasoning && ins.reasoning.length > 200 ? '…' : ''}
                </div>
              )}

              {/* Confidence bar */}
              {confidence !== null && (
                <div style={{ marginBottom: subs.length ? '8px' : '0' }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontSize: '10px',
                    color: 'var(--text-muted)',
                    marginBottom: '3px',
                    fontFamily: 'JetBrains Mono, monospace',
                  }}>
                    <span>Confidence</span>
                    <span style={{ color: confidence >= 70 ? 'var(--accent-renewable)' : 'var(--accent-energy)' }}>
                      {Math.round(confidence)}%
                    </span>
                  </div>
                  <div style={{
                    height: '3px',
                    borderRadius: '2px',
                    background: 'var(--bg-secondary)',
                    overflow: 'hidden',
                  }}>
                    <div style={{
                      height: '100%',
                      width: `${Math.min(100, Math.max(0, confidence))}%`,
                      background: confidence >= 70
                        ? 'var(--accent-renewable)'
                        : confidence >= 40
                          ? 'var(--accent-energy)'
                          : '#ef4444',
                      transition: 'width 0.5s ease',
                      borderRadius: '2px',
                    }} />
                  </div>
                </div>
              )}

              {/* Sub-questions */}
              {subs.length > 0 && (
                <div style={{ marginTop: '6px' }}>
                  <div style={{
                    fontSize: '10px',
                    color: 'var(--text-muted)',
                    fontFamily: 'JetBrains Mono, monospace',
                    marginBottom: '4px',
                    textTransform: 'uppercase' as const,
                    letterSpacing: '0.5px',
                  }}>
                    Still wondering:
                  </div>
                  {subs.map((sq, si) => (
                    <div key={si} style={{
                      fontSize: '11px',
                      color: 'var(--text-secondary)',
                      lineHeight: 1.4,
                      paddingLeft: '10px',
                      borderLeft: '2px solid var(--border-color)',
                      marginBottom: '3px',
                    }}>
                      {sq}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ── Root component ────────────────────────────────────────────────────────────

const NeuronThoughts: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', width: '100%' }}>
      {/* Section header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        paddingBottom: '4px',
        borderBottom: '1px solid var(--border-color)',
      }}>
        <span style={{
          fontFamily: 'var(--font-display)',
          fontSize: '12px',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '1px',
          color: 'var(--text-muted)',
        }}>
          Neuron's Inner Monologue
        </span>
        <span style={{
          fontSize: '10px',
          fontFamily: 'JetBrains Mono, monospace',
          color: 'var(--text-muted)',
          background: 'var(--bg-secondary)',
          padding: '2px 6px',
          borderRadius: '4px',
          border: '1px solid var(--border-color)',
        }}>
          live · auto-connects when curiosity_engine goes live
        </span>
      </div>

      {/* Three independent panels */}
      <ThoughtsPanel />
      <CuriositiesPanel />
      <InsightsPanel />
    </div>
  );
};

export default NeuronThoughts;

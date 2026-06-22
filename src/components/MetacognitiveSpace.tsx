import React, { useState, useEffect } from 'react';
import { ShieldCheck, ShieldAlert, KeyRound, Play, RefreshCw, Send, Search, PlusCircle } from 'lucide-react';

interface SwotData {
  swot_date: string;
  ts: number;
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
  upgrades: string[];
  emailed: number;
}

interface SelfTestCheck {
  name: string;
  status: 'pass' | 'fail' | 'warn';
  detail: string;
}

interface SelfTestData {
  checks: SelfTestCheck[];
  passed: number;
  failed: number;
  warned: number;
  verdict: string;
  generated_at: string;
}

interface RecallResult {
  text: string;
  source_id: string;
  score: number;
}

export const MetacognitiveSpace: React.FC = () => {
  const [password, setPassword] = useState('');
  const [isUnlocked, setIsUnlocked] = useState(false);
  const [passwordError, setPasswordError] = useState(false);

  // SWOT States
  const [swot, setSwot] = useState<SwotData | null>(null);
  const [swotLoading, setSwotLoading] = useState(false);

  // Self Test States
  const [selfTest, setSelfTest] = useState<SelfTestData | null>(null);
  const [testLoading, setTestLoading] = useState(false);

  // Memory Recall States
  const [searchQuery, setSearchQuery] = useState('');
  const [recallResults, setRecallResults] = useState<RecallResult[]>([]);
  const [recallLoading, setRecallLoading] = useState(false);

  // Add Fact States
  const [newFact, setNewFact] = useState('');
  const [addFactSuccess, setAddFactSuccess] = useState(false);

  // Password verification — delegated to backend (never checks key client-side)
  const handleUnlock = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/brain/health', {
        headers: { 'X-Neuron-Key': password }
      });
      if (res.ok) {
        setIsUnlocked(true);
        setPasswordError(false);
        loadSwot();
        loadSelfTest();
      } else {
        setPasswordError(true);
        setIsUnlocked(false);
      }
    } catch {
      setPasswordError(true);
      setIsUnlocked(false);
    }
  };

  const loadSwot = async () => {
    try {
      setSwotLoading(true);
      const res = await fetch('/api/swot').then(r => r.json());
      setSwot(res);
    } catch (e) {
      console.error(e);
    } finally {
      setSwotLoading(false);
    }
  };

  const triggerSwotRun = async () => {
    try {
      setSwotLoading(true);
      const res = await fetch('/api/swot/run', { method: 'POST' }).then(r => r.json());
      setSwot(res);
    } catch (e) {
      console.error(e);
    } finally {
      setSwotLoading(false);
    }
  };

  const loadSelfTest = async () => {
    try {
      setTestLoading(true);
      const res = await fetch('/api/self_test').then(r => r.json());
      setSelfTest(res);
    } catch (e) {
      console.error(e);
    } finally {
      setTestLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    try {
      setRecallLoading(true);
      const res = await fetch(`/api/memory/recall?q=${encodeURIComponent(searchQuery)}&k=5`).then(r => r.json());
      setRecallResults(res.results || []);
    } catch (e) {
      console.error(e);
    } finally {
      setRecallLoading(false);
    }
  };

  const handleAddFact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFact.trim()) return;
    try {
      await fetch('/api/memory/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: newFact, scope: 'neuron' })
      });
      setNewFact('');
      setAddFactSuccess(true);
      setTimeout(() => setAddFactSuccess(false), 3000);
      loadSelfTest(); // reload stats
    } catch (e) {
      console.error(e);
    }
  };

  if (!isUnlocked) {
    return (
      <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <form onSubmit={handleUnlock} className="panel-card" style={{ padding: '24px', width: '380px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px' }}>
            <KeyRound size={20} style={{ color: 'var(--accent-energy)' }} />
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 'bold' }}>METACOGNITIVE ACCESS REQUIRED</h3>
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '11px', color: 'var(--text-secondary)', fontWeight: 'bold', textTransform: 'uppercase' }}>Secure Core Key</label>
            <input
              type="password"
              placeholder="Enter secure credentials..."
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '6px',
                border: passwordError ? '1px solid #ef4444' : '1px solid var(--border-color)',
                background: 'var(--bg-primary)',
                color: 'var(--text-primary)',
                fontSize: '14px',
                outline: 'none'
              }}
            />
            {passwordError && (
              <span style={{ fontSize: '11px', color: '#ef4444', fontWeight: '600' }}>Authentication failed: Invalid secure key.</span>
            )}
          </div>

          <button
            type="submit"
            style={{
              padding: '10px',
              borderRadius: '6px',
              border: 'none',
              backgroundColor: 'var(--accent-energy)',
              color: '#000',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px'
            }}
          >
            Unlock Core Space
          </button>
        </form>
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', width: '100%', flex: 1 }}>
      
      {/* Left Column: SWOT Analysis */}
      <div className="panel-card" style={{ display: 'flex', flexDirection: 'column' }}>
        <div className="panel-header">
          <h3 className="panel-title">
            <ShieldCheck size={16} style={{ color: 'var(--accent-renewable)' }} />
            Autonomous SWOT Self-Analysis
          </h3>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={triggerSwotRun}
              disabled={swotLoading}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '11px'
              }}
            >
              <RefreshCw size={12} className={swotLoading ? 'spin-icon' : ''} />
              Re-analyse
            </button>
          </div>
        </div>

        <div className="panel-content" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {swotLoading && !swot ? (
            <div>Computing self SWOT matrix...</div>
          ) : (
            swot && (
              <>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div style={{ backgroundColor: 'rgba(34, 197, 94, 0.04)', border: '1px solid rgba(34, 197, 94, 0.1)', padding: '12px', borderRadius: '8px' }}>
                    <h4 style={{ fontSize: '11px', color: 'var(--accent-renewable)', fontWeight: 'bold', marginBottom: '6px', textTransform: 'uppercase' }}>Strengths</h4>
                    <ul style={{ paddingLeft: '14px', fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                      {swot.strengths.map((s, i) => <li key={i} style={{ marginBottom: '4px' }}>{s}</li>)}
                    </ul>
                  </div>

                  <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.04)', border: '1px solid rgba(239, 68, 68, 0.1)', padding: '12px', borderRadius: '8px' }}>
                    <h4 style={{ fontSize: '11px', color: '#ef4444', fontWeight: 'bold', marginBottom: '6px', textTransform: 'uppercase' }}>Weaknesses</h4>
                    <ul style={{ paddingLeft: '14px', fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                      {swot.weaknesses.map((w, i) => <li key={i} style={{ marginBottom: '4px' }}>{w}</li>)}
                    </ul>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div style={{ backgroundColor: 'rgba(59, 130, 246, 0.04)', border: '1px solid rgba(59, 130, 246, 0.1)', padding: '12px', borderRadius: '8px' }}>
                    <h4 style={{ fontSize: '11px', color: 'var(--accent-us)', fontWeight: 'bold', marginBottom: '6px', textTransform: 'uppercase' }}>Opportunities</h4>
                    <ul style={{ paddingLeft: '14px', fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                      {swot.opportunities.map((o, i) => <li key={i} style={{ marginBottom: '4px' }}>{o}</li>)}
                    </ul>
                  </div>

                  <div style={{ backgroundColor: 'rgba(249, 115, 22, 0.04)', border: '1px solid rgba(249, 115, 22, 0.1)', padding: '12px', borderRadius: '8px' }}>
                    <h4 style={{ fontSize: '11px', color: 'var(--accent-india)', fontWeight: 'bold', marginBottom: '6px', textTransform: 'uppercase' }}>Threats</h4>
                    <ul style={{ paddingLeft: '14px', fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                      {swot.threats.map((t, i) => <li key={i} style={{ marginBottom: '4px' }}>{t}</li>)}
                    </ul>
                  </div>
                </div>

                <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '12px' }}>
                  <h4 style={{ fontSize: '11px', color: 'var(--accent-energy)', fontWeight: 'bold', marginBottom: '6px', textTransform: 'uppercase' }}>Recommended Upgrades Checklist</h4>
                  <ul style={{ paddingLeft: '14px', fontSize: '11px', color: 'var(--text-primary)', lineHeight: '1.4' }}>
                    {swot.upgrades.map((u, i) => <li key={i} style={{ marginBottom: '4px' }}>{u}</li>)}
                  </ul>
                </div>

                <div style={{ display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', color: 'var(--text-muted)' }}>
                  <span>Emailed: {swot.emailed ? 'Yes (sent to thevipuljakhar@gmail.com)' : 'No (SMTP unconfigured)'}</span>
                  <span>As of: {swot.swot_date}</span>
                </div>
              </>
            )
          )}
        </div>
      </div>

      {/* Right Column: Invariant Self-Test & Telemetry */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        
        {/* Diagnostics Card */}
        <div className="panel-card" style={{ flex: 1 }}>
          <div className="panel-header">
            <h3 className="panel-title">
              <ShieldAlert size={16} style={{ color: 'var(--accent-india)' }} />
              Nervous System Diagnostics & Invariants
            </h3>
            <button
              onClick={loadSelfTest}
              disabled={testLoading}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '11px'
              }}
            >
              <Play size={12} />
              Run Self-Test
            </button>
          </div>

          <div className="panel-content" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {testLoading && !selfTest ? (
              <div>Running invariant test suites...</div>
            ) : (
              selfTest && (
                <>
                  <div style={{ display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontSize: '12px', fontWeight: 'bold' }}>SYSTEM HEALTH VERDICT</span>
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: '700',
                      backgroundColor: selfTest.verdict === 'GREEN' ? 'rgba(34, 197, 94, 0.12)' : 'rgba(239, 68, 68, 0.12)',
                      color: selfTest.verdict === 'GREEN' ? 'var(--accent-renewable)' : '#ef4444'
                    }}>{selfTest.verdict}</span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '160px', overflowY: 'auto' }}>
                    {selfTest.checks.map((c, i) => (
                      <div key={i} style={{ display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between', fontSize: '11px', padding: '4px 0', borderBottom: '1px solid var(--border-color)' }}>
                        <span style={{ color: 'var(--text-primary)' }}>{c.name}</span>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <span style={{ color: 'var(--text-secondary)' }}>{c.detail}</span>
                          <span style={{
                            color: c.status === 'pass' ? 'var(--accent-renewable)' : c.status === 'warn' ? 'var(--accent-energy)' : '#ef4444',
                            fontWeight: 'bold'
                          }}>{c.status.toUpperCase()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )
            )}
          </div>
        </div>

        {/* Memory Injector Desk */}
        <div className="panel-card">
          <div className="panel-header">
            <h3 className="panel-title">
              <PlusCircle size={16} style={{ color: 'var(--accent-us)' }} />
              Teach Neuron Fact
            </h3>
          </div>
          <div className="panel-content">
            <form onSubmit={handleAddFact} style={{ display: 'flex', gap: '8px' }}>
              <input
                type="text"
                placeholder="Teach Neuron a new fact (retained permanently)..."
                value={newFact}
                onChange={(e) => setNewFact(e.target.value)}
                style={{
                  flex: 1,
                  padding: '8px 12px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-primary)',
                  color: 'var(--text-primary)',
                  fontSize: '12px',
                  outline: 'none'
                }}
              />
              <button
                type="submit"
                style={{
                  padding: '8px 16px',
                  borderRadius: '6px',
                  border: 'none',
                  backgroundColor: 'var(--accent-us)',
                  color: '#fff',
                  fontWeight: '600',
                  fontSize: '12px',
                  cursor: 'pointer'
                }}
              >
                Inject
              </button>
            </form>
            {addFactSuccess && (
              <div style={{ fontSize: '11px', color: 'var(--accent-renewable)', marginTop: '6px', fontWeight: 'bold' }}>Fact injected successfully into MemoryOS.</div>
            )}
          </div>
        </div>

      </div>

      {/* Bottom Recall Console spanning full width */}
      <div className="panel-card" style={{ gridColumn: 'span 2', display: 'flex', flexDirection: 'column', minHeight: '180px' }}>
        <div className="panel-header">
          <h3 className="panel-title">
            <Search size={16} style={{ color: 'var(--accent-energy)' }} />
            Memory Recall Console (SQLite & Vector KNN)
          </h3>
        </div>

        <div className="panel-content" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <form onSubmit={handleSearch} style={{ display: 'flex', position: 'relative', alignItems: 'center' }}>
            <Search size={14} style={{ position: 'absolute', left: '10px', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Query vector database and temporal memory registry..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px 8px 30px',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-primary)',
                color: 'var(--text-primary)',
                fontSize: '13px',
                outline: 'none'
              }}
            />
          </form>

          <div style={{ flex: 1, maxHeight: '180px', overflowY: 'auto' }}>
            {recallLoading ? (
              <div>Searching MemoryOS vectors...</div>
            ) : (
              recallResults.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {recallResults.map((r, i) => (
                    <div key={i} style={{ padding: '8px', backgroundColor: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: '6px', display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '12px', color: 'var(--text-primary)', lineHeight: '1.4' }}>{r.text}</span>
                      <div style={{ display: 'flex', gap: '8px', fontSize: '10px', fontWeight: 'bold' }}>
                        <span style={{ padding: '2px 6px', borderRadius: '4px', backgroundColor: 'var(--bg-tertiary)', color: 'var(--text-secondary)' }}>{r.source_id}</span>
                        <span style={{ color: 'var(--accent-energy)' }}>KNN: {r.score}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                searchQuery && <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>No facts recalled for this query.</div>
              )
            )}
          </div>
        </div>
      </div>

    </div>
  );
};

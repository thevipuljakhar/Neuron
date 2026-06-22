import { useState, useEffect } from 'react';
import { Sun, Moon, Globe, Zap } from 'lucide-react';
import { EnergyMap } from './components/EnergyMap';
import { LiveNews } from './components/LiveNews';
import { GridStatus } from './components/GridStatus';
import { EnergyMix } from './components/EnergyMix';
import { RenewablesTracker } from './components/RenewablesTracker';

function App() {
  const [selectedRegion, setSelectedRegion] = useState<'India' | 'US' | 'Globe'>('India');
  const [isDarkMode, setIsDarkMode] = useState(true);
  
  // Data States
  const [news, setNews] = useState<any[]>([]);
  const [gridData, setGridData] = useState<any>(null);
  const [mixData, setMixData] = useState<any>(null);
  const [pins, setPins] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Apply dark/light class to html tag
  useEffect(() => {
    const htmlEl = document.documentElement;
    if (isDarkMode) {
      htmlEl.classList.remove('light-mode');
    } else {
      htmlEl.classList.add('light-mode');
    }
  }, [isDarkMode]);

  // Fetch compiled data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [newsRes, gridRes, mixRes, pinsRes] = await Promise.all([
          fetch('/data/news.json').then(r => r.json()),
          fetch('/data/grid-status.json').then(r => r.json()),
          fetch('/data/energy-mix.json').then(r => r.json()),
          fetch('/data/map-layers.json').then(r => r.json())
        ]);
        
        setNews(newsRes);
        setGridData(gridRes);
        setMixData(mixRes);
        setPins(pinsRes);
        setError(null);
      } catch (err: any) {
        console.error('Failed to load dashboard data:', err);
        setError('Failed to fetch real-time intelligence feeds. Displaying fallback configuration.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
    // Poll every 30 seconds for any updates to the static compiled files
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <header className="header-bar">
        <div className="brand-container">
          <h1 className="brand-title">NEURON 2.0</h1>
          <span className="brand-subtitle">Global Energy Intelligence Hub</span>
        </div>

        {/* Region Selector Tabs */}
        <div style={{ display: 'flex', gap: '8px', background: 'var(--bg-primary)', padding: '4px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          {(['India', 'US', 'Globe'] as const).map((region) => (
            <button
              key={region}
              onClick={() => setSelectedRegion(region)}
              style={{
                padding: '6px 16px',
                border: 'none',
                borderRadius: '6px',
                background: selectedRegion === region ? 'var(--bg-secondary)' : 'transparent',
                color: selectedRegion === region ? 'var(--accent-energy)' : 'var(--text-secondary)',
                fontWeight: '600',
                fontSize: '13px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              {region === 'Globe' ? <Globe size={14} /> : <Zap size={14} />}
              {region === 'Globe' ? 'Global' : region}
            </button>
          ))}
        </div>

        <div className="controls-group">
          {/* Developed By Signature */}
          <div className="branding-signature">
            Developed by Vipul Jakhar
          </div>
          
          {/* Theme Toggle */}
          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            className="theme-toggle-btn"
            title={isDarkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          >
            {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </header>

      {error && (
        <div style={{
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          color: '#ef4444',
          padding: '10px 16px',
          borderRadius: '8px',
          marginBottom: '16px',
          fontSize: '13px',
          fontWeight: '500'
        }}>
          {error}
        </div>
      )}

      {loading && !news.length ? (
        <div style={{ display: 'flex', flex: 1, alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
            <Zap size={32} className="pulse-icon" style={{ color: 'var(--accent-energy)', animation: 'pulse 1.5s infinite' }} />
            <span style={{ fontSize: '14px', color: 'var(--text-secondary)', fontWeight: '500' }}>
              Hydrating telemetry and intelligence channels...
            </span>
          </div>
        </div>
      ) : (
        <main className="dashboard-grid">
          {/* Center Map Panel */}
          <div className="panel-card map-panel">
            <div className="panel-header">
              <h3 className="panel-title">
                <Globe size={16} style={{ color: 'var(--accent-energy)' }} />
                Energy & Power Infrastructure Map ({selectedRegion})
              </h3>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 'bold' }}>TACTICAL MAP</span>
            </div>
            <div style={{ flex: 1, minHeight: '400px' }}>
              <EnergyMap
                pins={pins.filter(pin => selectedRegion === 'Globe' ? true : pin.region === selectedRegion)}
                isDarkMode={isDarkMode}
                selectedRegion={selectedRegion}
              />
            </div>
          </div>

          {/* Right Live News Stream Panel */}
          <LiveNews news={news} />

          {/* Grid Telemetry */}
          <GridStatus data={gridData} selectedRegion={selectedRegion} />

          {/* Fuel Mix Chart */}
          <EnergyMix data={mixData} selectedRegion={selectedRegion} />

          {/* Renewable Targets progress bar tracker */}
          <RenewablesTracker selectedRegion={selectedRegion} />
        </main>
      )}
    </>
  );
}

export default App;

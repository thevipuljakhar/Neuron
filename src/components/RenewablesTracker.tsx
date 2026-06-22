import React from 'react';
import { Target, Compass } from 'lucide-react';

interface RenewablesTrackerProps {
  selectedRegion: string;
}

export const RenewablesTracker: React.FC<RenewablesTrackerProps> = ({ selectedRegion }) => {
  const renderContent = () => {
    if (selectedRegion === 'India') {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
              <span>India Clean Energy 2030 Goal</span>
              <span style={{ fontWeight: 'bold' }}>192 / 500 GW</span>
            </div>
            <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: '38.4%', backgroundColor: 'var(--accent-renewable)', borderRadius: '4px' }}></div>
            </div>
            <div style={{ display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
              <span>Progress: 38.4% completed</span>
              <span>Target: 2030</span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '4px' }}>
            <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 'bold' }}>ACTIVE SOLAR PIPELINE</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--accent-india)', fontFamily: 'var(--font-display)' }}>62.5 GW</div>
            </div>
            <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 'bold' }}>OFFSHORE WIND TARGET</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--accent-renewable)', fontFamily: 'var(--font-display)' }}>30.0 GW</div>
            </div>
          </div>
        </div>
      );
    }

    if (selectedRegion === 'US') {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div>
            <div style={{ display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
              <span>US Clean Electricity 2035 Goal</span>
              <span style={{ fontWeight: 'bold' }}>40.8% / 100%</span>
            </div>
            <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: '40.8%', backgroundColor: 'var(--accent-us)', borderRadius: '4px' }}></div>
            </div>
            <div style={{ display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
              <span>Progress: 40.8% completed</span>
              <span>Target: 2035</span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '4px' }}>
            <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 'bold' }}>IRA FUNDING SPENT</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--accent-us)', fontFamily: 'var(--font-display)' }}>$114 Billion</div>
            </div>
            <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 'bold' }}>GRID INTERCONNECTION</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#ef4444', fontFamily: 'var(--font-display)' }}>2,600 GW queued</div>
            </div>
          </div>
        </div>
      );
    }

    // Globe
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
            <span>COP28 Tripling Renewables Goal</span>
            <span style={{ fontWeight: 'bold' }}>3,980 / 11,000 GW</span>
          </div>
          <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: '36.2%', backgroundColor: 'var(--accent-globe)', borderRadius: '4px' }}></div>
          </div>
          <div style={{ display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between', fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
            <span>Progress: 36.2% completed</span>
            <span>Target: 2030</span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '4px' }}>
          <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 'bold' }}>GLOBAL SOLAR CAPACITY</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--accent-energy)', fontFamily: 'var(--font-display)' }}>1,420 GW</div>
          </div>
          <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 'bold' }}>GLOBAL WIND CAPACITY</div>
            <div style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--accent-renewable)', fontFamily: 'var(--font-display)' }}>1,010 GW</div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="panel-card renewables-panel">
      <div className="panel-header">
        <h3 className="panel-title">
          <Target size={16} style={{ color: 'var(--accent-renewable)' }} />
          Renewable Capacity Targets ({selectedRegion})
        </h3>
        <Compass size={14} style={{ color: 'var(--text-muted)' }} />
      </div>
      <div className="panel-content">
        {renderContent()}
      </div>
    </div>
  );
};

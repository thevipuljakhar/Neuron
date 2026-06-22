import React from 'react';
import { Activity, TrendingUp } from 'lucide-react';

interface GridData {
  demand: number;
  capacity: number;
  frequency?: number;
  deficit?: number;
  reserveMargin?: number;
  status: string;
  renewablesInstant?: number;
  euGasStorage?: number;
  globalDemandGrowth?: number;
  lngFleetActive?: number;
  coalPhaseoutRate?: number;
  updateTime: string;
}

interface GridStatusProps {
  data: {
    india: GridData;
    us: GridData;
    global: GridData;
  } | null;
  selectedRegion: string;
}

export const GridStatus: React.FC<GridStatusProps> = ({ data, selectedRegion }) => {
  if (!data) return <div className="panel-card status-panel"><div className="panel-content">Loading grid status...</div></div>;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Normal': return '#22c55e';
      case 'Alert': return '#eab308';
      case 'Critical': return '#ef4444';
      default: return 'var(--text-muted)';
    }
  };

  const renderGridContent = () => {
    if (selectedRegion === 'India') {
      const loadFactor = Math.round((data.india.demand / data.india.capacity) * 100);
      const renewShare = Math.round((data.india.renewablesInstant! / data.india.demand) * 100);
      
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>POSOCO Grid Frequency</span>
            <span style={{ fontSize: '16px', fontWeight: 'bold', fontFamily: 'var(--font-display)', color: 'var(--accent-energy)' }}>
              {data.india.frequency} Hz
            </span>
          </div>

          <div className="metric-row">
            <span className="metric-label">Peak Demand Load</span>
            <span className="metric-value">{data.india.demand} GW</span>
          </div>

          <div className="metric-row">
            <span className="metric-label">Total Installed Capacity</span>
            <span className="metric-value">{data.india.capacity} GW</span>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
              <span>Grid Load Factor</span>
              <span>{loadFactor}%</span>
            </div>
            <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${loadFactor}%`, backgroundColor: 'var(--accent-india)', borderRadius: '3px' }}></div>
            </div>
          </div>

          <div className="metric-row">
            <span className="metric-label">Active Power Deficit</span>
            <span className="metric-value" style={{ color: data.india.deficit! > 0 ? '#ef4444' : 'var(--text-primary)' }}>
              {data.india.deficit} GW
            </span>
          </div>

          <div className="metric-row">
            <span className="metric-label">Instantaneous Clean Output</span>
            <span className="metric-value" style={{ color: 'var(--accent-renewable)' }}>
              {data.india.renewablesInstant} GW ({renewShare}%)
            </span>
          </div>
        </div>
      );
    }

    if (selectedRegion === 'US') {
      const loadFactor = Math.round((data.us.demand / data.us.capacity) * 100);
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div className="metric-row">
            <span className="metric-label">EIA Total Demand</span>
            <span className="metric-value">{data.us.demand} GW</span>
          </div>

          <div className="metric-row">
            <span className="metric-label">Total Grid Capacity</span>
            <span className="metric-value">{data.us.capacity} GW</span>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
              <span>Grid Utilization</span>
              <span>{loadFactor}%</span>
            </div>
            <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${loadFactor}%`, backgroundColor: 'var(--accent-us)', borderRadius: '3px' }}></div>
            </div>
          </div>

          <div className="metric-row">
            <span className="metric-label">Operating Reserve Margin</span>
            <span className="metric-value" style={{ color: 'var(--accent-renewable)' }}>
              {data.us.reserveMargin}%
            </span>
          </div>

          <div className="metric-row">
            <span className="metric-label">Wind + Solar Contribution</span>
            <span className="metric-value">{data.us.renewablesInstant} GW</span>
          </div>
        </div>
      );
    }

    // Default Globe
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div className="metric-row">
          <span className="metric-label">EU Gas Storage Level</span>
          <span className="metric-value" style={{ color: 'var(--accent-energy)' }}>{data.global.euGasStorage}%</span>
        </div>

        <div>
          <div style={{ display: 'flex', justifySelf: 'stretch', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>
            <span>Storage Fill Status</span>
            <span>{data.global.euGasStorage}%</span>
          </div>
          <div style={{ width: '100%', height: '6px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${data.global.euGasStorage}%`, backgroundColor: 'var(--accent-globe)', borderRadius: '3px' }}></div>
          </div>
        </div>

        <div className="metric-row">
          <span className="metric-label">Global Energy Demand Growth</span>
          <span className="metric-value" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <TrendingUp size={14} style={{ color: 'var(--accent-renewable)' }} />
            +{data.global.globalDemandGrowth}% YoY
          </span>
        </div>

        <div className="metric-row">
          <span className="metric-label">Active LNG Transport Fleet</span>
          <span className="metric-value">{data.global.lngFleetActive} vessels</span>
        </div>

        <div className="metric-row">
          <span className="metric-label">Coal Consumption Phaseout Rate</span>
          <span className="metric-value" style={{ color: '#ef4444' }}>{data.global.coalPhaseoutRate}%</span>
        </div>
      </div>
    );
  };

  const activeGrid = selectedRegion === 'India' ? data.india : selectedRegion === 'US' ? data.us : data.global;

  return (
    <div className="panel-card status-panel">
      <div className="panel-header">
        <h3 className="panel-title">
          <Activity size={16} style={{ color: 'var(--accent-us)' }} />
          Grid telemetry ({selectedRegion})
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: getStatusColor(activeGrid.status),
            boxShadow: `0 0 6px ${getStatusColor(activeGrid.status)}`
          }}></span>
          <span style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--text-secondary)' }}>
            {activeGrid.status}
          </span>
        </div>
      </div>
      <div className="panel-content">
        {renderGridContent()}
        
        <div style={{ marginTop: '14px', fontSize: '10px', color: 'var(--text-muted)', textAlign: 'right' }}>
          Telemetry: {new Date(activeGrid.updateTime).toLocaleString()}
        </div>
      </div>
    </div>
  );
};

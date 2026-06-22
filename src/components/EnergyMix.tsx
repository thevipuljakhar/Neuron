import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Fuel } from 'lucide-react';

interface MixItem {
  name: string;
  value: number;
  color: string;
}

interface EnergyMixProps {
  data: {
    india: MixItem[];
    us: MixItem[];
    global: MixItem[];
  } | null;
  selectedRegion: string;
}

export const EnergyMix: React.FC<EnergyMixProps> = ({ data, selectedRegion }) => {
  if (!data) return <div className="panel-card mix-panel"><div className="panel-content">Loading fuel mix...</div></div>;

  const currentMix = selectedRegion === 'India'
    ? data.india
    : selectedRegion === 'US'
      ? data.us
      : data.global;

  // Compute Clean Energy Percentage (non-coal, non-gas, non-fossil)
  const cleanEnergyPct = Math.round(
    currentMix
      .filter(item => ['Solar', 'Wind', 'Hydro', 'Nuclear', 'Other Clean', 'Renewable'].includes(item.name))
      .reduce((sum, item) => sum + item.value, 0)
  );

  return (
    <div className="panel-card mix-panel">
      <div className="panel-header">
        <h3 className="panel-title">
          <Fuel size={16} style={{ color: 'var(--accent-energy)' }} />
          Generation Fuel Mix
        </h3>
        <span style={{
          fontSize: '11px',
          fontWeight: '700',
          padding: '2px 8px',
          borderRadius: '4px',
          backgroundColor: 'rgba(34, 197, 94, 0.12)',
          color: 'var(--accent-renewable)',
          border: '1px solid rgba(34, 197, 94, 0.3)'
        }}>
          {cleanEnergyPct}% CLEAN
        </span>
      </div>
      <div className="panel-content" style={{ display: 'flex', flexDirection: 'column', height: '280px' }}>
        <div style={{ flex: 1, minHeight: '160px', width: '100%', position: 'relative' }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={currentMix}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={75}
                paddingAngle={2}
                dataKey="value"
              >
                {currentMix.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value: any) => [`${value}%`, 'Share']}
                contentStyle={{
                  backgroundColor: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '6px',
                  color: 'var(--text-primary)',
                  fontFamily: 'var(--font-sans)',
                  fontSize: '12px'
                }}
              />
            </PieChart>
          </ResponsiveContainer>
          {/* Centered clean energy stat inside Donut */}
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            textAlign: 'center',
            pointerEvents: 'none'
          }}>
            <div style={{ fontSize: '20px', fontWeight: 'bold', fontFamily: 'var(--font-display)', color: 'var(--text-primary)' }}>
              {cleanEnergyPct}%
            </div>
            <div style={{ fontSize: '9px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: '600' }}>
              Clean
            </div>
          </div>
        </div>

        {/* Legend */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '8px 4px',
          marginTop: '12px',
          fontSize: '11px',
          color: 'var(--text-secondary)'
        }}>
          {currentMix.map((item, index) => (
            <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: item.color,
                display: 'inline-block',
                flexShrink: 0
              }}></span>
              <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {item.name}: <strong>{item.value}%</strong>
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

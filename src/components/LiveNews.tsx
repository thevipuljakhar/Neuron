import React, { useState } from 'react';
import { Search, Radio, ExternalLink } from 'lucide-react';

interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  timestamp: string;
  region: 'India' | 'US' | 'Globe';
  category: 'Grid' | 'Fossil' | 'Renewable';
  link: string;
}

interface LiveNewsProps {
  news: NewsItem[];
}

export const LiveNews: React.FC<LiveNewsProps> = ({ news }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [regionFilter, setRegionFilter] = useState<'All' | 'India' | 'US' | 'Globe'>('All');
  const [categoryFilter, setCategoryFilter] = useState<'All' | 'Grid' | 'Fossil' | 'Renewable'>('All');

  // Calculate actual ratios in loaded news
  const indiaCount = news.filter(n => n.region === 'India').length;
  const usCount = news.filter(n => n.region === 'US').length;
  const globeCount = news.filter(n => n.region === 'Globe').length;
  const total = news.length || 1;

  const indiaPct = Math.round((indiaCount / total) * 100);
  const usPct = Math.round((usCount / total) * 100);
  const globePct = Math.round((globeCount / total) * 100);

  // Filter news items
  const filteredNews = news.filter(item => {
    const matchesSearch = item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          item.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          item.source.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesRegion = regionFilter === 'All' || item.region === regionFilter;
    const matchesCategory = categoryFilter === 'All' || item.category === categoryFilter;

    return matchesSearch && matchesRegion && matchesCategory;
  });

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'Renewable': return 'var(--accent-renewable)';
      case 'Grid': return 'var(--accent-us)';
      case 'Fossil': return '#ef4444';
      default: return 'var(--text-muted)';
    }
  };

  const getRegionBadgeStyle = (region: string) => {
    switch (region) {
      case 'India': return { backgroundColor: 'rgba(249, 115, 22, 0.12)', color: 'var(--accent-india)', border: '1px solid rgba(249, 115, 22, 0.3)' };
      case 'US': return { backgroundColor: 'rgba(59, 130, 246, 0.12)', color: 'var(--accent-us)', border: '1px solid rgba(59, 130, 246, 0.3)' };
      case 'Globe': return { backgroundColor: 'rgba(168, 85, 247, 0.12)', color: 'var(--accent-globe)', border: '1px solid rgba(168, 85, 247, 0.3)' };
      default: return {};
    }
  };

  return (
    <div className="panel-card news-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="panel-header">
        <h3 className="panel-title">
          <Radio size={16} className="pulse-icon" style={{ color: 'var(--accent-india)' }} />
          Intelligence Stream
        </h3>
        <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 'bold' }}>LIVE FEEDS</span>
      </div>

      {/* Target Focus Ratios */}
      <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.02)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', fontWeight: 'bold', marginBottom: '4px' }}>
          <span>FOCUS TARGET (IN:US:GL)</span>
          <span style={{ color: 'var(--accent-india)' }}>70% : 15% : 15%</span>
        </div>
        <div className="ratio-bar-container">
          <div className="ratio-segment" style={{ width: '70%', backgroundColor: 'var(--accent-india)' }}></div>
          <div className="ratio-segment" style={{ width: '15%', backgroundColor: 'var(--accent-us)' }}></div>
          <div className="ratio-segment" style={{ width: '15%', backgroundColor: 'var(--accent-globe)' }}></div>
        </div>
        <div className="ratio-legend">
          <div className="ratio-legend-item">
            <span className="color-dot" style={{ backgroundColor: 'var(--accent-india)' }}></span>
            <span>India (${indiaPct}%)</span>
          </div>
          <div className="ratio-legend-item">
            <span className="color-dot" style={{ backgroundColor: 'var(--accent-us)' }}></span>
            <span>US (${usPct}%)</span>
          </div>
          <div className="ratio-legend-item">
            <span className="color-dot" style={{ backgroundColor: 'var(--accent-globe)' }}></span>
            <span>Global (${globePct}%)</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', position: 'relative', alignItems: 'center' }}>
          <Search size={14} style={{ position: 'absolute', left: '10px', color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Filter intelligence..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '6px 12px 6px 30px',
              borderRadius: '6px',
              border: '1px solid var(--border-color)',
              background: 'var(--bg-primary)',
              color: 'var(--text-primary)',
              fontSize: '13px',
              outline: 'none'
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '2px' }}>
          <button
            onClick={() => setRegionFilter('All')}
            className={`filter-btn ${regionFilter === 'All' ? 'active' : ''}`}
            style={getFilterStyle(regionFilter === 'All')}
          >
            All regions
          </button>
          <button
            onClick={() => setRegionFilter('India')}
            className={`filter-btn ${regionFilter === 'India' ? 'active' : ''}`}
            style={getFilterStyle(regionFilter === 'India')}
          >
            India
          </button>
          <button
            onClick={() => setRegionFilter('US')}
            className={`filter-btn ${regionFilter === 'US' ? 'active' : ''}`}
            style={getFilterStyle(regionFilter === 'US')}
          >
            US
          </button>
          <button
            onClick={() => setRegionFilter('Globe')}
            className={`filter-btn ${regionFilter === 'Globe' ? 'active' : ''}`}
            style={getFilterStyle(regionFilter === 'Globe')}
          >
            Global
          </button>
        </div>

        <div style={{ display: 'flex', gap: '6px', overflowX: 'auto' }}>
          <button
            onClick={() => setCategoryFilter('All')}
            className={`filter-btn ${categoryFilter === 'All' ? 'active' : ''}`}
            style={getFilterStyle(categoryFilter === 'All')}
          >
            All sectors
          </button>
          <button
            onClick={() => setCategoryFilter('Renewable')}
            className={`filter-btn ${categoryFilter === 'Renewable' ? 'active' : ''}`}
            style={getFilterStyle(categoryFilter === 'Renewable')}
          >
            Renewable
          </button>
          <button
            onClick={() => setCategoryFilter('Grid')}
            className={`filter-btn ${categoryFilter === 'Grid' ? 'active' : ''}`}
            style={getFilterStyle(categoryFilter === 'Grid')}
          >
            Grid System
          </button>
          <button
            onClick={() => setCategoryFilter('Fossil')}
            className={`filter-btn ${categoryFilter === 'Fossil' ? 'active' : ''}`}
            style={getFilterStyle(categoryFilter === 'Fossil')}
          >
            Fossil/Thermal
          </button>
        </div>
      </div>

      {/* Feed list */}
      <div className="panel-content" style={{ flex: 1, padding: 0 }}>
        {filteredNews.length === 0 ? (
          <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
            No matching reports found
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {filteredNews.map(item => (
              <div
                key={item.id}
                style={{
                  padding: '14px 16px',
                  borderBottom: '1px solid var(--border-color)',
                  transition: 'background-color 0.2s ease',
                  cursor: 'pointer',
                  position: 'relative'
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.02)'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                    <span style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: getCategoryColor(item.category),
                      boxShadow: `0 0 6px ${getCategoryColor(item.category)}`
                    }}></span>
                    <span style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--text-muted)' }}>{item.source}</span>
                  </div>
                  <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                    {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>

                <h4 style={{ fontSize: '13px', fontWeight: '600', lineHeight: '1.4', marginBottom: '4px', color: 'var(--text-primary)' }}>
                  {item.title}
                </h4>
                
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4', marginBottom: '8px' }}>
                  {item.summary}
                </p>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <span style={{
                      fontSize: '9px',
                      fontWeight: '700',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      ...getRegionBadgeStyle(item.region)
                    }}>{item.region}</span>
                    <span style={{
                      fontSize: '9px',
                      fontWeight: '700',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      backgroundColor: 'var(--bg-tertiary)',
                      color: 'var(--text-secondary)',
                      border: '1px solid var(--border-color)'
                    }}>{item.category}</span>
                  </div>
                  
                  <a
                    href={item.link}
                    target="_blank"
                    rel="noreferrer"
                    style={{
                      color: 'var(--text-muted)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      textDecoration: 'none',
                      fontSize: '11px'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.color = 'var(--accent-energy)'}
                    onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
                  >
                    Source <ExternalLink size={10} />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const getFilterStyle = (isActive: boolean) => ({
  padding: '4px 10px',
  borderRadius: '4px',
  border: '1px solid var(--border-color)',
  background: isActive ? 'var(--bg-tertiary)' : 'transparent',
  color: isActive ? 'var(--accent-energy)' : 'var(--text-secondary)',
  fontSize: '11px',
  fontWeight: '600',
  cursor: 'pointer',
  whiteSpace: 'nowrap' as const,
  transition: 'all 0.2s ease',
});

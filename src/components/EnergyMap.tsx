import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';

interface MapPin {
  id: string;
  name: string;
  type: string;
  capacity: string;
  region: string;
  lat: number;
  lng: number;
  status: string;
  description: string;
}

interface EnergyMapProps {
  pins: MapPin[];
  isDarkMode: boolean;
  selectedRegion: string;
}

// Helper to center/fly map to region
const MapController: React.FC<{ region: string }> = ({ region }) => {
  const map = useMap();
  useEffect(() => {
    if (region === 'India') {
      map.flyTo([22.5, 78.5], 4.5, { duration: 1.5 });
    } else if (region === 'US') {
      map.flyTo([37.8, -96.0], 4, { duration: 1.5 });
    } else if (region === 'Globe') {
      map.flyTo([25, 10], 2, { duration: 1.5 });
    }
  }, [region, map]);

  return null;
};

export const EnergyMap: React.FC<EnergyMapProps> = ({ pins, isDarkMode, selectedRegion }) => {
  // Basemap tile URL based on theme
  const tileUrl = isDarkMode
    ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
    : 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';

  const attribution = isDarkMode
    ? '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    : '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';

  const createCustomIcon = (type: string) => {
    let color = '#eab308'; // Amber for solar/energy
    if (type === 'Solar') color = '#eab308';
    else if (type === 'Wind') color = '#22c55e';
    else if (type === 'Nuclear') color = '#a855f7';
    else if (type === 'Hydro') color = '#3b82f6';
    else if (type === 'Battery') color = '#14b8a6';
    else if (type === 'Fossil') color = '#ef4444';

    return L.divIcon({
      className: 'custom-map-pin',
      html: `<div style="
        background-color: ${color};
        width: 14px;
        height: 14px;
        border-radius: 50%;
        border: 2px solid #ffffff;
        box-shadow: 0 0 8px ${color}, 0 0 4px ${color};
      "></div>`,
      iconSize: [14, 14],
      iconAnchor: [7, 7],
      popupAnchor: [0, -7]
    });
  };

  return (
    <div className="map-container-wrapper">
      <MapContainer
        center={[22.5, 78.5]}
        zoom={4.5}
        scrollWheelZoom={true}
        style={{ width: '100%', height: '100%', borderRadius: '0 0 12px 12px' }}
      >
        <TileLayer url={tileUrl} attribution={attribution} />
        <MapController region={selectedRegion} />
        {pins.map((pin) => (
          <Marker
            key={pin.id}
            position={[pin.lat, pin.lng]}
            icon={createCustomIcon(pin.type)}
          >
            <Popup>
              <div style={{ fontFamily: 'var(--font-sans)', minWidth: '180px' }}>
                <h4 style={{ margin: '0 0 4px 0', fontSize: '14px', fontWeight: 'bold' }}>{pin.name}</h4>
                <div style={{ display: 'flex', gap: '6px', margin: '4px 0 8px 0' }}>
                  <span style={{
                    fontSize: '10px',
                    fontWeight: 'bold',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    backgroundColor: '#e2e8f0',
                    color: '#475569'
                  }}>{pin.type}</span>
                  <span style={{
                    fontSize: '10px',
                    fontWeight: 'bold',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    backgroundColor: '#dcfce7',
                    color: '#15803d'
                  }}>{pin.status}</span>
                </div>
                <p style={{ margin: '0 0 6px 0', fontSize: '11px', color: '#64748b' }}>
                  <strong>Capacity:</strong> {pin.capacity}
                </p>
                <p style={{ margin: 0, fontSize: '11px', color: '#475569', lineHeight: '1.3' }}>
                  {pin.description}
                </p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
};

'use client';

import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect } from 'react';

// Fix for default marker icons in React Leaflet
const iconUrl = 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png';
const iconRetinaUrl = 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png';
const shadowUrl = 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
  iconUrl,
  iconRetinaUrl,
  shadowUrl,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

const customIcon = L.divIcon({
  className: 'custom-div-icon',
  html: `<div style="background-color: #ef4444; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px #ef4444;"></div>`,
  iconSize: [12, 12],
  iconAnchor: [6, 6]
});

export default function MapComponent({ geoData }: { geoData: any[] }) {
  // Center roughly based on data or default to mid-Atlantic
  const center = geoData.length > 0 
    ? [geoData[0].geo.lat, geoData[0].geo.lon] 
    : [20, 0];

  return (
    <div className="h-[500px] w-full rounded-xl overflow-hidden border border-zinc-800 shadow-2xl z-0">
      <MapContainer 
        center={center as [number, number]} 
        zoom={3} 
        style={{ height: '100%', width: '100%', background: '#0d1117' }}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />
        
        {geoData.map((session) => {
          if (!session.geo || session.geo.lat === 0 || session.geo.lon === 0) return null;
          
          return (
            <div key={session.session_id}>
              <CircleMarker
                center={[session.geo.lat, session.geo.lon]}
                radius={20}
                pathOptions={{
                  color: '#ef4444',
                  fillColor: '#ef4444',
                  fillOpacity: 0.15,
                  weight: 2
                }}
              />
              <Marker 
                position={[session.geo.lat, session.geo.lon]}
                icon={customIcon}
              >
                <Popup className="bg-zinc-900 border-zinc-800 text-white rounded-lg">
                  <div className="text-zinc-200 p-1 text-sm notranslate" translate="no">
                    <p className="font-bold text-white mb-1">IP: {session.client_ip}</p>
                    <p><span className="text-zinc-500">City:</span> {session.geo.city}</p>
                    <p><span className="text-zinc-500">Country:</span> {session.geo.country}</p>
                    <p><span className="text-zinc-500">ISP:</span> {session.geo.isp}</p>
                    <p><span className="text-zinc-500">Session:</span> {session.session_id.substring(0,8)}...</p>
                  </div>
                </Popup>
              </Marker>
            </div>
          );
        })}
      </MapContainer>
    </div>
  );
}

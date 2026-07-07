import React, { useState, useEffect } from 'react';
import './App.css';

function GaugeCircle({ value, max, label, unit, color }) {
  const pct = Math.min(value / max, 1);
  const r = 60;
  const cx = 80, cy = 80;
  const startAngle = -135 * (Math.PI / 180);
  const arcLength = 270 * (Math.PI / 180);
  const filledArc = pct * arcLength;
  const x1 = cx + r * Math.cos(startAngle);
  const y1 = cy + r * Math.sin(startAngle);
  const x2 = cx + r * Math.cos(startAngle + filledArc);
  const y2 = cy + r * Math.sin(startAngle + filledArc);
  const largeArc = filledArc > Math.PI ? 1 : 0;

  return (
    <div className="gauge">
      <svg width="160" height="160" viewBox="0 0 160 160">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#1a1a2e" strokeWidth="12" />
        {pct > 0 && (
          <path
            d={`M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`}
            fill="none" stroke={color} strokeWidth="12" strokeLinecap="round"
          />
        )}
        <text x={cx} y={cy - 8} textAnchor="middle" fill="white" fontSize="22" fontWeight="bold">{value}</text>
        <text x={cx} y={cy + 12} textAnchor="middle" fill="#888" fontSize="11">{unit}</text>
      </svg>
      <div className="gauge-label">{label}</div>
    </div>
  );
}

function BatteryBar({ voltage }) {
  const pct = Math.max(0, Math.min(1, (voltage - 11.5) / 3));
  const color = voltage < 12.0 ? '#ff4444' : voltage < 12.4 ? '#ffaa00' : '#00ff88';
  return (
    <div className="mid-card">
      <div className="card-title">BATERIA</div>
      <div className="battery-voltage">{voltage.toFixed(1)} V</div>
      <div className="battery-bar-bg">
        <div className="battery-bar-fill" style={{ width: `${pct * 100}%`, background: color }} />
      </div>
      <div className="battery-status" style={{ color }}>
        {voltage < 12.0 ? 'CRÍTICA' : voltage < 12.4 ? 'BAIXA' : 'NORMAL'}
      </div>
    </div>
  );
}

export default function App() {
  const [data, setData] = useState({ rpm: 850, speed: 0, temp: 88, battery: 12.6, fuel: 65, headlights: false });
  const [listening, setListening] = useState(false);
  const [aiMsg, setAiMsg] = useState('Sistema inicializado. Boa viagem, Abimael.');
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => {
      setData(d => ({ ...d, rpm: 820 + Math.floor(Math.random() * 160) }));
      setTime(new Date());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const toggleLight = () => {
    setData(d => ({ ...d, headlights: !d.headlights }));
    setAiMsg(data.headlights ? 'Farol desligado.' : 'Farol ligado.');
  };

  const handleVoice = () => {
    setListening(true);
    setTimeout(() => {
      setListening(false);
      setAiMsg('Bateria em 12.6V, nível normal. Temperatura do motor estável em 88°C.');
    }, 2000);
  };

  const tempColor = data.temp > 100 ? '#ff4444' : data.temp > 90 ? '#ffaa00' : '#00ff88';
  const hh = time.getHours().toString().padStart(2, '0');
  const mm = time.getMinutes().toString().padStart(2, '0');

  return (
    <div className="app">
      <header className="header">
        <div className="logo">⚡ CORSA<span>OS</span></div>
        <div className="clock">{hh}:{mm}</div>
        <div className="engine-on">● MOTOR ON</div>
      </header>

      <div className="gauges-row">
        <GaugeCircle value={data.rpm} max={6000} label="RPM" unit="rpm" color="#00aaff" />
        <div className="speed-center">
          <div className="speed-value">{data.speed}</div>
          <div className="speed-unit">km/h</div>
        </div>
        <GaugeCircle value={Math.round(data.temp)} max={120} label="TEMPERATURA" unit="°C" color={tempColor} />
      </div>

      <div className="mid-row">
        <BatteryBar voltage={data.battery} />

        <div className="mid-card">
          <div className="card-title">COMBUSTÍVEL</div>
          <svg width="100" height="100" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="40" fill="none" stroke="#1a1a2e" strokeWidth="10"/>
            <circle cx="50" cy="50" r="40" fill="none" stroke="#ffaa00"
              strokeWidth="10" strokeDasharray={`${data.fuel * 2.51} 251`}
              strokeDashoffset="62.75" strokeLinecap="round" transform="rotate(-90 50 50)"/>
            <text x="50" y="55" textAnchor="middle" fill="white" fontSize="18" fontWeight="bold">{data.fuel}%</text>
          </svg>
        </div>

        <div className="mid-card">
          <div className="card-title">CONTROLES</div>
          <button className={`ctrl-btn ${data.headlights ? 'active' : ''}`} onClick={toggleLight}>
            💡 {data.headlights ? 'Farol ON' : 'Farol OFF'}
          </button>
        </div>
      </div>

      <div className="ai-bar">
        <span className="ai-icon">🤖</span>
        <span className="ai-text">{aiMsg}</span>
        <button className={`voice-btn ${listening ? 'listening' : ''}`} onClick={handleVoice}>
          🎙 {listening ? 'Ouvindo...' : 'Corsa, falar'}
        </button>
      </div>

      <div className="status-row">
        {[
          { icon: '🌡', label: 'INTERIOR', val: '24°C', color: '#00ff88' },
          { icon: '💧', label: 'UMIDADE', val: '58%', color: '#00aaff' },
          { icon: '🛣', label: 'CONSUMO', val: '12.4 km/L', color: '#ffaa00' },
          { icon: '🔧', label: 'REVISÃO', val: '2.400 km', color: '#ff88aa' },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <span className="stat-icon">{s.icon}</span>
            <div>
              <div className="stat-label">{s.label}</div>
              <div className="stat-val" style={{ color: s.color }}>{s.val}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

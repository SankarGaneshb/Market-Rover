import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { Activity, ArrowUpCircle, ArrowDownCircle, AlertCircle, Info } from 'lucide-react';
import { motion } from 'framer-motion';

const api = axios.create({ baseURL: '' });

// Helper Components
const GlassMetric = ({ title, value, sub, icon }) => (
  <div style={{
    background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)',
    borderRadius: '12px', padding: '1rem', display: 'flex', flexDirection: 'column',
    position: 'relative', overflow: 'hidden'
  }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
      <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, letterSpacing: '0.5px' }}>{title}</span>
      {icon}
    </div>
    <span style={{ fontSize: '1.4rem', fontWeight: 800, color: 'white' }}>{value !== null ? value : '-'}</span>
    {sub && <span style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '4px' }}>{sub}</span>}
  </div>
);

const DistanceBadge = ({ pct }) => {
  if (pct === null || pct === undefined) return null;
  const isPos = pct >= 0;
  const color = isPos ? '#10b981' : '#f43f5e';
  const bg = isPos ? 'rgba(16,185,129,0.1)' : 'rgba(244,63,94,0.1)';
  return (
    <span style={{
      background: bg, color: color, padding: '2px 6px', borderRadius: '6px',
      fontSize: '0.65rem', fontWeight: 700, marginLeft: '6px'
    }}>
      {isPos ? '+' : ''}{pct}%
    </span>
  );
};

const Thermometer = ({ value, min, max, pos, labelLow, labelHigh, markers = [] }) => {
  const dayLow = markers.find(m => m.label === 'Day Low');
  const dayHigh = markers.find(m => m.label === 'Day High');
  const dma50 = markers.find(m => m.label === '50 DMA');
  const dma200 = markers.find(m => m.label === '200 DMA');

  const getPct = (val, l, h) => {
    if (h <= l || val === null || val === undefined) return 0;
    return Math.max(0, Math.min(100, ((val - l) / (h - l)) * 100));
  };

  const dayPos = dayLow && dayHigh ? getPct(value, dayLow.value, dayHigh.value) : 50;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* SECTION 1: DUAL RANGE SLIDERS WITH MA TICKS */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>

        {/* 1. Day Range Slider */}
        {dayLow && dayHigh && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600 }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#f43f5e' }}></span>
                Day Low: <span style={{ color: 'white' }}>₹{dayLow.value}</span>
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                Day High: <span style={{ color: 'white' }}>₹{dayHigh.value}</span>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }}></span>
              </span>
            </div>

            <div style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', position: 'relative', margin: '0.2rem 0' }}>
              {/* 50 DMA Tick on Day Slider (only if within day range) */}
              {dma50 && dma50.value >= dayLow.value && dma50.value <= dayHigh.value && (
                <div style={{
                  position: 'absolute', left: `${getPct(dma50.value, dayLow.value, dayHigh.value)}%`, top: '50%', transform: 'translate(-50%, -50%)',
                  width: '4px', height: '14px', background: '#3b82f6', borderRadius: '1px',
                  boxShadow: '0 0 6px rgba(59,130,246,0.8)', zIndex: 4
                }} title={`50 DMA: ₹${dma50.value} (Inside Day Range)`} />
              )}

              {/* 200 DMA Tick on Day Slider (only if within day range) */}
              {dma200 && dma200.value >= dayLow.value && dma200.value <= dayHigh.value && (
                <div style={{
                  position: 'absolute', left: `${getPct(dma200.value, dayLow.value, dayHigh.value)}%`, top: '50%', transform: 'translate(-50%, -50%)',
                  width: '4px', height: '14px', background: '#8b5cf6', borderRadius: '1px',
                  boxShadow: '0 0 6px rgba(139,92,246,0.8)', zIndex: 4
                }} title={`200 DMA: ₹${dma200.value} (Inside Day Range)`} />
              )}

              {/* Current Price Pin */}
              <div style={{
                position: 'absolute', left: `${dayPos}%`, top: '50%', transform: 'translate(-50%, -50%)',
                width: '12px', height: '12px', background: 'var(--accent-cyan)', borderRadius: '50%',
                boxShadow: '0 0 10px var(--accent-cyan)', zIndex: 10
              }} title={`Current Price: ₹${value}`} />

              <div style={{
                position: 'absolute', left: 0, top: 0, height: '100%', width: `${dayPos}%`,
                background: 'linear-gradient(90deg, rgba(6,182,212,0.1), rgba(6,182,212,0.6))', borderRadius: '3px'
              }} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.62rem', color: '#64748b' }}>
              <span>+{((value - dayLow.value) / dayLow.value * 100).toFixed(1)}% from Low</span>
              <span>{((value - dayHigh.value) / dayHigh.value * 100).toFixed(1)}% to High</span>
            </div>
          </div>
        )}

        {/* 2. 52W Range Slider */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '0.8rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.72rem', color: '#94a3b8', fontWeight: 600 }}>
            <span>52W Low: <span style={{ color: 'white' }}>₹{min}</span></span>
            <span>52W High: <span style={{ color: 'white' }}>₹{max}</span></span>
          </div>

          <div style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', position: 'relative', margin: '0.2rem 0' }}>
            {/* 50 DMA Tick on 52W Slider */}
            {dma50 && (
              <div style={{
                position: 'absolute', left: `${getPct(dma50.value, min, max)}%`, top: '50%', transform: 'translate(-50%, -50%)',
                width: '4px', height: '14px', background: '#3b82f6', borderRadius: '1px',
                boxShadow: '0 0 6px rgba(59,130,246,0.8)', zIndex: 4
              }} title={`50 DMA: ₹${dma50.value}`} />
            )}

            {/* 200 DMA Tick on 52W Slider */}
            {dma200 && (
              <div style={{
                position: 'absolute', left: `${getPct(dma200.value, min, max)}%`, top: '50%', transform: 'translate(-50%, -50%)',
                width: '4px', height: '14px', background: '#8b5cf6', borderRadius: '1px',
                boxShadow: '0 0 6px rgba(139,92,246,0.8)', zIndex: 4
              }} title={`200 DMA: ₹${dma200.value}`} />
            )}

            {/* Current Price Pin */}
            <div style={{
              position: 'absolute', left: `${pos}%`, top: '50%', transform: 'translate(-50%, -50%)',
              width: '12px', height: '12px', background: 'var(--accent-cyan)', borderRadius: '50%',
              boxShadow: '0 0 10px var(--accent-cyan)', zIndex: 10
            }} title={`Current Price: ₹${value}`} />

            <div style={{
              position: 'absolute', left: 0, top: 0, height: '100%', width: `${pos}%`,
              background: 'linear-gradient(90deg, rgba(6,182,212,0.1), rgba(6,182,212,0.6))', borderRadius: '3px'
            }} />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.62rem', color: '#64748b' }}>
            <span>+{((value - min) / min * 100).toFixed(1)}% from Low</span>
            <span>{((value - max) / max * 100).toFixed(1)}% to High</span>
          </div>
        </div>

      </div>

      {/* SECTION 2: TECHNICAL MOVING AVERAGES CARDS WITH COMPARISONS */}
      {(dma50 || dma200) && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '0.6rem',
          borderTop: '1px solid rgba(255,255,255,0.05)',
          paddingTop: '0.8rem'
        }}>
          {dma50 && (
            <div style={{
              background: 'rgba(59, 130, 246, 0.03)',
              border: '1px solid rgba(59, 130, 246, 0.15)',
              borderRadius: '8px',
              padding: '0.6rem 0.8rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '1rem'
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#3b82f6' }}></span>
                  <span style={{ fontSize: '0.7rem', color: '#3b82f6', fontWeight: 800 }}>50 DMA</span>
                  <span style={{
                    fontSize: '0.58rem',
                    fontWeight: 800,
                    padding: '1px 6px',
                    borderRadius: '4px',
                    background: value >= dma50.value ? 'rgba(16,185,129,0.1)' : 'rgba(244,63,94,0.1)',
                    color: value >= dma50.value ? '#10b981' : '#f43f5e',
                    border: value >= dma50.value ? '1px solid rgba(16,185,129,0.2)' : '1px solid rgba(244,63,94,0.2)'
                  }}>
                    {value >= dma50.value ? 'Short Term: POSITIVE' : 'Short Term: NEGATIVE'}
                  </span>
                </div>
                <span style={{ fontSize: '1rem', fontWeight: 800, color: 'white' }}>₹{dma50.value}</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '2px' }}>
                <span style={{
                  fontSize: '0.75rem',
                  color: value >= dma50.value ? '#10b981' : '#f43f5e',
                  fontWeight: 800
                }}>
                  Current Price: {value >= dma50.value ? '▲' : '▼'} {Math.abs(((value - dma50.value) / dma50.value * 100)).toFixed(1)}%
                </span>
                <span style={{ fontSize: '0.62rem', color: '#94a3b8' }}>
                  {dayLow && dayHigh && dma50.value >= dayLow.value && dma50.value <= dayHigh.value
                    ? '🎯 Inside Session Range'
                    : dma50.value > dayHigh.value ? '📈 Above Day High' : '📉 Below Day Low'}
                </span>
                <span style={{ fontSize: '0.6rem', color: '#64748b' }}>
                  Position in 52W: {getPct(dma50.value, min, max).toFixed(0)}% from Low
                </span>
              </div>
            </div>
          )}

          {dma200 && (
            <div style={{
              background: 'rgba(139, 92, 246, 0.03)',
              border: '1px solid rgba(139, 92, 246, 0.15)',
              borderRadius: '8px',
              padding: '0.6rem 0.8rem',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '1rem'
            }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#8b5cf6' }}></span>
                  <span style={{ fontSize: '0.7rem', color: '#8b5cf6', fontWeight: 800 }}>200 DMA</span>
                  <span style={{
                    fontSize: '0.58rem',
                    fontWeight: 800,
                    padding: '1px 6px',
                    borderRadius: '4px',
                    background: value >= dma200.value ? 'rgba(16,185,129,0.1)' : 'rgba(244,63,94,0.1)',
                    color: value >= dma200.value ? '#10b981' : '#f43f5e',
                    border: value >= dma200.value ? '1px solid rgba(16,185,129,0.2)' : '1px solid rgba(244,63,94,0.2)'
                  }}>
                    {value >= dma200.value ? 'Long Term: POSITIVE' : 'Long Term: NEGATIVE'}
                  </span>
                </div>
                <span style={{ fontSize: '1rem', fontWeight: 800, color: 'white' }}>₹{dma200.value}</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '2px' }}>
                <span style={{
                  fontSize: '0.75rem',
                  color: value >= dma200.value ? '#10b981' : '#f43f5e',
                  fontWeight: 800
                }}>
                  Current Price: {value >= dma200.value ? '▲' : '▼'} {Math.abs(((value - dma200.value) / dma200.value * 100)).toFixed(1)}%
                </span>
                <span style={{ fontSize: '0.62rem', color: '#94a3b8' }}>
                  {dayLow && dayHigh && dma200.value >= dayLow.value && dma200.value <= dayHigh.value
                    ? '🎯 Inside Session Range'
                    : dma200.value > dayHigh.value ? '📈 Above Day High' : '📉 Below Day Low'}
                </span>
                <span style={{ fontSize: '0.6rem', color: '#64748b' }}>
                  Position in 52W: {getPct(dma200.value, min, max).toFixed(0)}% from Low
                </span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default function StockSnapshot({ ticker }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [show50DMA, setShow50DMA] = useState(true);
  const [show200DMA, setShow200DMA] = useState(true);
  const [showMACD, setShowMACD] = useState(false);
  const [showMACDSignal, setShowMACDSignal] = useState(false);
  const [showRSI, setShowRSI] = useState(false);

  useEffect(() => {
    const fetchSnapshot = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get(`/api/snapshot/${ticker}`);
        setData(res.data);
      } catch (err) {
        setError('Failed to load snapshot data.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (ticker) {
      fetchSnapshot();
    }
  }, [ticker]);

  if (!ticker) return null;

  if (loading) {
    return (
      <div className="glass-card" style={{ padding: '2rem', textAlign: 'center', marginBottom: '1.5rem' }}>
        <motion.div animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.5 }}>
          <Activity size={24} color="var(--accent-cyan)" style={{ marginBottom: '10px' }} />
          <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>Fetching live snapshot for {ticker}...</p>
        </motion.div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card" style={{ padding: '1rem', background: 'rgba(244,63,94,0.05)', borderColor: 'rgba(244,63,94,0.2)', marginBottom: '1.5rem' }}>
        <p style={{ color: '#f43f5e', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}><AlertCircle size={16} /> {error}</p>
      </div>
    );
  }

  const { metrics, chart_data } = data;

  return (
    <div className="glass-card" style={{ padding: '1.5rem', marginBottom: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

      {/* Header & Quick Thermometers */}
      <div style={{ display: 'flex', gap: '2rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ flex: '1 1 250px' }}>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 900, display: 'flex', alignItems: 'center', gap: '12px' }}>
            {ticker}
            <span style={{ fontSize: '1.2rem', color: 'var(--accent-cyan)' }}>₹{metrics.current_price}</span>
          </h2>
          <p style={{ fontSize: '0.8rem', color: '#64748b' }}>Live Institutional Snapshot</p>
        </div>

        <div style={{ flex: '1 1 300px', background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.03)' }}>
          <Thermometer
            value={metrics.current_price}
            min={metrics['52w_low']}
            max={metrics['52w_high']}
            pos={metrics.range_52w_pos}
            labelLow="52W Low"
            labelHigh="52W High"
            markers={[
                { value: metrics.dma_50, label: '50 DMA', color: '#3b82f6' },
                { value: metrics.dma_200, label: '200 DMA', color: '#8b5cf6' },
                { value: metrics.day_low, label: 'Day Low', color: '#f43f5e' },
                { value: metrics.day_high, label: 'Day High', color: '#10b981' }
            ].filter(m => m.value !== null && m.value !== undefined)}
          />
        </div>
      </div>

      {/* 1-Year Chart */}
      <div style={{ height: '350px', background: 'rgba(0,0,0,0.3)', borderRadius: '16px', padding: '1rem', border: '1px solid rgba(255,255,255,0.05)', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h4 style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: 700, margin: 0 }}>1-Year Price History vs DMAs & MACD</h4>
            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <label style={{ fontSize: '0.75rem', color: show50DMA ? '#3b82f6' : '#64748b', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: show50DMA ? 700 : 400 }}>
                    <input type="checkbox" checked={show50DMA} onChange={() => setShow50DMA(!show50DMA)} style={{ cursor: 'pointer' }} />
                    50 DMA
                </label>
                <label style={{ fontSize: '0.75rem', color: show200DMA ? '#8b5cf6' : '#64748b', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: show200DMA ? 700 : 400 }}>
                    <input type="checkbox" checked={show200DMA} onChange={() => setShow200DMA(!show200DMA)} style={{ cursor: 'pointer' }} />
                    200 DMA
                </label>
                <label style={{ fontSize: '0.75rem', color: showMACD ? '#f59e0b' : '#64748b', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: showMACD ? 700 : 400 }}>
                    <input type="checkbox" checked={showMACD} onChange={() => setShowMACD(!showMACD)} style={{ cursor: 'pointer' }} />
                    MACD
                </label>
                <label style={{ fontSize: '0.75rem', color: showMACDSignal ? '#ef4444' : '#64748b', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: showMACDSignal ? 700 : 400 }}>
                    <input type="checkbox" checked={showMACDSignal} onChange={() => setShowMACDSignal(!showMACDSignal)} style={{ cursor: 'pointer' }} />
                    MACD Signal
                </label>
                <label style={{ fontSize: '0.75rem', color: showRSI ? '#10b981' : '#64748b', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: showRSI ? 700 : 400 }}>
                    <input type="checkbox" checked={showRSI} onChange={() => setShowRSI(!showRSI)} style={{ cursor: 'pointer' }} />
                    RSI (14)
                </label>
            </div>
        </div>

        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chart_data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <XAxis dataKey="date" stroke="#475569" fontSize={10} tickFormatter={(val) => val.split('-')[1] + '/' + val.split('-')[0].slice(2)} minTickGap={30} />
            <YAxis yAxisId="price" stroke="#475569" fontSize={10} domain={['auto', 'auto']} tickFormatter={(val) => `₹${val}`} />
            { (showMACD || showMACDSignal) && <YAxis yAxisId="macd" orientation="right" stroke="#64748b" fontSize={10} domain={['auto', 'auto']} tickFormatter={(val) => val.toFixed(1)} /> }
            { showRSI && <YAxis yAxisId="rsi" orientation="right" stroke="#10b981" fontSize={10} domain={[0, 100]} /> }
            <RechartsTooltip
              contentStyle={{ background: 'rgba(15,23,42,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', fontSize: '0.8rem', boxShadow: '0 4px 6px rgba(0,0,0,0.3)' }}
              itemStyle={{ fontWeight: 700 }}
            />
            <Line yAxisId="price" type="monotone" dataKey="close" name="Close Price" stroke="var(--accent-cyan)" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: "var(--accent-cyan)", stroke: "transparent" }} />
            {show50DMA && <Line yAxisId="price" type="monotone" dataKey="dma_50" name="50-Day Moving Avg" stroke="#3b82f6" strokeWidth={1} dot={false} strokeDasharray="3 3" />}
            {show200DMA && <Line yAxisId="price" type="monotone" dataKey="dma_200" name="200-Day Moving Avg" stroke="#8b5cf6" strokeWidth={1} dot={false} strokeDasharray="3 3" />}
            {showMACD && <Line yAxisId="macd" type="monotone" dataKey="macd" name="MACD" stroke="#f59e0b" strokeWidth={1.5} dot={false} />}
            {showMACDSignal && <Line yAxisId="macd" type="monotone" dataKey="macd_signal" name="MACD Signal" stroke="#ef4444" strokeWidth={1.5} dot={false} strokeDasharray="4 4" />}
            {showRSI && <Line yAxisId="rsi" type="monotone" dataKey="rsi" name="RSI" stroke="#10b981" strokeWidth={1.5} dot={false} />}
          </LineChart>
        </ResponsiveContainer>
      </div>

    </div>
  );
}

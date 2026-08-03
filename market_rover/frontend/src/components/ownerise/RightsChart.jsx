import React from 'react';
import {
  LineChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  ReferenceLine,
  ReferenceArea,
  Label,
  ComposedChart
} from 'recharts';
import { TrendingUp, Activity, Calendar, BarChart3, Info, ShieldCheck } from 'lucide-react';

const RightsChart = ({ stockData, reData, symbol, timeline }) => {
  if (!stockData || stockData.length === 0) return null;

  // Prepare unified data stream to prevent X-axis domain fragmentation
  const unifiedData = stockData.map((d, index) => {
    const isHist = d.type === 'HISTORICAL';
    const isLastHist = isHist && (stockData[index + 1]?.type === 'FORECAST');

    return {
      ...d,
      // Only show area for historical points
      histPrice: isHist ? d.price : null,
      // Forecast line connects to the last historical point
      forecastPrice: (d.type === 'FORECAST' || isLastHist) ? d.price : null
    };
  });

  const isForecasting = stockData.some(d => d.type === 'FORECAST');

  return (
    <div style={{ marginTop: '2rem', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Main Stock Chart with Annotations & Volume */}
      <div style={{
        padding: '1.5rem',
        background: 'rgba(255,255,255,0.02)',
        borderRadius: '24px',
        border: '1px solid rgba(255,255,255,0.05)',
        position: 'relative'
      }}>
        {isForecasting && (
          <div style={{ position: 'absolute', top: '1.5rem', right: '1.5rem', display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', background: 'rgba(167,139,250,0.1)', border: '1px solid rgba(167,139,250,0.3)', borderRadius: '12px' }}>
            <ShieldCheck size={14} color="#a78bfa" />
            <span style={{ fontSize: '0.65rem', fontWeight: 800, color: '#a78bfa', letterSpacing: '1px' }}>COUNCIL OF EXPERTS FORECAST</span>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '1.1rem', fontWeight: 700 }}>
            <TrendingUp size={18} color="#22d3ee" /> {symbol} Institutional Lifecycle
          </h3>
        </div>

        <div style={{ width: '100%', height: 400 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={unifiedData}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#22d3ee" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis
                dataKey="date"
                stroke="#64748b"
                fontSize={10}
                tickFormatter={(str) => {
                  const d = new Date(str);
                  return d.toLocaleDateString('en-US', { day: 'numeric', month: 'short' });
                }}
              />
              <YAxis
                yAxisId="left"
                stroke="#64748b"
                fontSize={10}
                domain={['auto', 'auto']}
                tickFormatter={(val) => `₹${val}`}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="#64748b"
                fontSize={10}
                domain={[0, (dataMax) => dataMax * 3]}
                tickFormatter={(val) => `${(val/1000000).toFixed(0)}M`}
              />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                itemStyle={{ color: '#22d3ee' }}
                labelStyle={{ color: '#94a3b8' }}
              />

              {/* Shading for RE Trading Window (Amber Zone) */}
              {timeline && (
                <ReferenceArea
                  yAxisId="left"
                  x1={timeline.open_date}
                  x2={timeline.renunciation_date}
                  fill="rgba(245, 158, 11, 0.18)"
                  stroke="#f59e0b"
                  strokeOpacity={0.5}
                  strokeDasharray="3 3"
                />
              )}

              {/* Key Lifecycle Milestones */}
              {timeline && (
                <>
                  <ReferenceLine yAxisId="left" x={timeline.announcement_date} stroke="#94a3b8" strokeDasharray="3 3">
                    <Label value="ANNOUNCEMENT" position="top" fill="#94a3b8" fontSize={8} fontWeight={700} offset={20} />
                  </ReferenceLine>
                  <ReferenceLine yAxisId="left" x={timeline.record_date} stroke="#f43f5e" strokeDasharray="3 3">
                    <Label value="RECORD DATE" position="top" fill="#f43f5e" fontSize={9} fontWeight={800} offset={10} />
                  </ReferenceLine>
                  <ReferenceLine yAxisId="left" x={timeline.open_date} stroke="#10b981" strokeDasharray="3 3">
                    <Label value="ISSUE OPENS" position="top" fill="#10b981" fontSize={9} fontWeight={800} offset={10} />
                  </ReferenceLine>
                  <ReferenceLine yAxisId="left" x={timeline.close_date} stroke="#f59e0b" strokeDasharray="3 3">
                    <Label value="ISSUE CLOSES" position="top" fill="#f59e0b" fontSize={9} fontWeight={800} offset={10} />
                  </ReferenceLine>
                  <ReferenceLine yAxisId="left" x={timeline.listing_date} stroke="#a78bfa" strokeDasharray="3 3">
                    <Label value="LISTING" position="top" fill="#a78bfa" fontSize={9} fontWeight={800} offset={10} />
                  </ReferenceLine>
                </>
              )}

              <Bar
                yAxisId="right"
                dataKey="volume"
                fill="#475569"
                opacity={0.6}
                barSize={8}
              />

              {/* Historical Price Area */}
              <Area
                yAxisId="left"
                type="monotone"
                dataKey="histPrice"
                stroke="#22d3ee"
                strokeWidth={3}
                fillOpacity={1}
                fill="url(#colorPrice)"
                isAnimationActive={false}
                connectNulls={false}
              />

              {/* Forecast Price Line (Dashed) */}
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="forecastPrice"
                stroke="#a78bfa"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                activeDot={{ r: 6, fill: '#a78bfa' }}
                connectNulls={false}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>

        {/* Legend & Disclaimer */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '1.5rem' }}>
          <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.7rem', color: '#22d3ee' }}>
              <div style={{ width: 12, height: 2, background: '#22d3ee' }} /> Historical
            </div>
            {isForecasting && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.7rem', color: '#a78bfa' }}>
                <div style={{ width: 12, height: 2, borderBottom: '2px dashed #a78bfa' }} /> AI Forecast
              </div>
            )}
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.7rem', color: '#f59e0b', background: 'rgba(245,158,11,0.2)', padding: '2px 8px', borderRadius: '4px', fontWeight: 800 }}>
              AMBER ZONE: RE TRADING
            </div>
          </div>

          <div style={{ maxWidth: '350px', padding: '12px', background: 'rgba(0,0,0,0.3)', borderRadius: '12px', border: '1px solid rgba(244,63,94,0.2)' }}>
            <p style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.65rem', color: '#f43f5e', fontWeight: 900, marginBottom: '4px', textTransform: 'uppercase' }}>
              <Info size={12} /> Institutional Disclaimer
            </p>
            <p style={{ fontSize: '0.6rem', color: '#64748b', lineHeight: 1.4 }}>
              Forecasts are generated by the Market-Rover Council of Experts using Bayesian probability and historical rights-issue drift patterns. Past performance is not indicative of future results. Not financial advice.
            </p>
          </div>
        </div>
      </div>

      {/* Rights Entitlement Chart */}
      <div style={{
        padding: '1.5rem',
        background: 'rgba(255,255,255,0.02)',
        borderRadius: '24px',
        border: '1px solid rgba(255,255,255,0.05)'
      }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1.5rem', fontSize: '1.1rem', fontWeight: 700 }}>
          <Activity size={18} color="#f59e0b" /> {symbol}-RE Intrinsic Value Analysis
        </h3>
        <div style={{ width: '100%', height: 200 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={reData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
              <XAxis
                dataKey="date"
                stroke="#64748b"
                fontSize={10}
                tickFormatter={(str) => {
                  const d = new Date(str);
                  return d.toLocaleDateString('en-US', { day: 'numeric', month: 'short' });
                }}
              />
              <YAxis
                stroke="#64748b"
                fontSize={10}
                domain={['auto', 'auto']}
                tickFormatter={(val) => `₹${val}`}
              />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
                itemStyle={{ color: '#f59e0b' }}
                labelStyle={{ color: '#94a3b8' }}
              />

              {timeline && (
                <ReferenceLine x={timeline.renunciation_date} stroke="#f59e0b" strokeDasharray="5 5">
                   <Label value="LAST TRADING DAY" position="right" fill="#f59e0b" fontSize={8} fontWeight={700} />
                </ReferenceLine>
              )}

              <Line
                type="stepAfter"
                dataKey="price"
                stroke="#f59e0b"
                strokeWidth={3}
                dot={{ r: 4, fill: '#f59e0b', strokeWidth: 0 }}
                activeDot={{ r: 6, stroke: '#fff', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

const Badge = ({ text, color = '#22d3ee' }) => (
  <span style={{
    fontSize: '0.6rem', padding: '2px 8px',
    background: `${color}18`, color, borderRadius: '6px', fontWeight: 700, letterSpacing: '1px'
  }}>{text}</span>
);

export default RightsChart;

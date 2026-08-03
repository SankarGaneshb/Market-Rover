import React, { useState, useEffect, useCallback } from 'react';
import { Scale, TrendingUp, Wallet, AlertCircle } from 'lucide-react';

const ProfitLossCalculator = ({ details }) => {
  const [holdings, setHoldings] = useState(100);
  const [additional, setAdditional] = useState(0);
  const [results, setResults] = useState(null);

  const calculate = useCallback(async () => {
    // In a real app, this would call the /api/v1/ownerise/calculate endpoint
    // For now, we simulate the logic from calculations.py
    const oldRatio = details.old_shares_ratio;
    const newRatio = details.new_shares_ratio;
    const entitled = Math.floor((holdings / oldRatio) * newRatio);
    const totalApplied = entitled + additional;
    const capitalReq = totalApplied * details.issue_price;

    const currentVal = holdings * details.current_market_price;
    const totalCost = currentVal + capitalReq;
    const totalShares = holdings + totalApplied;
    const avgCost = totalShares > 0 ? totalCost / totalShares : 0;

    const terp = ((details.current_market_price * oldRatio) + (details.issue_price * newRatio)) / (oldRatio + newRatio);
    const paperProfit = (totalShares * terp) - totalCost;

    setResults({
      entitled,
      capitalReq,
      totalShares,
      avgCost,
      terp,
      paperProfit
    });
  }, [holdings, additional, details]);

  useEffect(() => {
    calculate();
  }, [calculate]);

  return (
    <div style={{ padding: '1.5rem', background: 'rgba(255,255,255,0.02)', borderRadius: '24px', border: '1px solid rgba(255,255,255,0.05)' }}>
      <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1.5rem', fontSize: '1.2rem', fontWeight: 800 }}>
        <Scale size={20} color="#10b981" /> Rights P&L Simulator
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        <div>
          <label style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 800, letterSpacing: '1px' }}>CURRENT HOLDINGS</label>
          <input
            type="number"
            value={holdings}
            onChange={(e) => setHoldings(parseInt(e.target.value) || 0)}
            style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', padding: '12px', borderRadius: '12px', color: 'white', marginTop: '8px' }}
          />
        </div>
        <div>
          <label style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 800, letterSpacing: '1px' }}>ADDITIONAL SHARES</label>
          <input
            type="number"
            value={additional}
            onChange={(e) => setAdditional(parseInt(e.target.value) || 0)}
            style={{ width: '100%', background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.1)', padding: '12px', borderRadius: '12px', color: 'white', marginTop: '8px' }}
          />
        </div>
      </div>

      {results && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
          <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <p style={{ fontSize: '0.65rem', color: '#94a3b8' }}>ENTITLED SHARES</p>
            <p style={{ fontSize: '1.2rem', fontWeight: 900, color: '#22d3ee' }}>{results.entitled}</p>
          </div>
          <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <p style={{ fontSize: '0.65rem', color: '#94a3b8' }}>CAPITAL REQUIRED</p>
            <p style={{ fontSize: '1.2rem', fontWeight: 900, color: '#10b981' }}>₹{results.capitalReq.toLocaleString()}</p>
          </div>
          <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <p style={{ fontSize: '0.65rem', color: '#94a3b8' }}>PROJECTED TERP</p>
            <p style={{ fontSize: '1.2rem', fontWeight: 900, color: '#f59e0b' }}>₹{results.terp.toFixed(2)}</p>
          </div>
          <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <p style={{ fontSize: '0.65rem', color: '#94a3b8' }}>EST. P&L</p>
            <p style={{ fontSize: '1.2rem', fontWeight: 900, color: results.paperProfit >= 0 ? '#10b981' : '#f43f5e' }}>
              ₹{results.paperProfit.toLocaleString()}
            </p>
          </div>
        </div>
      )}

      <div style={{ marginTop: '1.5rem', padding: '12px', background: 'rgba(245,158,11,0.08)', borderRadius: '12px', border: '1px solid rgba(245,158,11,0.2)', display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
        <AlertCircle size={16} color="#f59e0b" style={{ marginTop: '2px', flexShrink: 0 }} />
        <p style={{ fontSize: '0.75rem', color: '#d97706', lineHeight: 1.5 }}>
          <strong>Tax Note:</strong> Any profit from selling Rights Entitlements (RE) is considered Short-Term Capital Gains (STCG) with a cost of acquisition as Zero.
        </p>
      </div>
    </div>
  );
};

export default ProfitLossCalculator;

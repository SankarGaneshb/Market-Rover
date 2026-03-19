import React, { useEffect, useState } from 'react';
import { Activity, ShieldAlert, ArrowUpRight, TrendingDown, Users, Search } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const [promoters, setPromoters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch 7-day rolling window from Harvester backend
        const res = await fetch('/api/pledges/feed');
        if (res.ok) {
          const data = await res.json();
          setMetrics(data.metrics);
          
          // Fallback to local array mapping to retain the specific Governance UI colors if the backend just returns raw events
          // Since our core logic generates Governance Scores, we're blending the feed here.
        }
        
        // Simulating the /api/promoters list fetch replaced with actual backend call which uses mock_historical.py
        try {
          const promRes = await fetch('/api/promoters/');
          if (promRes.ok) {
            const promData = await promRes.json();
            const mappedPromoters = promData.map(p => ({
              ...p,
              risk: p.intent_label === 'Survival' ? 'High' : p.intent_label === 'Growth' ? 'Low' : 'Medium'
            }));
            setPromoters(mappedPromoters);
          }
        } catch (e) {
          console.error("Failed to fetch promoters from backend.");
        }
        console.error("Dashboard Fetch Error:", err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchDashboardData();
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Market Overview</h1>
          <p className="text-trust-silver text-sm">Real-time analysis of Promoter Pledging & Skin in the Game.</p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-400" />
          <input 
            type="text" 
            placeholder="Search NSE/BSE Symbol..." 
            className="bg-navy-800/50 border border-navy-600 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder:text-navy-400 focus:outline-none focus:ring-2 focus:ring-electric-cyan w-full md:w-64"
          />
        </div>
      </header>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-6 flex items-start justify-between group hover:border-electric-cyan/30 transition-colors">
          <div>
            <p className="text-sm font-medium text-navy-300 mb-1">Active Contagions</p>
            <h3 className="text-2xl font-bold text-white tracking-tight">{metrics ? metrics.active_contagions : '...'}</h3>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="p-2 bg-navy-900 rounded-lg border border-navy-700">
              <ShieldAlert className="w-5 h-5 text-red-400" />
            </div>
            {metrics && (
              <span className="text-xs font-semibold text-emerald-400 flex items-center">
                <ArrowUpRight className="w-3 h-3 mr-1" /> {metrics.trend_contagions}
              </span>
            )}
          </div>
        </div>
        
        <div className="glass-card p-6 flex items-start justify-between group hover:border-electric-cyan/30 transition-colors">
          <div>
            <p className="text-sm font-medium text-navy-300 mb-1">Total Pledged (NSE & BSE)</p>
            <h3 className="text-2xl font-bold text-white tracking-tight">{metrics ? metrics.total_pledged_cr : '...'}</h3>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="p-2 bg-navy-900 rounded-lg border border-navy-700">
              <Activity className="w-5 h-5 text-electric-cyan" />
            </div>
            {metrics && (
              <span className="text-xs font-semibold text-emerald-400 flex items-center">
                <ArrowUpRight className="w-3 h-3 mr-1" /> {metrics.trend_pledged}
              </span>
            )}
          </div>
        </div>

        <div className="glass-card p-6 flex items-start justify-between group hover:border-electric-cyan/30 transition-colors">
          <div>
            <p className="text-sm font-medium text-navy-300 mb-1">Promoters Tracked (7 Days)</p>
            <h3 className="text-2xl font-bold text-white tracking-tight">{metrics ? metrics.promoters_tracked : '...'}</h3>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="p-2 bg-navy-900 rounded-lg border border-navy-700">
              <Users className="w-5 h-5 text-trust-blue" />
            </div>
            {metrics && (
              <span className="text-xs font-semibold text-emerald-400 flex items-center">
                <ArrowUpRight className="w-3 h-3 mr-1" /> {metrics.trend_tracked}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Main Table */}
      <section className="glass-panel overflow-hidden">
        <div className="p-6 border-b border-navy-700/50 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Activity className="w-5 h-5 text-electric-cyan" />
            Recent Council Analysis
          </h2>
          <button className="text-sm text-electric-cyan hover:text-white transition-colors">View All Feed</button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-trust-silver">
            <thead className="text-xs uppercase bg-navy-900/50 text-navy-300 border-b border-navy-700/50">
              <tr>
                <th className="px-6 py-4 font-medium">Symbol</th>
                <th className="px-6 py-4 font-medium">Company</th>
                <th className="px-6 py-4 font-medium">Skin / Survival</th>
                <th className="px-6 py-4 font-medium">Contagion Risk</th>
                <th className="px-6 py-4 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-6 py-12 text-center text-navy-400">
                    <div className="animate-pulse flex flex-col items-center">
                      <div className="w-8 h-8 border-2 border-electric-cyan border-t-transparent rounded-full animate-spin mb-4"></div>
                      <p>The Council is gathering intelligence...</p>
                    </div>
                  </td>
                </tr>
              ) : (
                promoters.map((p) => (
                  <tr key={p.symbol} className="border-b border-navy-700/30 hover:bg-navy-800/40 transition-colors group">
                    <td className="px-6 py-4 font-bold text-white group-hover:text-electric-cyan transition-colors">
                      {p.symbol}
                    </td>
                    <td className="px-6 py-4">{p.company_name}</td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-navy-400 w-16">Skin %</span>
                          <div className="w-full bg-navy-700 rounded-full h-1.5 max-w-[80px]">
                            <div 
                              className={`h-1.5 rounded-full ${p.skin_in_the_game > 60 ? 'bg-emerald-400' : p.skin_in_the_game > 30 ? 'bg-amber-400' : 'bg-red-500'}`}
                              style={{ width: `${p.skin_in_the_game}%` }}
                            ></div>
                          </div>
                          <span className="font-mono text-xs">{p.skin_in_the_game.toFixed(1)}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-navy-400 w-16">Survival</span>
                          <div className="w-full bg-navy-700 rounded-full h-1.5 max-w-[80px]">
                            <div 
                              className={`h-1.5 rounded-full ${p.survival_score < 30 ? 'bg-emerald-400' : p.survival_score < 60 ? 'bg-amber-400' : 'bg-red-500'}`}
                              style={{ width: `${p.survival_score}%` }}
                            ></div>
                          </div>
                          <span className="font-mono text-xs">{p.survival_score.toFixed(0)}</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                       <span className={`px-2 py-1 rounded-md text-xs font-semibold ${
                         p.risk === 'Low' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 
                         p.risk === 'High' ? 'bg-red-500/10 text-red-400 border border-red-500/20 shadow-[0_0_10px_rgba(239,68,68,0.2)]' : 
                         'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                       }`}>
                         {p.risk}
                       </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link to={`/promoter/${p.symbol}`} className="btn-accent text-xs py-1.5 px-3 inline-flex items-center">
                        View Dossier <ArrowUpRight className="w-3 h-3 ml-1" />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

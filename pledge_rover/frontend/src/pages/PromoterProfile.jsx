import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, ShieldAlert, Cpu, GitMerge, FileText, CheckCircle2, TrendingDown, Network } from 'lucide-react';
import ShadowNetworkGraph from '../components/ShadowNetworkGraph';

const DOSSIER_DATA = {
  'LLOYDSME': {
    title: 'Lloyds Metals And Energy',
    score: '3.8',
    skin: '76.8% (Normalized)',
    danger: true,
    a1: 'Extracted SAST Regulation 31 from NSE. Pledgor: Thriveni Earthmovers Private Limited. Total encumbered now sits at 1,31,21,610 shares (high percentage of promoter holding).',
    a2: 'Shadow Track complete. Thriveni Earthmovers is a key promoter entity. Cross-referencing LEI and Pledgee attachments: This pledge is tied to heavy capital expenditure and working capital requirements for mining operations. Normalized Skin in the Game calculated at 76.8% of SEBI limit.',
    a3: 'Alert. LTV ratio sits at elevated levels. Calculating trigger price... Current market price is ₹845. Estimated margin call trigger is ₹750.',
    a3_alert: 'Contagion proximity: 11.2% (Danger Zone)',
    synthesis: '"This is a mix of Survival and Aggressive Growth Pledging. The promoter structure relies heavily on pledging for massive mining capex. The Actuary\'s margin trigger of ₹750 is plausible if iron ore prices face a sudden macro shock."',
    sentiment: 'Cautious on Corporate Governance Risk',
    action: 'Flag for Institutional Monitoring'
  },
  'DEEPAKFERT': {
    title: 'Deepak Fertilizers',
    score: '6.2',
    skin: '56.4% (Normalized)',
    danger: false,
    a1: 'Extracted SAST Regulation 31. Pledgor: Robust Marketing Services. 29,05,000 shares newly encumbered.',
    a2: 'Traced Pledgee to major banking consortium. Purpose matched against recent quarterly announcements: Debt servicing for newly commissioned ammonia plant. Normalized Skin in Game is robust at 56.4%.',
    a3: 'LTV is stable at 2.1x. Current price ₹620. Margin trigger at ₹510.',
    a3_alert: 'Contagion proximity: 21% (Safe Zone)',
    synthesis: '"This is standard Growth Pledging for heavy industrial expansion. Cash flows from the new plant should cover the debt servicing. Systemic contagion risk is low unless the ammonia cycle crashes."',
    sentiment: 'Neutral (Capex Cycle)',
    action: 'Standard Monitoring'
  },
  'NOCIL': {
    title: 'NOCIL Limited',
    score: '8.5',
    skin: '50.6% (Normalized)',
    danger: false,
    a1: 'Extracted SAST Regulation 31. Pledgor: Gurukripa Trust. Pledged 67,00,000 shares.',
    a2: 'Trustee structure maps directly to original promoter family. Pledge is for personal liquidity, not corporate debt. No shadow NBFCs detected. Promoter retains 50.6% Normalized Skin in the Game.',
    a3: 'LTV is extremely conservative (1.4x). CMP ₹305. Margin call trigger ₹160.',
    a3_alert: 'Contagion proximity: >45% (Safe Zone)',
    synthesis: '"Classic low-risk pledge. The borrowing is isolated from corporate operations and heavily collateralized. Zero systemic contagion threat observed."',
    sentiment: 'Positive Governance',
    action: 'Clear for Portfolio Allocation'
  },
  'AJANTPHARM': {
    title: 'Ajanta Pharma',
    score: '9.1',
    skin: '84.9% (Normalized)',
    danger: false,
    a1: 'Extracted SAST Reg 31. Pledgor: Aayush Agrawal Trust. 79,98,848 shares pledged.',
    a2: 'Clean corporate structure. Very few shadow entities. Encumbrance represents a fraction of total family net worth. Normalized Skin in Game remains extremely high at ~85%.',
    a3: 'Minimal LTV. CMP ₹2600. Trigger ₹1800.',
    a3_alert: 'Contagion proximity: 30% (Safe Zone)',
    synthesis: '"Governance checks highlight extremely robust capital structure. Pledging is incidental, not operational. No risk markers triggered."',
    sentiment: 'Strong Positive',
    action: 'Clear'
  },
  'CAMLINFINE': {
    title: 'Camlin Fine Sciences',
    score: '4.5',
    skin: '38.0% (Normalized)',
    danger: true,
    a1: 'Extracted SAST Reg 31. Pledgor: Ashish Subhash Dandekar. 88,00,000 shares pledged.',
    a2: 'Tracing identifies pledges linked to high-yield debt to fund foreign acquisitions (Mexico/Italy subsidiaries). Complex cross-border holding structures detected. Normalized Skin in Game dipping critically to 38.0%.',
    a3: 'LTV creeping higher as stock faces headwinds. CMP ₹112. Trigger ₹90.',
    a3_alert: 'Contagion proximity: 19% (Warning Zone)',
    synthesis: '"Aggressive inorganic Growth Pledging. While not immediately in survival mode, the high-cost debt tied to foreign subsidiaries puts pressure on the Indian parent holding."',
    sentiment: 'Elevated Risk Mismatch',
    action: 'Review Quarterly Debt Profile'
  }
};

export default function PromoterProfile() {
  const { symbol } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPromoterData = async () => {
      try {
        const res = await fetch(`/api/promoters/${symbol}`);
        if (res.ok) {
           const pData = await res.json();
           
           // Synthesize the AI text locally for now until AI Council prompt is fully integrated
           // Create mock network data based on symbol
           let mockNetwork = { nodes: [], edges: [] };
           if (symbol === 'LLOYDSME') {
             mockNetwork = {
               nodes: [
                 { id: '1', type: 'glass', position: { x: 250, y: 50 }, data: { label: 'Thriveni Earthmovers', entityType: 'promoter', description: 'Key Promoter Entity' } },
                 { id: '2', type: 'glass', position: { x: 250, y: 250 }, data: { label: 'Banking Consortium', entityType: 'lender_safe', description: 'Working Capital & Capex' } }
               ],
               edges: [
                 { id: 'e1-2', source: '1', target: '2', animated: true, label: 'Pledge (1.31Cr)' }
               ]
             };
           } else if (symbol === 'CAMLINFINE') {
             mockNetwork = {
               nodes: [
                 { id: '1', type: 'glass', position: { x: 250, y: 50 }, data: { label: 'Ashish Dandekar', entityType: 'promoter', description: 'Primary Promoter' } },
                 { id: '2', type: 'glass', position: { x: 100, y: 250 }, data: { label: 'High-Yield Fund', entityType: 'lender_risky', description: 'Expensive Foreign Debt' } },
                 { id: '3', type: 'glass', position: { x: 400, y: 250 }, data: { label: 'Mexico Subsidiary', entityType: 'subsidiary', description: 'Acquisition Target' } }
               ],
               edges: [
                 { id: 'e1-2', source: '1', target: '2', animated: true, label: 'Pledge (88L)' },
                 { id: 'e1-3', source: '1', target: '3', animated: true, label: 'Capital Flow' }
               ]
             };
           } else {
             mockNetwork = {
               nodes: [
                 { id: '1', type: 'glass', position: { x: 250, y: 50 }, data: { label: pData.company_name + ' Promoter', entityType: 'promoter', description: 'Core Holding' } },
                 { id: '2', type: 'glass', position: { x: 250, y: 250 }, data: { label: 'Primary Lender', entityType: pData.intent_label === 'Survival' ? 'lender_risky' : 'lender_safe', description: 'Credit Facility' } }
               ],
               edges: [
                 { id: 'e1-2', source: '1', target: '2', animated: true, label: 'Encumbrance' }
               ]
             };
           }

           const dynamicData = {
              title: pData.company_name,
              score: pData.governance_score.toFixed(1),
              holding: pData.holding_pct ? pData.holding_pct.toFixed(1) + '%' : 'N/A',
              prePledge: pData.holding_pct ? pData.holding_pct.toFixed(1) + '%' : '0%',
              postPledge: (pData.holding_pct - pData.pledged_pct).toFixed(1) + '%',
              pledgedOfHolding: pData.holding_pct > 0 ? ((pData.pledged_pct / pData.holding_pct) * 100).toFixed(1) + '%' : '0%',
              skin: pData.skin_in_the_game.toFixed(1) + '%',
              danger: pData.intent_label === 'Survival',
              a1: `Extracted SAST Regulation 31. Total encumbered stands at ${pData.pledged_pct}% of total shares.`,
              a2: `Pledgee tracked. Lender quality falls under: ${pData.trust_signal}. Skin in the Game computation: Layer1 Commitment is ${pData.skin_layer1}%, Layer2 Concentration is ${pData.skin_layer2}.`,
              a3: `Survival computation signals a ${pData.intent_label} pattern with score ${pData.survival_score.toFixed(0)}/100. Release-to-create ratio is ${pData.release_create_ratio}x.`,
              a3_alert: pData.intent_label === 'Survival' ? 'Contagion proximity: Warning Zone' : 'Contagion proximity: Safe Zone',
              synthesis: `This represents a ${pData.intent_label} pledging pattern based on the 8-quarter time-series analysis.`,
              sentiment: pData.intent_label === 'Survival' ? 'Cautious on Corporate Governance Risk' : 'Neutral/Positive',
              action: pData.intent_label === 'Survival' ? 'Flag for Institutional Monitoring' : 'Clear for Allocation',
              network: mockNetwork
           };
           setData(dynamicData);
        }
      } catch (err) {
        console.error("Failed to fetch promoter", err);
      } finally {
        setLoading(false);
      }
    };
    fetchPromoterData();
  }, [symbol]);

  if (loading || !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
         <Cpu className="w-12 h-12 text-electric-cyan animate-pulse mb-6" />
         <h2 className="text-xl font-display text-white mb-2">Accessing Agent Intelligence...</h2>
         <p className="text-navy-400 text-sm">The Genealogist is tracing LEI records for {symbol}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <Link to="/" className="inline-flex items-center text-sm text-navy-300 hover:text-white transition-colors">
        <ArrowLeft className="w-4 h-4 mr-2" /> Back to Intelligence Feed
      </Link>

      <header className={`glass-panel p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 border-l-4 ${data.danger ? 'border-l-red-500' : 'border-l-trust-blue'}`}>
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-4xl font-bold text-white tracking-tight">{symbol}</h1>
            {data.danger && (
              <span className="bg-red-500/10 text-red-500 border border-red-500/20 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider flex items-center shadow-[0_0_15px_rgba(239,68,68,0.3)]">
                <ShieldAlert className="w-3 h-3 mr-1" /> Contagion Risk
              </span>
            )}
          </div>
          <p className="text-xl text-trust-silver font-display">{data.title} Target Analysis</p>
        </div>
        
        <div className="flex gap-4 md:gap-8 bg-navy-900/50 p-4 rounded-xl border border-navy-700">
          <div className="text-center">
            <p className="text-xs text-navy-400 uppercase tracking-wider mb-1">Gov Score</p>
            <p className="text-xl md:text-3xl font-mono text-white">{data.score}<span className="text-sm text-navy-500">/10</span></p>
          </div>
          <div className="w-px bg-navy-700"></div>
          <div className="text-center">
            <p className="text-xs text-navy-400 uppercase tracking-wider mb-1">Sys Holding</p>
            <p className="text-xl md:text-3xl font-mono text-white">{data.holding}</p>
          </div>
          <div className="w-px bg-navy-700"></div>
          <div className="text-center">
            <p className="text-xs text-navy-400 uppercase tracking-wider mb-1" title="Calculated as unencumbered holding relative to SEBI's 75% max limit">Norm Skin</p>
            <p className={`text-xl md:text-3xl font-mono ${data.danger ? 'text-red-400' : 'text-emerald-400'}`}>{data.skin}</p>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: The Agentic Medallion Logs */}
        <div className="lg:col-span-2 space-y-6">
          <section className="glass-card p-6 h-full">
            <h2 className="text-xl font-semibold text-white mb-6 border-b border-navy-700 pb-3 flex items-center">
              <Cpu className="w-5 h-5 mr-2 text-trust-blue" />
              The Council's Debate Log
            </h2>
            
            <div className="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-navy-600 before:to-transparent">
              
              {/* Agent 1 */}
              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                <div className="flex items-center justify-center w-10 h-10 rounded-full border-2 border-trust-blue bg-navy-900 shadow-[0_0_10px_rgba(21,101,192,0.5)] shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 text-trust-blue z-10">
                  <FileText className="w-4 h-4" />
                </div>
                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] glass-panel p-4 border-trust-blue/30 relative">
                   <div className="flex items-center justify-between mb-2">
                     <span className="text-xs font-bold text-trust-blue uppercase tracking-wider">The Harvester</span>
                     <span className="text-xs text-navy-400 whitespace-nowrap">09:42 AM</span>
                   </div>
                   <p className="text-sm text-trust-silver leading-relaxed">
                     {data.a1}
                   </p>
                </div>
              </div>

              {/* Agent 2 */}
              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                <div className="flex items-center justify-center w-10 h-10 rounded-full border-2 border-electric-cyan bg-navy-900 shadow-glow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 text-electric-cyan z-10">
                  <GitMerge className="w-4 h-4" />
                </div>
                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] glass-panel p-4 border-electric-cyan/30 relative">
                   <div className="flex items-center justify-between mb-2">
                     <span className="text-xs font-bold text-electric-cyan uppercase tracking-wider">The Genealogist</span>
                     <span className="text-xs text-navy-400 whitespace-nowrap">09:44 AM</span>
                   </div>
                   <p className="text-sm text-trust-silver leading-relaxed">
                     {data.a2}
                   </p>
                </div>
              </div>

              {/* Agent 3 */}
              <div className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                <div className="flex items-center justify-center w-10 h-10 rounded-full border-2 border-red-500 bg-navy-900 shadow-[0_0_15px_rgba(239,68,68,0.5)] shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 text-red-500 z-10">
                  <TrendingDown className="w-4 h-4" />
                </div>
                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] glass-panel p-4 border-red-500/30 relative">
                   <div className="flex items-center justify-between mb-2">
                     <span className="text-xs font-bold text-red-500 uppercase tracking-wider">The Actuary</span>
                     <span className="text-xs text-navy-400 whitespace-nowrap">09:45 AM</span>
                   </div>
                   <p className="text-sm text-trust-silver leading-relaxed">
                     {data.a3}
                     <span className={`block mt-2 font-medium ${data.danger ? 'text-red-400' : 'text-emerald-400'}`}>{data.a3_alert}</span>
                   </p>
                </div>
              </div>

            </div>
          </section>
        </div>

        {/* Right Col: Synthesis & Impact */}
        <div className="space-y-6">
          <section className="glass-panel p-6 border-t-2 border-t-trust-blue">
             <h3 className="text-sm uppercase tracking-wider text-navy-400 font-bold mb-4">Pledge Impact Analysis</h3>
             <div className="space-y-3">
               <div className="flex justify-between items-center text-sm">
                 <span className="text-trust-silver">Pre-Pledge Holding</span>
                 <span className="font-mono text-white">{data.prePledge}</span>
               </div>
               <div className="flex justify-between items-center text-sm">
                 <span className="text-trust-silver">Post-Pledge Holding <span className="text-[10px] text-navy-400 ml-1">(Unencumbered)</span></span>
                 <span className="font-mono text-emerald-400">{data.postPledge}</span>
               </div>
               <div className="w-full bg-navy-700 h-px my-2"></div>
               <div className="flex justify-between items-center text-sm">
                 <span className="text-trust-silver">Holding Pledged</span>
                 <span className="font-mono text-red-400">{data.pledgedOfHolding}</span>
               </div>
             </div>
          </section>

          <section className="glass-panel p-6 border-t-2 border-t-electric-cyan">
             <h3 className="text-sm uppercase tracking-wider text-navy-400 font-bold mb-4">Skeptic Synthesis</h3>
             <div className="prose prose-invert prose-sm">
               <p className="text-white" dangerouslySetInnerHTML={{__html: data.synthesis.replace('Survival', '<strong class=\'text-red-400\'>Survival</strong>').replace('Growth', '<strong class=\'text-emerald-400\'>Growth</strong>')}}></p>
               <br/>
               <div className="bg-navy-900/80 p-3 rounded-lg border border-navy-700">
                 <h4 className="flex items-center text-trust-silver font-semibold mb-2">
                   <CheckCircle2 className="w-4 h-4 mr-2 text-trust-blue" /> Final Resolution
                 </h4>
                 <ul className="space-y-1 pl-6 list-disc text-trust-silver">
                   <li>Net Effective Holding: <span className={`font-bold ${data.danger ? 'text-red-400' : 'text-emerald-400'}`}>{data.skin}</span></li>
                   <li>Sentiment: {data.sentiment}.</li>
                   <li>Recommendation: {data.action}.</li>
                 </ul>
               </div>
             </div>
          </section>

          {/* New Methodology Box */}
          <section className="glass-panel p-6 border-t-2 border-t-trust-silver mt-6">
             <h3 className="text-sm uppercase tracking-wider text-navy-400 font-bold mb-4 flex items-center">
               <FileText className="w-4 h-4 mr-2" /> Methodology & Formulas
             </h3>
             <div className="space-y-4 text-xs text-trust-silver leading-relaxed">
               <div>
                 <strong className="text-white text-sm">Gov Score (The Council Rating)</strong>
                 <p className="mt-1">A qualitative risk score (1-10) debated and finalized by The Skeptic. It heavily penalizes "Survival" intent, obscure shadow lenders (non-Tier 1 banks), and elevated Loan-to-Value (LTV) ratios approaching the Contagion Zone.</p>
               </div>
               <div className="w-full bg-navy-700 h-px my-2"></div>
               <div>
                 <strong className="text-white text-sm">Norm Skin (Normalized Skin in the Game)</strong>
                 <p className="mt-1">Since SEBI limits maximum promoter holding to 75% (to maintain a 25% minimum float), an 80% holding is technically impossible. This metric converts raw unencumbered holding into an *effective* commitment relative to the highest legally permissible holding.</p>
                 <code className="block bg-navy-900/50 p-2 mt-2 rounded border border-navy-700 font-mono text-electric-cyan text-[10px] shadow-inner">
                   Formula: ((Raw Holding % - Pledged %) ÷ 75%) × 100
                 </code>
               </div>
               <div className="w-full bg-navy-700 h-px my-2"></div>
               <div>
                 <strong className="text-white text-sm">Layer 1 & Layer 2 Commitment</strong>
                 <p className="mt-1"><span className="text-trust-blue font-semibold">Layer 1:</span> The promoter's direct, unencumbered shareholding (highest accountability).<br/><span className="text-orange-400 font-semibold">Layer 2:</span> The percentage of holding routed through opaque shell entities, trusts, or LLPs. High Layer 2 indicates risk obfuscation.</p>
               </div>
               <div className="w-full bg-navy-700 h-px my-2"></div>
               <div>
                 <strong className="text-white text-sm">Release-to-Create Ratio</strong>
                 <p className="mt-1">An 8-quarter rolling ratio tracking shares being released from pledge vs new pledges being created. A ratio {">"} 1.0x implies debt reduction and health; ratio {"<"} 1.0x implies heavy debt dependency.</p>
               </div>
               <div className="w-full bg-navy-700 h-px my-2"></div>
               <div>
                 <strong className="text-white text-sm">Contagion Proximity</strong>
                 <p className="mt-1">The percentage drop required from the Current Market Price (CMP) to trigger the Actuary's Margin Call Trigger Price. The closer to 0%, the higher the immediate risk of a systemic institutional sell-off.</p>
                 <code className="block bg-navy-900/50 p-2 mt-2 rounded border border-navy-700 font-mono text-electric-cyan text-[10px] shadow-inner">
                   Formula: ((CMP - Trigger Price) ÷ CMP) × 100
                 </code>
               </div>
             </div>
          </section>
        </div>

      </div>

      {/* Bottom Full-Width Row: Network Visualization */}
      <section className="glass-panel p-6 border-t-2 border-t-electric-cyan mt-6">
        <h2 className="text-xl font-semibold text-white mb-2 border-b border-navy-700 pb-3 flex items-center">
          <Network className="w-5 h-5 mr-2 text-electric-cyan" />
          The Genealogist's Shadow Network
        </h2>
        <p className="text-sm text-trust-silver mb-6">Interactive map of entity relationships, shadow holding companies, and the lender network.</p>
        <ShadowNetworkGraph initialNodes={data.network.nodes} initialEdges={data.network.edges} />
      </section>
    </div>
  );
}

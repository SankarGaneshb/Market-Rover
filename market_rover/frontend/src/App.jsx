import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  LineChart, TrendingUp, Shield, Target, User, Zap, Gamepad2,
  Activity, AlertTriangle, CheckCircle, Briefcase, ExternalLink,
  ChevronRight, Database, Calendar, Layers, Search, History,
  LogOut, Globe, Eye, BarChart2, Flame, ChevronDown
} from 'lucide-react';
import Confetti from 'react-confetti';
import { motion, AnimatePresence } from 'framer-motion';

// ── Base URL — Vite proxy handles /api  in dev, nginx in prod ──────────────────
const API = '';

// ── Helpers ───────────────────────────────────────────────────────────────────

const api = axios.create({ baseURL: API });

const SidebarItem = ({ icon, label, active, onClick, external }) => (
  <button
    id={`nav-${label.toLowerCase().replace(/\s+/g, '-')}`}
    onClick={onClick}
    style={{
      width: '100%', display: 'flex', alignItems: 'center',
      justifyContent: 'space-between', padding: '0.85rem 1.2rem',
      borderRadius: '12px', border: 'none',
      background: active ? 'rgba(0,255,242,0.1)' : 'transparent',
      color: active ? 'var(--accent-cyan)' : 'var(--text-secondary)',
      cursor: 'pointer', transition: 'all 0.3s ease',
      marginBottom: '0.5rem', fontSize: '0.9rem'
    }}
    onMouseEnter={e => !active && (e.currentTarget.style.background = 'rgba(255,255,255,0.04)')}
    onMouseLeave={e => !active && (e.currentTarget.style.background = 'transparent')}
  >
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
      {icon}<span>{label}</span>
    </div>
    {external ? <ExternalLink size={14} /> : active && <ChevronRight size={16} />}
  </button>
);

const Badge = ({ text, color = '#22d3ee' }) => (
  <span style={{
    fontSize: '0.6rem', padding: '2px 8px',
    background: `${color}18`, color, borderRadius: '6px', fontWeight: 700
  }}>{text}</span>
);

const GlassCard = ({ children, style = {} }) => (
  <div className="glass-card" style={style}>{children}</div>
);

const SectionHeader = ({ icon, title, sub }) => (
  <div style={{ marginBottom: '1.5rem' }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
      {icon}
      <h2 style={{ fontSize: '1.8rem', fontWeight: 800 }}>{title}</h2>
    </div>
    {sub && <p style={{ color: '#64748b', fontSize: '0.9rem', marginTop: '0.4rem' }}>{sub}</p>}
  </div>
);

// ── Heatmap Cell Component ─────────────────────────────────────────────────────

const HeatCell = ({ val }) => {
  if (val === null || val === undefined) {
    return <td style={{ padding: '6px', fontSize: '0.7rem', color: '#334155', textAlign: 'center' }}>–</td>;
  }
  const abs = Math.min(Math.abs(val), 12);
  const intensity = abs / 12;
  const bg = val >= 0
    ? `rgba(16,185,129,${0.1 + intensity * 0.7})`
    : `rgba(244,63,94,${0.1 + intensity * 0.7})`;
  return (
    <td style={{
      padding: '6px 8px', fontSize: '0.72rem', fontWeight: 700,
      textAlign: 'center', borderRadius: '6px', background: bg,
      color: val >= 0 ? '#10b981' : '#f43f5e', minWidth: '52px',
      transition: 'background 0.2s'
    }}>
      {val > 0 ? '+' : ''}{val.toFixed(1)}%
    </td>
  );
};

// ── Main App ──────────────────────────────────────────────────────────────────

const App = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [socialIdentity, setSocialIdentity] = useState({ handle: '', provider: '' });
  const [activeTab, setActiveTab] = useState('dashboard');
  const [persona, setPersona] = useState('Not Set');
  const [showConfetti, setShowConfetti] = useState(false);

  // ── Dashboard (Intelligence Hub) ──
  const [tickers, setTickers] = useState('TCS.NS, RELIANCE.NS, INFY.NS');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [report, setReport] = useState('');
  const [findings, setFindings] = useState([]);
  const [traditionalInsights, setTraditionalInsights] = useState([]);

  // ── Profile (Sleep Test) ──
  const [quizStep, setQuizStep] = useState(0);
  const [quizScores, setQuizScores] = useState({ q1: 2, q2: 2, q3: 2 });

  // ── Forecast ──
  const [forecasts, setForecasts] = useState([]);

  // ── Shadow ──
  const [shadowSignals, setShadowSignals] = useState([]);
  const [shadowLoading, setShadowLoading] = useState(false);

  // ── Calendar ──
  const [muhurthamWindows, setMuhurthamWindows] = useState([]);
  const [seasonalPatterns, setSeasonalPatterns] = useState([]);
  const [calLoaded, setCalLoaded] = useState(false);

  // ── Heatmap ──
  const [heatTicker, setHeatTicker] = useState('TCS.NS');
  const [heatData, setHeatData] = useState(null);
  const [heatLoading, setHeatLoading] = useState(false);
  const [heatError, setHeatError] = useState('');

  // ── Auth Handlers ──────────────────────────────────────────────────────────

  const handleCallback = useCallback(async (code, provider = 'Google') => {
    try {
      setIsAnalyzing(true);
      // Determine the correct callback endpoint based on the provider
      const endpoint = `/api/auth/${provider.toLowerCase()}/callback`;
      const { data } = await api.post(endpoint, { code });

      if (data.handle) {
        setSocialIdentity({ handle: data.handle, provider: data.provider || provider });
        setIsLoggedIn(true);
        // Clean the URL
        window.history.replaceState({}, document.title, window.location.pathname);
      }
    } catch (e) {
      const detail = e.response?.data?.error || e.message;
      alert(`Social Auth Failed [${provider}]: ${detail}`);
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const handleLogin = async (provider) => {
    try {
      const { data } = await api.get(`/api/auth/${provider.toLowerCase()}/url`);
      if (data.url) window.location.href = data.url;
    } catch (e) {
      alert(`${provider} connection failed. Is the backend running?`);
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setSocialIdentity({ handle: '', provider: '' });
    setPersona('Not Set');
    setActiveTab('dashboard');
  };

  // ── Profile ────────────────────────────────────────────────────────────────

  const fetchProfile = useCallback(async () => {
    try {
      const res = await api.get(`/api/profile/${socialIdentity.handle}`);
      const fetchedPersona = res.data.persona || 'Not Set';
      setPersona(fetchedPersona);
      // Force new users to the calibration screen immediately
      if (fetchedPersona === 'Not Set') {
        setActiveTab('profile');
      }
    } catch (e) { console.error('fetchProfile:', e); }
  }, [socialIdentity.handle]);

  const updatePersona = async (newPersona) => {
    try {
      await api.post('/api/profile', { user_handle: socialIdentity.handle, persona: newPersona });
      setPersona(newPersona);
    } catch (e) { console.error('updatePersona:', e); }
  };

  const submitQuiz = async (finalScores = quizScores) => {
    try {
      const { data } = await api.post('/api/profile/analyze', finalScores);
      await updatePersona(data.persona);
      setQuizStep(0);
      setShowConfetti(true);
      // Auto-navigate to Market Analysis (Dashboard) after calibration
      setTimeout(() => {
        setShowConfetti(false);
        setActiveTab('dashboard');
      }, 3000);
    } catch (e) {
      alert('Calibration failed. Check your connection.');
    }
  };

  // ── Analysis ───────────────────────────────────────────────────────────────

  const runAnalysis = async () => {
    setIsAnalyzing(true);
    setReport('');
    setFindings([]);
    try {
      const { data } = await api.post('/api/analyze', {
        tickers: tickers.split(',').map(t => t.trim()),
        discoverable_handle: socialIdentity.handle
      });

      // Async polling mechanism
      const taskId = data.task_id;
      const pollTimer = setInterval(async () => {
        try {
          const res = await api.get(`/api/analyze/status/${taskId}`);
          if (res.data.status === 'completed') {
            clearInterval(pollTimer);
            const result = res.data.result;
            setReport(result.final_report || '');
            setTraditionalInsights(result.traditional_insights || []);
            setFindings([
              ...(result.technical_data || []),
              ...(result.dividend_data || []),
              ...(result.forensic_reports || []),
              ...(result.shadow_signals || []).map(s => ({ type: 'SHADOW', message: s }))
            ]);
            if (result.celebrations?.some(c => c.type === 'FINAL_CONFETTI_BURST')) {
              setShowConfetti(true);
              setTimeout(() => setShowConfetti(false), 5000);
            }
            setIsAnalyzing(false);
          } else if (res.data.status === 'failed') {
            clearInterval(pollTimer);
            setReport('Analysis failed: ' + res.data.error);
            setIsAnalyzing(false);
          }
        } catch (err) {
          clearInterval(pollTimer);
          setReport('Error polling analysis status.');
          setIsAnalyzing(false);
        }
      }, 2000);
    } catch (e) {
      setReport('Analysis failed to start. Check the backend connection.');
      console.error('runAnalysis:', e);
      setIsAnalyzing(false);
    }
  };

  // ── Forecasts ──────────────────────────────────────────────────────────────

  const fetchForecasts = useCallback(async () => {
    try {
      const res = await api.get(`/api/forecasts/${socialIdentity.handle}`);
      setForecasts(res.data);
    } catch (e) { console.error('fetchForecasts:', e); }
  }, [socialIdentity.handle]);

  // ── Shadow ─────────────────────────────────────────────────────────────────

  const fetchShadow = useCallback(async () => {
    setShadowLoading(true);
    try {
      const res = await api.get(`/api/shadow?user_handle=${socialIdentity.handle}`);
      setShadowSignals(res.data.shadow_signals || []);
    } catch (e) { console.error('fetchShadow:', e); }
    finally { setShadowLoading(false); }
  }, [socialIdentity.handle]);

  // ── Calendar ───────────────────────────────────────────────────────────────

  const fetchCalendar = useCallback(async () => {
    if (calLoaded) return;
    try {
      const res = await api.get('/api/calendar');

      // Adapt the unified calendar format to split arrays
      const calData = res.data.calendar || [];
      const windows = calData.filter(c => c.type === 'Buy' || c.type === 'Sell').map(w => ({
          name: w.event, date: w.month, note: w.type + ' action recommended.'
      }));
      const seasonals = calData.filter(c => c.type === 'Accumulate' || c.type === 'Hold').map(s => ({
          season: s.event, months: s.month, note: s.type + ' logic applies.'
      }));

      setMuhurthamWindows(windows);
      setSeasonalPatterns(seasonals);
      setCalLoaded(true);
    } catch (e) { console.error('fetchCalendar:', e); }
  }, [calLoaded]);

  // ── Heatmap ────────────────────────────────────────────────────────────────

  const fetchHeatmap = async () => {
    setHeatLoading(true);
    setHeatError('');
    setHeatData(null);
    try {
      const res = await api.get(`/api/heatmap/${heatTicker}`);
      setHeatData(res.data);
    } catch (e) {
      setHeatError(e.response?.data?.error || 'Heatmap data unavailable.');
    } finally { setHeatLoading(false); }
  };

  // ── Effects ────────────────────────────────────────────────────────────────

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const provider = params.get('state') || 'Google'; // Default to Google
    if (code && !isLoggedIn) handleCallback(code, provider);
  }, [handleCallback, isLoggedIn]);

  useEffect(() => {
    if (!isLoggedIn || !socialIdentity.handle) return;
    fetchProfile();
  }, [isLoggedIn, socialIdentity.handle, fetchProfile]);

  useEffect(() => {
    if (!isLoggedIn || !socialIdentity.handle) return;
    if (activeTab === 'forecasts') fetchForecasts();
    if (activeTab === 'shadow') fetchShadow();
    if (activeTab === 'calendar') fetchCalendar();
  }, [activeTab, isLoggedIn, socialIdentity.handle, fetchForecasts, fetchShadow, fetchCalendar]);

  // ── Login Screen ───────────────────────────────────────────────────────────

  if (!isLoggedIn) {
    return (
      <div style={{ height: '100vh', background: '#020617', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white' }}>
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card"
          style={{ width: '480px', padding: '3rem', borderRadius: '40px', textAlign: 'center' }}
        >
          <Zap size={60} color="#06b6d4" style={{ marginBottom: '1.5rem' }} />
          <h1 style={{ fontSize: '2rem', fontWeight: 900, marginBottom: '0.5rem' }}>Market-Rover Intelligence</h1>
          <p style={{ color: '#64748b', marginBottom: '3rem', fontSize: '0.9rem' }}>
            Deploying agentic analysts for your portfolio alpha.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {[
              { id: 'Google',   icon: <Globe size={20} />, color: '#ea4335' },
              { id: 'X',        icon: <span style={{ fontWeight: 900, fontSize: '1.2rem' }}>X</span>, color: '#fff' },
              { id: 'LinkedIn', icon: <span style={{ fontWeight: 900 }}>in</span>, color: '#0077b5' },
              { id: 'Facebook', icon: <span style={{ fontWeight: 900 }}>f</span>, color: '#1877f2' }
            ].map(p => (
              <button
                key={p.id}
                id={`login-${p.id.toLowerCase()}`}
                onClick={() => handleLogin(p.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '12px', padding: '1.2rem',
                  background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)',
                  borderRadius: '16px', color: 'white', cursor: 'pointer',
                  transition: 'all 0.3s', fontWeight: 600, fontSize: '0.95rem'
                }}
                onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.07)'; e.currentTarget.style.borderColor = p.color; }}
                onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.03)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.05)'; }}
              >
                <span style={{ color: p.color, width: '24px', display: 'flex', justifyContent: 'center' }}>{p.icon}</span>
                Connect with {p.id}
              </button>
            ))}
          </div>

          <button
            id="login-bypass"
            onClick={() => { setSocialIdentity({ handle: 'dev.analyst@market-rover.com', provider: 'Local' }); setIsLoggedIn(true); }}
            style={{ marginTop: '1.5rem', background: 'transparent', border: 'none', color: '#475569', fontSize: '0.8rem', cursor: 'pointer', textDecoration: 'underline' }}
          >
            Use Local Analyst Account (Bypass OAuth)
          </button>
          <p style={{ marginTop: '1rem', fontSize: '0.7rem', color: '#334155', letterSpacing: '1px' }}>
            SECURE SOCIAL GOVERNANCE SHIELD [ACTIVE]
          </p>
        </motion.div>
      </div>
    );
  }

  // ── Authenticated Layout ───────────────────────────────────────────────────

  const personaIcon = persona.includes('Hunter') ? '(Hunter)' : persona.includes('Defender') ? '(Defender)' : persona.includes('Compounder') ? '(Compounder)' : persona.includes('Preserver') ? '(Preserver)' : '';

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#020617', color: 'white', fontFamily: 'Inter, system-ui, sans-serif' }}>
      {showConfetti && <Confetti recycle={false} numberOfPieces={300} />}

      {/* ── Sidebar ────────────────────────────────────────────────────────── */}
      <aside className="glass-card" style={{ width: '280px', margin: '1rem', borderRadius: '32px', display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
        <div style={{ padding: '2rem 1.5rem', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <h2 className="glow-text" style={{ fontSize: '1.5rem', display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 800 }}>
            <Zap size={28} fill="var(--accent-cyan)" /> Market-Rover
          </h2>
          <p style={{ fontSize: '0.6rem', color: '#475569', marginTop: '6px', letterSpacing: '2px', fontWeight: 700 }}>ELITE ACCESS CONSOLE v5</p>
        </div>

        <nav style={{ flex: 1, padding: '1.2rem 0.8rem', overflowY: 'auto' }}>
          <p style={{ margin: '0 0.5rem 0.8rem', fontSize: '0.65rem', color: '#334155', fontWeight: 800, letterSpacing: '1.5px' }}>
            {persona === 'Not Set' ? 'CALIBRATION REQUIRED' : 'CORE INTELLIGENCE'}
          </p>

          <SidebarItem icon={<User size={18} />} label="Investor Profile" active={activeTab === 'profile'} onClick={() => setActiveTab('profile')} />

          {persona && persona !== 'Not Set' && (<>
            <SidebarItem icon={<Activity size={18} />}   label="Market Analysis Hub"   active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
            <SidebarItem icon={<BarChart2 size={18} />}  label="Market Heatmap"     active={activeTab === 'heatmap'}   onClick={() => setActiveTab('heatmap')} />
            <SidebarItem icon={<Eye size={18} />}        label="Shadow Discovery"   active={activeTab === 'shadow'}    onClick={() => setActiveTab('shadow')} />
            <SidebarItem icon={<History size={18} />}    label="Forecast Tracker"   active={activeTab === 'forecasts'} onClick={() => setActiveTab('forecasts')} />
            <SidebarItem icon={<Calendar size={18} />}   label="Trading Calendar"   active={activeTab === 'calendar'}  onClick={() => setActiveTab('calendar')} />

            <p style={{ margin: '1.5rem 0.5rem 0.8rem', fontSize: '0.65rem', color: '#334155', fontWeight: 800, letterSpacing: '1.5px' }}>SATELLITE MISSIONS</p>
            <SidebarItem icon={<Layers size={18} />}  label="HIL Mission Control" external onClick={() => window.open('https://hil-rover-9514347926.us-central1.run.app', '_blank')} />
            <SidebarItem icon={<Shield size={18} />}  label="Pledge & SRE Hub"    external onClick={() => window.open('https://pledge-rover-9514347926.us-central1.run.app', '_blank')} />
            <SidebarItem icon={<Gamepad2 size={18} />} label="InvestBrand Hub"    external onClick={() => window.open('https://investbrand-ui-9514347926.us-central1.run.app', '_blank')} />
          </>)}
        </nav>

        {persona !== 'Not Set' && (
          <div style={{ padding: '0.8rem 1rem', margin: '0 0.8rem 0.5rem', background: 'rgba(6,182,212,0.06)', borderRadius: '16px', border: '1px solid rgba(6,182,212,0.15)' }}>
            <p style={{ fontSize: '0.6rem', color: '#94a3b8', letterSpacing: '1px', fontWeight: 800 }}>ACTIVE PERSONA</p>
            <p style={{ fontSize: '0.85rem', fontWeight: 900, color: '#22d3ee' }}>{persona.toUpperCase()} {personaIcon}</p>
          </div>
        )}

        <div style={{ padding: '0.8rem 1rem', margin: '0 0.8rem 1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.05)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.8rem' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'linear-gradient(135deg, #06b6d4,#3b82f6)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <User size={18} />
            </div>
            <div style={{ overflow: 'hidden' }}>
              <p style={{ fontSize: '0.78rem', fontWeight: 700, textOverflow: 'ellipsis', whiteSpace: 'nowrap', overflow: 'hidden' }}>{socialIdentity.handle}</p>
              <div style={{ display: 'flex', gap: '4px', marginTop: '3px' }}>
                <Badge text={persona.toUpperCase()} />
                <Badge text={socialIdentity.provider} color="#10b981" />
              </div>
            </div>
          </div>
          <button id="btn-signout" onClick={handleLogout} style={{ width: '100%', padding: '0.5rem', background: 'rgba(244,63,94,0.1)', color: '#f43f5e', border: 'none', borderRadius: '10px', fontSize: '0.72rem', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
            <LogOut size={13} /> SIGN OUT
          </button>
        </div>
      </aside>

      {/* ── Main Content ──────────────────────────────────────────────────── */}
      <main style={{ flex: 1, padding: '1.5rem 1.5rem 1.5rem 0.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', overflowY: 'auto' }}>

        <AnimatePresence mode="wait">

          {/* ── Intelligence Hub ─────────────────────────────────────────── */}
          {activeTab === 'dashboard' && (
            <motion.div key="dashboard" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <SectionHeader icon={<Activity size={24} color="var(--accent-cyan)" />} title="Market Analysis Hub" sub={`Secure analysis for ${socialIdentity.handle}`} />

              <GlassCard style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', alignItems: 'center' }}>
                <div style={{ flex: 1, position: 'relative' }}>
                  <Search style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: '#475569' }} size={18} />
                  <input
                    id="input-tickers"
                    type="text"
                    value={tickers}
                    onChange={e => setTickers(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && !isAnalyzing && runAnalysis()}
                    placeholder="Enter NSE tickers (e.g. TCS.NS, RELIANCE.NS, INFY.NS)..."
                    style={{ width: '100%', background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.07)', padding: '1rem 1rem 1rem 3rem', borderRadius: '16px', color: 'white', fontSize: '0.95rem', fontFamily: 'JetBrains Mono, monospace', outline: 'none' }}
                  />
                </div>
                <button
                  id="btn-run-analysis"
                  className="btn-primary"
                  onClick={runAnalysis}
                  disabled={isAnalyzing}
                  style={{ height: '60px', padding: '0 2.5rem', background: 'linear-gradient(45deg,#06b6d4,#3b82f6)', border: 'none', borderRadius: '16px', color: 'white', fontWeight: 800, cursor: isAnalyzing ? 'not-allowed' : 'pointer', opacity: isAnalyzing ? 0.7 : 1, boxShadow: '0 8px 15px -3px rgba(6,182,212,0.4)', whiteSpace: 'nowrap' }}
                >
                  {isAnalyzing ? 'ORCHESTRATING...' : 'RUN INTELLIGENCE'}
                </button>
              </GlassCard>

              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1.2fr', gap: '1.5rem' }}>
                <GlassCard style={{ display: 'flex', flexDirection: 'column', minHeight: '540px' }}>
                  <h3 style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1.5rem', fontWeight: 700 }}>
                    <Activity size={18} color="var(--accent-cyan)" /> Intelligence Terminal
                  </h3>
                  <div style={{ flex: 1, background: '#000', borderRadius: '14px', padding: '1.8rem', fontFamily: 'JetBrains Mono, monospace', fontSize: '0.85rem', color: '#10b981', overflowY: 'auto', border: '1px solid rgba(255,255,255,0.06)', lineHeight: 1.7 }}>
                    {isAnalyzing ? (
                      <div style={{ color: '#06b6d4' }}>
                        &gt; Authenticating session...<br />
                        &gt; Spawning Forensic Detective...<br />
                        &gt; Scanning Nifty sector flow...<br />
                        &gt; Verifying Subha Muhurtham windows...<br />
                        <motion.span animate={{ opacity: [0, 1] }} transition={{ repeat: Infinity, duration: 0.8 }}>_</motion.span>
                      </div>
                    ) : report || '> READY FOR MARKET INGESTION.\n> SYSTEM STATUS: NOMINAL.'}
                  </div>
                </GlassCard>

                <GlassCard style={{ minHeight: '540px', display: 'flex', flexDirection: 'column' }}>
                  <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 700 }}>
                    <CheckCircle size={18} color="#10b981" /> Live Signal Stream
                  </h3>
                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '10px', overflowY: 'auto' }}>
                    {findings.length > 0 ? findings.slice(0, 10).map((f, i) => {
                      const isShadow = f.type === 'SHADOW';
                      return (
                        <motion.div key={i} initial={{ x: 20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: i * 0.05 }}
                          style={{ padding: '0.9rem', background: isShadow ? 'rgba(244,63,94,0.08)' : 'rgba(255,255,255,0.03)', borderRadius: '14px', fontSize: '0.82rem', borderLeft: `4px solid ${isShadow ? '#f43f5e' : '#06b6d4'}` }}>
                          {isShadow
                            ? <div style={{ color: '#fb7185' }}><strong>[SHADOW]</strong> {f.message}</div>
                            : <div><strong style={{ color: 'var(--accent-cyan)' }}>{f.ticker}</strong>: {f.sentiment || f.yield || f.status || 'Technical Concordance'}</div>}
                        </motion.div>
                      );
                    }) : (
                      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#334155' }}>
                        <Database size={36} style={{ marginBottom: '1rem', opacity: 0.5 }} />
                        <p style={{ fontSize: '0.85rem' }}>No active signals. Run intelligence above.</p>
                      </div>
                    )}
                  </div>
                </GlassCard>
              </div>
            </motion.div>
          )}

          {/* ── Market Heatmap ────────────────────────────────────────────── */}
          {activeTab === 'heatmap' && (
            <motion.div key="heatmap" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <SectionHeader icon={<BarChart2 size={24} color="#f59e0b" />} title="Market Heatmap" sub="Monthly returns matrix — spot seasonal patterns and momentum cycles" />

              <GlassCard style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', alignItems: 'center' }}>
                <div style={{ flex: 1, position: 'relative' }}>
                  <Search style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: '#475569' }} size={18} />
                  <input
                    id="input-heatmap-ticker"
                    type="text"
                    value={heatTicker}
                    onChange={e => setHeatTicker(e.target.value.toUpperCase())}
                    onKeyDown={e => e.key === 'Enter' && fetchHeatmap()}
                    placeholder="NSE ticker (e.g. TCS.NS, RELIANCE.NS)..."
                    style={{ width: '100%', background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.07)', padding: '1rem 1rem 1rem 3rem', borderRadius: '16px', color: 'white', fontSize: '0.95rem', fontFamily: 'JetBrains Mono, monospace', outline: 'none' }}
                  />
                </div>
                <button
                  id="btn-load-heatmap"
                  className="btn-primary"
                  onClick={fetchHeatmap}
                  disabled={heatLoading}
                  style={{ height: '60px', padding: '0 2.5rem', background: 'linear-gradient(45deg,#f59e0b,#ef4444)', border: 'none', borderRadius: '16px', color: 'white', fontWeight: 800, cursor: heatLoading ? 'not-allowed' : 'pointer', opacity: heatLoading ? 0.7 : 1 }}
                >
                  {heatLoading ? 'LOADING...' : 'LOAD HEATMAP'}
                </button>
              </GlassCard>

              {heatError && (
                <GlassCard style={{ background: 'rgba(244,63,94,0.06)', borderColor: 'rgba(244,63,94,0.2)', marginBottom: '1rem' }}>
                  <p style={{ color: '#f43f5e', fontSize: '0.9rem' }}>[ERROR] {heatError}</p>
                </GlassCard>
              )}

              {heatData && (
                <GlassCard>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
                    <div>
                      <h3 style={{ fontWeight: 800, fontSize: '1.4rem', color: '#22d3ee' }}>{heatData.ticker}</h3>
                      <p style={{ color: '#64748b', fontSize: '0.8rem' }}>3-year monthly returns — green = gain, red = loss</p>
                    </div>
                    <div style={{ display: 'flex', gap: '1rem' }}>
                      <div style={{ padding: '0.8rem 1.2rem', background: 'rgba(16,185,129,0.1)', borderRadius: '14px', border: '1px solid rgba(16,185,129,0.2)', textAlign: 'center' }}>
                        <p style={{ fontSize: '0.6rem', color: '#64748b', marginBottom: '4px' }}>BEST MONTH</p>
                        <p style={{ color: '#10b981', fontWeight: 800, fontSize: '0.85rem' }}>{heatData.best?.month}</p>
                        <p style={{ color: '#10b981', fontWeight: 900 }}>+{heatData.best?.return?.toFixed(1)}%</p>
                      </div>
                      <div style={{ padding: '0.8rem 1.2rem', background: 'rgba(244,63,94,0.1)', borderRadius: '14px', border: '1px solid rgba(244,63,94,0.2)', textAlign: 'center' }}>
                        <p style={{ fontSize: '0.6rem', color: '#64748b', marginBottom: '4px' }}>WORST MONTH</p>
                        <p style={{ color: '#f43f5e', fontWeight: 800, fontSize: '0.85rem' }}>{heatData.worst?.month}</p>
                        <p style={{ color: '#f43f5e', fontWeight: 900 }}>{heatData.worst?.return?.toFixed(1)}%</p>
                      </div>
                    </div>
                  </div>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ borderCollapse: 'separate', borderSpacing: '3px', width: '100%' }}>
                      <thead>
                        <tr>
                          <th style={{ padding: '6px 10px', fontSize: '0.7rem', color: '#475569', textAlign: 'left', fontWeight: 800 }}>YEAR</th>
                          {heatData.months.map(m => (
                            <th key={m} style={{ padding: '6px 8px', fontSize: '0.68rem', color: '#475569', textAlign: 'center', fontWeight: 700 }}>{m}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {heatData.years.map(yr => (
                          <tr key={yr}>
                            <td style={{ padding: '6px 10px', fontSize: '0.8rem', fontWeight: 700, color: '#94a3b8', whiteSpace: 'nowrap' }}>{yr}</td>
                            {heatData.months.map(m => (
                              <HeatCell key={m} val={heatData.data[String(yr)]?.[m] ?? null} />
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </GlassCard>
              )}

              {!heatData && !heatLoading && !heatError && (
                <GlassCard style={{ textAlign: 'center', padding: '4rem', color: '#334155' }}>
                  <Flame size={48} style={{ margin: '0 auto 1rem', opacity: 0.4 }} />
                  <p>Enter an NSE ticker and click Load Heatmap to visualize 3 years of monthly returns.</p>
                </GlassCard>
              )}
            </motion.div>
          )}

          {/* ── Shadow Discovery ──────────────────────────────────────────── */}
          {activeTab === 'shadow' && (
            <motion.div key="shadow" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <SectionHeader icon={<Eye size={24} color="#a78bfa" />} title="Shadow Discovery" sub="Decoding institutional footprints via forensic divergence analysis" />

              {shadowLoading && (
                <GlassCard style={{ textAlign: 'center', padding: '3rem', color: '#64748b' }}>
                  <motion.div animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 1.5 }}>
                    Scanning agent memory for institutional signals...
                  </motion.div>
                </GlassCard>
              )}

              {!shadowLoading && shadowSignals.length === 0 && (
                <GlassCard style={{ textAlign: 'center', padding: '4rem', color: '#334155' }}>
                  <Eye size={48} style={{ margin: '0 auto 1rem', opacity: 0.3 }} />
                  <p style={{ fontSize: '0.95rem' }}>No shadow signals yet. Run an intelligence analysis to generate institutional fingerprints.</p>
                  <button id="btn-goto-analysis" onClick={() => setActiveTab('dashboard')} className="btn-primary" style={{ marginTop: '1.5rem', padding: '0.8rem 2rem' }}>
                    Go to Intelligence Hub
                  </button>
                </GlassCard>
              )}

              {!shadowLoading && shadowSignals.length > 0 && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem' }}>
                  {shadowSignals.map((s, i) => {
                    const isAccum = s.stance === 'ACCUMULATION';
                    const isWarn  = s.stance === 'WARNING';
                    const color   = isWarn ? '#f59e0b' : isAccum ? '#10b981' : '#f43f5e';
                    return (
                      <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}>
                        <GlassCard style={{ background: `${color}08`, border: `1px solid ${color}22` }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                            <span style={{ fontWeight: 900, fontSize: '1.3rem', color }}>{s.ticker}</span>
                            <Badge text={s.stance} color={color} />
                          </div>
                          <p style={{ fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.6 }}>{s.logic_summary}</p>
                          <p style={{ fontSize: '0.7rem', color: '#475569', marginTop: '1rem' }}>
                            {s.analysis_date ? new Date(s.analysis_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : ''}
                          </p>
                        </GlassCard>
                      </motion.div>
                    );
                  })}
                </div>
              )}
            </motion.div>
          )}

          {/* ── Forecast Tracker ──────────────────────────────────────────── */}
          {activeTab === 'forecasts' && (
            <motion.div key="forecasts" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <SectionHeader icon={<Target size={24} color="var(--accent-cyan)" />} title="Forecast Accountability" sub="Your complete historical analysis record — every stance on record" />
              <GlassCard>
                {forecasts.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '3rem', color: '#334155' }}>
                    <History size={40} style={{ margin: '0 auto 1rem', opacity: 0.4 }} />
                    <p>No forecasts yet. Run an analysis to start building your track record.</p>
                  </div>
                ) : (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ color: '#475569', fontSize: '0.72rem', fontWeight: 800, borderBottom: '1px solid rgba(255,255,255,0.08)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                          {['Analysis Date', 'Ticker', 'Stance', 'Intelligence Summary'].map(h => (
                            <th key={h} style={{ padding: '1rem' }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {forecasts.map((f, i) => (
                          <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', fontSize: '0.88rem', transition: 'background 0.2s' }}
                            onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                            <td style={{ padding: '1rem', color: '#64748b', fontFamily: 'monospace' }}>{f.analysis_date?.split('T')[0]}</td>
                            <td style={{ padding: '1rem', fontWeight: 900, color: 'var(--accent-cyan)' }}>{f.ticker}</td>
                            <td style={{ padding: '1rem' }}>
                              <Badge text={f.stance} color={f.stance === 'ACCUMULATION' ? '#10b981' : f.stance === 'WARNING' ? '#f59e0b' : '#f43f5e'} />
                            </td>
                            <td style={{ padding: '1rem', color: '#94a3b8', maxWidth: '420px', lineHeight: 1.5 }}>{f.logic_summary}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </GlassCard>
            </motion.div>
          )}

          {/* ── Trading Calendar ──────────────────────────────────────────── */}
          {activeTab === 'calendar' && (
            <motion.div key="calendar" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <SectionHeader icon={<Calendar size={24} color="#fbbf24" />} title="Trading Calendar" sub="Subha Muhurtham windows & seasonal performance cycles for strategic timing" />

              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '1.5rem' }}>
                <GlassCard>
                  <h3 style={{ fontWeight: 800, marginBottom: '1.2rem', display: 'flex', alignItems: 'center', gap: '10px', color: '#fbbf24' }}>
                    <CheckCircle size={18} /> Auspicious Windows 2026
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
                    {muhurthamWindows.length === 0 ? (
                      <p style={{ color: '#475569', fontSize: '0.85rem' }}>Loading auspicious windows...</p>
                    ) : muhurthamWindows.map((w, i) => (
                      <motion.div key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.07 }}
                        style={{ padding: '1rem', background: 'rgba(251,191,36,0.05)', borderRadius: '16px', border: '1px solid rgba(251,191,36,0.12)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                          <span style={{ fontWeight: 800, color: '#fbbf24', fontSize: '0.9rem' }}>{w.name}</span>
                          <span style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'monospace' }}>{w.date}</span>
                        </div>
                        <p style={{ fontSize: '0.78rem', color: '#94a3b8', lineHeight: 1.5 }}>{w.note}</p>
                      </motion.div>
                    ))}
                  </div>
                </GlassCard>

                <GlassCard>
                  <h3 style={{ fontWeight: 800, marginBottom: '1.2rem', display: 'flex', alignItems: 'center', gap: '10px', color: '#06b6d4' }}>
                    <TrendingUp size={18} /> Seasonal Performance Patterns
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
                    {seasonalPatterns.length === 0 ? (
                      <p style={{ color: '#475569', fontSize: '0.85rem' }}>Loading patterns...</p>
                    ) : seasonalPatterns.map((p, i) => (
                      <motion.div key={i} initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.07 }}
                        style={{ padding: '1rem', background: 'rgba(6,182,212,0.05)', borderRadius: '16px', border: '1px solid rgba(6,182,212,0.1)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                          <span style={{ fontWeight: 800, color: '#06b6d4', fontSize: '0.9rem' }}>{p.season}</span>
                          <Badge text={p.months} color="#06b6d4" />
                        </div>
                        <p style={{ fontSize: '0.78rem', color: '#94a3b8', lineHeight: 1.5 }}>{p.note}</p>
                      </motion.div>
                    ))}
                  </div>
                </GlassCard>
              </div>
            </motion.div>
          )}

          {/* ── Investor Profile ──────────────────────────────────────────── */}
          {activeTab === 'profile' && (
            <motion.div key="profile" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
              <SectionHeader icon={<Shield size={24} color="var(--accent-cyan)" />} title="Investor Persona" sub="The Sleep Test calibrates your risk tolerance, asset limits, and agent reporting tone" />

              {persona === 'Not Set' ? (
                <div style={{ maxWidth: '600px', margin: '0 auto', width: '100%' }}>
                  <AnimatePresence mode="wait">
                    {quizStep === 0 && (
                      <motion.div key="q0" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                        <GlassCard style={{ textAlign: 'center', padding: '3rem' }}>
                          <Shield size={64} color="#06b6d4" style={{ margin: '0 auto 1.5rem', display: 'block', filter: 'drop-shadow(0 0 10px rgba(6,182,212,0.4))' }} />
                          <h3 style={{ fontSize: '1.8rem', fontWeight: 900, marginBottom: '1rem' }}>The Sleep Test</h3>
                          <p style={{ color: '#94a3b8', marginBottom: '2.5rem', lineHeight: 1.7 }}>
                            Answer three honesty-based questions to determine your mathematical agentic strategy — balancing risk tolerance, time horizon, and loss capacity.
                          </p>
                          <button id="btn-begin-calibration" className="btn-primary" onClick={() => setQuizStep(1)} style={{ padding: '1.2rem 3rem', fontSize: '1rem' }}>
                            BEGIN CALIBRATION
                          </button>
                        </GlassCard>
                      </motion.div>
                    )}

                    {[
                      {
                        step: 1, key: 'q1', label: '1 / 3 — THE PANIC TEST',
                        question: 'The market crashes 20% tomorrow. What is your immediate reaction?',
                        choices: [{ text: 'Sell everything immediately', score: 1 }, { text: 'Wait and watch — do nothing', score: 2 }, { text: 'Buy more at lower prices', score: 3 }]
                      },
                      {
                        step: 2, key: 'q2', label: '2 / 3 — THE DEADLINE TEST',
                        question: 'When do you absolutely need to access this specific capital?',
                        choices: [{ text: 'Less than 3 Years', score: 1 }, { text: '3 to 7 Years', score: 2 }, { text: 'More than 7 Years', score: 3 }]
                      },
                      {
                        step: 3, key: 'q3', label: '3 / 3 — THE CUSHION TEST',
                        question: 'If this portfolio drops 50% temporarily, does your lifestyle change?',
                        choices: [{ text: 'My lifestyle would be significantly affected', score: 1 }, { text: 'I would have to cut back on some luxuries', score: 2 }, { text: 'No impact — my lifestyle is secure', score: 3 }]
                      }
                    ].filter(q => q.step === quizStep).map(q => (
                      <motion.div key={q.key} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
                        <GlassCard style={{ padding: '2.5rem' }}>
                          <p style={{ fontSize: '0.7rem', color: '#06b6d4', fontWeight: 800, letterSpacing: '2px', marginBottom: '0.6rem' }}>{q.label}</p>
                          <h4 style={{ fontSize: '1.05rem', color: '#cbd5e1', marginBottom: '2rem', lineHeight: 1.6 }}>{q.question}</h4>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                            {q.choices.map((c, ci) => (
                              <button
                                id={`quiz-${q.key}-${ci}`}
                                key={ci}
                                onClick={() => {
                                  const next = { ...quizScores, [q.key]: c.score };
                                  setQuizScores(next);
                                  if (q.step < 3) setQuizStep(q.step + 1);
                                  else { submitQuiz(next); }
                                }}
                                style={{ padding: '1.1rem', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: '14px', color: 'white', textAlign: 'left', cursor: 'pointer', transition: 'all 0.2s', fontWeight: 600, fontSize: '0.9rem' }}
                                onMouseEnter={e => e.currentTarget.style.background = 'rgba(6,182,212,0.1)'}
                                onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                              >{c.text}</button>
                            ))}
                          </div>
                        </GlassCard>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
                  {[
                    { id: 'The Hunter',    color: '#10b981', icon: <TrendingUp />, desc: 'Aggressive alpha seeker. Mid-caps, high-volatility breakouts, and institutional momentum. PEG < 0.8 focus.' },
                    { id: 'The Defender',  color: '#3b82f6', icon: <Shield />,     desc: 'Capital preservation first. Low-beta blue-chips, dividend yield, and sector-defensive rotation.' },
                    { id: 'The Compounder',color: '#8b5cf6', icon: <Activity />,   desc: 'Moderate multi-cap growth. Nifty Next 50 rising stars and structural sector leaders. PEG < 1.5.' },
                    { id: 'The Preserver', color: '#f59e0b', icon: <Database />,   desc: 'Ultra-conservative. Liquid funds, government bonds, gold ETFs, and high-dividend PSU stocks.' }
                  ].map(p => (
                    <motion.div
                      key={p.id}
                      id={`persona-${p.id.toLowerCase().replace(/\s+/g, '-')}`}
                      whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                      onClick={() => updatePersona(p.id)}
                      style={{
                        padding: '2rem', borderRadius: '28px', cursor: 'pointer', position: 'relative', overflow: 'hidden',
                        background: persona === p.id ? `${p.color}12` : 'rgba(255,255,255,0.02)',
                        border: persona === p.id ? `2px solid ${p.color}` : '1px solid rgba(255,255,255,0.06)',
                        transition: 'all 0.3s'
                      }}
                    >
                      {persona === p.id && <div style={{ position: 'absolute', top: 0, right: 0, padding: '5px 14px', background: p.color, color: '#000', fontSize: '0.6rem', fontWeight: 900, borderBottomLeftRadius: '14px' }}>ACTIVE</div>}
                      <div style={{ marginBottom: '1.2rem', color: p.color, background: 'rgba(255,255,255,0.04)', width: 'fit-content', padding: '0.8rem', borderRadius: '12px' }}>{p.icon}</div>
                      <h3 style={{ marginBottom: '0.8rem', fontWeight: 800, fontSize: '1.2rem' }}>{p.id}</h3>
                      <p style={{ fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.6 }}>{p.desc}</p>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          )}

        </AnimatePresence>
      </main>
    </div>
  );
};

export default App;

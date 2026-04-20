import React, { useState, useEffect } from 'react';

const API_BASE = '/api'; // Adjusted for production/proxy

function App() {
  const [requests, setRequests] = useState([]);
  const [stats, setStats] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [brainData, setBrainData] = useState(null);
  const [kpiData, setKpiData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [now, setNow] = useState(() => Date.now());
  const [activeTab, setActiveTab] = useState('governance');
  const [provisionLog, setProvisionLog] = useState(null);
  const [provisioning, setProvisioning] = useState(false);

  const fetchData = async () => {
    try {
      const urls = [
        `${API_BASE}/requests`,
        `${API_BASE}/stats`,
        `${API_BASE}/health-stats`,
        `${API_BASE}/brain-manifest`,
        `${API_BASE}/kpi-leaderboard`
      ];
      const results = await Promise.all(urls.map(u => fetch(u).then(r => r.json())));

      setRequests(results[0]);
      setStats(results[1]);
      setHealthData(results[2]);
      setBrainData(results[3]);
      setKpiData(results[4]);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching HIL data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchData();
    const interval = setInterval(fetchData, 10000); // Poll every 10s
    const timeInterval = setInterval(() => setNow(Date.now()), 60000); // Update stable time every minute
    return () => {
      clearInterval(interval);
      clearInterval(timeInterval);
    };
  }, []);

  const handleDecision = async (id, decision) => {
    try {
      await fetch(`${API_BASE}/requests/${id}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, comments: "Processed via Governance Portal" })
      });
      fetchData();
    } catch {
      alert('Failed to process request');
    }
  };

  const pendingRequests = requests.filter(r => r.status === 'PENDING' && r.request_type !== 'QUALITATIVE_FEEDBACK');
  const feedbackItems = requests.filter(r => r.request_type === 'QUALITATIVE_FEEDBACK');

  if (loading && !stats) return <div className="dashboard-container"><h1>Initializing Core...</h1></div>;

  return (
    <div className="dashboard-container">
      <header className="header" style={{ marginBottom: '1rem' }}>
        <div className="title-group">
          <h1>HIL MISSION CONTROL</h1>
          <p className="timestamp">System Time: {new Date(now).toLocaleTimeString()} IST</p>
        </div>
        <div className="agent-badge">Operational Status: Optimal</div>
      </header>

      <nav className="tabs">
        <button className={`tab-btn ${activeTab === 'governance' ? 'active' : ''}`} onClick={() => setActiveTab('governance')}>🛡️ Governance Gate</button>
        <button className={`tab-btn ${activeTab === 'brain' ? 'active' : ''}`} onClick={() => setActiveTab('brain')}>🧠 Agent Brain</button>
        <button className={`tab-btn ${activeTab === 'kpis' ? 'active' : ''}`} onClick={() => setActiveTab('kpis')}>📈 Agent KPIs</button>
        <button className={`tab-btn ${activeTab === 'feedback' ? 'active' : ''}`} onClick={() => setActiveTab('feedback')}>🌟 Success & Feedback</button>
        <button className={`tab-btn ${activeTab === 'health' ? 'active' : ''}`} onClick={() => setActiveTab('health')}>⚙️ System Health</button>
        <button className={`tab-btn ${activeTab === 'infra' ? 'active' : ''}`} onClick={() => setActiveTab('infra')}>🏗️ Infrastructure</button>
      </nav>

      {activeTab === 'governance' && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Total Requests</div>
              <div className="stat-value">{stats?.total || 0}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Approval Rate</div>
              <div className="stat-value" style={{color: 'var(--accent-green)'}}>
                {stats?.approval_rate?.toFixed(1) || 0}%
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Pending Approval</div>
              <div className="stat-value" style={{color: 'var(--accent-amber)'}}>
                {stats?.pending || 0}
              </div>
            </div>
            <div className="stat-card" style={stats?.sla_breaches > 0 ? {borderColor: 'var(--accent-red)'} : {}}>
              <div className="stat-label">SLA Breaches (&gt;24h)</div>
              <div className="stat-value" style={{color: stats?.sla_breaches > 0 ? 'var(--accent-red)' : 'var(--text-secondary)'}}>
                {stats?.sla_breaches || 0}
              </div>
            </div>
          </div>

          <main>
            <h2 style={{marginBottom: '1.5rem', fontSize: '1.5rem'}}>📥 Decision Queue</h2>
            {pendingRequests.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">🛡️</div>
                <h3>No Pending Actions</h3>
                <p>Agents are operating within established safety parameters.</p>
              </div>
            ) : (
              <div className="request-grid">
                {pendingRequests.map(req => {
                  const age = now - new Date(req.created_at).getTime();
                  const isUrgent = age > (18 * 60 * 60 * 1000);

                  return (
                    <div key={req.id} className={`request-card ${isUrgent ? 'urgent' : ''}`}>
                      <div className="card-header">
                        <span className="agent-badge">{req.agent_name}</span>
                        <span className="timestamp">{new Date(req.created_at).toLocaleDateString()}</span>
                      </div>
                      <h3 className="task-name">{req.task_name}</h3>
                      <div className="instructions">
                        <strong>HIL Guideline:</strong><br />
                        {req.instructions}
                      </div>
                      <div className="data-payload">
                        <pre>{JSON.stringify(req.data, null, 2)}</pre>
                      </div>
                      <div className="action-buttons">
                        <button className="btn-approve" onClick={() => handleDecision(req.id, 'APPROVED')}>Approve</button>
                        <button className="btn-reject" onClick={() => handleDecision(req.id, 'REJECTED')}>Reject</button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </main>
        </>
      )}

      {activeTab === 'brain' && (
        <main>
          <h2 style={{marginBottom: '1.5rem'}}>🧠 Neural Manifest</h2>
          <div className="request-grid">
            {brainData?.agents.map(agent => (
              <div key={agent.name} className="request-card">
                 <div className="card-header">
                    <span className="agent-badge">{agent.status}</span>
                  </div>
                  <h3 className="task-name">{agent.name}</h3>
                  <p style={{color: 'var(--text-secondary)', marginBottom: '1rem'}}>{agent.role}</p>
                  <div className="instructions" style={{borderLeftColor: 'var(--accent-blue)'}}>
                    <strong>Autonomy Level:</strong> High (max_iter={agent.max_iter})<br />
                    <strong>Memory State:</strong> Optimized
                  </div>
              </div>
            ))}
          </div>
        </main>
      )}

      {activeTab === 'kpis' && (
        <main>
          <h2 style={{marginBottom: '1.5rem'}}>📈 Agent Performance Leaderboard</h2>
          <div className="request-grid">
            {kpiData.map(kpi => (
              <div key={kpi.agent} className="request-card">
                 <div className="card-header">
                    <span className="agent-badge" style={{background: kpi.score >= kpi.target ? 'var(--accent-green)' : 'var(--accent-amber)'}}>
                      {kpi.status}
                    </span>
                  </div>
                  <h3 className="task-name">{kpi.agent}</h3>
                  <div className="instructions">
                    <strong>Primary KPI:</strong> {kpi.kpi}
                  </div>
                  <div style={{marginTop: '1rem'}}>
                    <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.8rem'}}>
                      <span>Score: {kpi.score}%</span>
                      <span style={{opacity: 0.5}}>Target: {kpi.target}%</span>
                    </div>
                    <div className="progress-bar-bg">
                      <div className="progress-bar-fill" style={{width: `${kpi.score}%`, backgroundColor: kpi.score >= kpi.target ? 'var(--accent-green)' : 'var(--accent-amber)'}}></div>
                    </div>
                  </div>
              </div>
            ))}
          </div>
        </main>
      )}

      {activeTab === 'feedback' && (
        <main>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem'}}>
            <h2>🌟 Qualitative Insights & User Feedback</h2>
            <div style={{fontSize: '0.9rem', color: 'var(--accent-green)'}}>● Collecting Live Feedback</div>
          </div>

          <div className="request-grid">
            {feedbackItems.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">🌟</div>
                <h3>No Strategic Feedback Yet</h3>
                <p>Agents are waiting for user interaction data to synthesize improvements.</p>
              </div>
            ) : (
              feedbackItems.map(item => (
                <div key={item.id} className="request-card" style={{borderLeft: `4px solid ${item.severity === 'high' ? 'var(--accent-red)' : (item.sentiment === 'Positive' ? 'var(--accent-green)' : 'var(--accent-blue)')}`}}>
                  <div className="card-header">
                    <span className="agent-badge" style={{background: item.sentiment === 'Positive' ? 'var(--accent-green)' : 'var(--accent-blue)'}}>
                      {item.topic || 'Insight'}
                    </span>
                    <span className="timestamp">{new Date(item.created_at).toLocaleDateString()}</span>
                  </div>
                  <h3 className="task-name">{item.agent_name}: {item.task_name}</h3>
                  <p style={{fontSize: '0.9rem', opacity: 0.8, marginBottom: '1rem'}}>
                    {item.user_feedback || 'Agent-synthesized success story based on recent performance metrics.'}
                  </p>
                  <div className="instructions" style={{borderColor: item.sentiment === 'Positive' ? 'var(--accent-green)' : 'var(--accent-blue)', background: 'rgba(255, 255, 255, 0.05)'}}>
                    <strong>HIL Task:</strong> {item.instructions}
                  </div>
                </div>
              ))
            )}
          </div>

          <div style={{marginTop: '3rem', padding: '2rem', background: 'rgba(255,255,255,0.02)', borderRadius: '16px', textAlign: 'center'}}>
             <p style={{opacity: 0.6, fontSize: '0.9rem'}}>This mission-critical tab captures qualitative data and user sentiment to drive agentic evolution.</p>
          </div>
        </main>
      )}

      {activeTab === 'health' && (
        <main>
          <h2 style={{marginBottom: '1.5rem'}}>⚙️ System Telemetry</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">API Latency</div>
              <div className="stat-value">{healthData?.api_latency}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Cache Success</div>
              <div className="stat-value" style={{color: 'var(--accent-green)'}}>{healthData?.cache_hit_rate}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Error Rate</div>
              <div className="stat-value" style={{color: 'var(--accent-blue)'}}>{healthData?.error_rate}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Token Consumption</div>
              <div className="stat-value">{healthData?.token_usage_total}</div>
            </div>
          </div>
          <div style={{marginTop: '2rem'}}>
            <button className="btn-approve" style={{maxWidth: '300px'}} onClick={async () => {
              const res = await fetch(`${API_BASE}/sre/audit`, { method: 'POST' });
              const data = await res.json();
              alert(data.message);
              fetchData();
            }}>
              🔍 Run SRE Sentinel Audit
            </button>
          </div>
        </main>
      )}

      <footer style={{marginTop: '4rem', opacity: 0.3, fontSize: '0.8rem', textAlign: 'center'}}>
        &copy; 2026 Market-Rover Ecosystem | Autonomous Governance Protocol
      </footer>

      {activeTab === 'infra' && (
        <main>
          <h2 style={{marginBottom: '0.5rem'}}>Infrastructure Provisioning</h2>
          <p style={{color: 'var(--text-secondary)', marginBottom: '2rem', fontSize: '0.9rem'}}>
            Creates the <code>market_rover</code>, <code>pledge_rover</code>, and <code>hil_rover</code> databases
            on the shared <strong>investbrand-db</strong> Cloud SQL instance and applies all schemas.
            Safe to run multiple times — fully idempotent.
          </p>

          <button
            id="btn-provision"
            className="btn-approve"
            style={{maxWidth: '320px', fontSize: '1rem', padding: '0.9rem 2rem', marginBottom: '2rem'}}
            disabled={provisioning}
            onClick={async () => {
              setProvisioning(true);
              setProvisionLog(null);
              try {
                const res = await fetch(`${API_BASE}/provision`, { method: 'POST' });
                const data = await res.json();
                setProvisionLog(data);
              } catch (e) {
                setProvisionLog({ status: 'error', log: [], errors: [String(e)] });
              } finally {
                setProvisioning(false);
              }
            }}
          >
            {provisioning ? 'Provisioning...' : 'Provision All Databases'}
          </button>

          {provisionLog && (
            <div style={{
              background: 'rgba(0,0,0,0.3)',
              borderRadius: '12px',
              padding: '1.5rem',
              border: `1px solid ${provisionLog.status === 'done' ? 'var(--accent-green)' : 'var(--accent-amber)'}`
            }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: '0.75rem',
                marginBottom: '1.25rem'
              }}>
                <span style={{
                  background: provisionLog.status === 'done' ? 'var(--accent-green)' : 'var(--accent-amber)',
                  color: '#000', borderRadius: '6px', padding: '0.2rem 0.75rem',
                  fontWeight: 700, fontSize: '0.8rem', textTransform: 'uppercase'
                }}>
                  {provisionLog.status}
                </span>
                <span style={{color: 'var(--text-secondary)', fontSize: '0.85rem'}}>
                  Provision completed
                </span>
              </div>

              <div style={{marginBottom: '1rem'}}>
                <strong style={{fontSize: '0.85rem', opacity: 0.6, textTransform: 'uppercase', letterSpacing: '0.05em'}}>Log</strong>
                <ul style={{marginTop: '0.5rem', listStyle: 'none', padding: 0}}>
                  {provisionLog.log.map((entry, i) => (
                    <li key={i} style={{
                      padding: '0.4rem 0',
                      borderBottom: '1px solid rgba(255,255,255,0.05)',
                      fontSize: '0.9rem',
                      color: 'var(--accent-green)'
                    }}>
                      {entry}
                    </li>
                  ))}
                </ul>
              </div>

              {provisionLog.errors.length > 0 && (
                <div>
                  <strong style={{fontSize: '0.85rem', color: 'var(--accent-red)', textTransform: 'uppercase', letterSpacing: '0.05em'}}>Errors</strong>
                  <ul style={{marginTop: '0.5rem', listStyle: 'none', padding: 0}}>
                    {provisionLog.errors.map((err, i) => (
                      <li key={i} style={{
                        padding: '0.4rem 0',
                        fontSize: '0.85rem',
                        color: 'var(--accent-red)'
                      }}>
                        {err}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </main>
      )}
    </div>
  );
}

export default App;

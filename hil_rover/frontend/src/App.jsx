import React, { useState, useEffect } from 'react';

const API_BASE = '/api'; // Adjusted for production/proxy

function App() {
  const [requests, setRequests] = useState([]);
  const [stats, setStats] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [brainData, setBrainData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('governance');

  const fetchData = async () => {
    try {
      const urls = [
        `${API_BASE}/requests`,
        `${API_BASE}/stats`,
        `${API_BASE}/health-stats`,
        `${API_BASE}/brain-manifest`
      ];
      const results = await Promise.all(urls.map(u => fetch(u).then(r => r.json())));

      setRequests(results[0]);
      setStats(results[1]);
      setHealthData(results[2]);
      setBrainData(results[3]);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching HIL data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, []);

  const handleDecision = async (id, decision) => {
    try {
      await fetch(`${API_BASE}/requests/${id}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision, comments: "Processed via Governance Portal" })
      });
      fetchData();
    } catch (error) {
      alert('Failed to process request');
    }
  };

  const pendingRequests = requests.filter(r => r.status === 'PENDING');

  if (loading && !stats) return <div className="dashboard-container"><h1>Initializing Core...</h1></div>;

  return (
    <div className="dashboard-container">
      <header className="header" style={{ marginBottom: '1rem' }}>
        <div className="title-group">
          <h1>HIL MISSION CONTROL</h1>
          <p className="timestamp">System Time: {new Date().toLocaleTimeString()} IST</p>
        </div>
        <div className="agent-badge">Operational Status: Optimal</div>
      </header>

      <nav className="tabs">
        <button className={`tab-btn ${activeTab === 'governance' ? 'active' : ''}`} onClick={() => setActiveTab('governance')}>🛡️ Governance Gate</button>
        <button className={`tab-btn ${activeTab === 'brain' ? 'active' : ''}`} onClick={() => setActiveTab('brain')}>🧠 Agent Brain</button>
        <button className={`tab-btn ${activeTab === 'health' ? 'active' : ''}`} onClick={() => setActiveTab('health')}>⚙️ System Health</button>
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
                  const age = Date.now() - new Date(req.created_at).getTime();
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
        </main>
      )}

      <footer style={{marginTop: '4rem', opacity: 0.3, fontSize: '0.8rem', textAlign: 'center'}}>
        &copy; 2026 Market-Rover Ecosystem | Autonomous Governance Protocol
      </footer>
    </div>
  );
}

export default App;

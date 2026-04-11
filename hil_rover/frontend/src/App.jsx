import React, { useState, useEffect } from 'react';

const API_BASE = '/api'; // Adjusted for production/proxy

function App() {
  const [requests, setRequests] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [reqRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/requests`),
        fetch(`${API_BASE}/stats`)
      ]);
      const reqData = await reqRes.json();
      const statsData = await statsRes.json();

      setRequests(reqData);
      setStats(statsData);
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
      <header className="header">
        <div className="title-group">
          <h1>HIL GOVERNANCE DASHBOARD</h1>
          <p className="timestamp">System Time: {new Date().toLocaleTimeString()} IST</p>
        </div>
        <div className="agent-badge">Operational Status: Optimal</div>
      </header>

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
          <div className="stat-label">SLA Breaches (>24h)</div>
          <div className="stat-value" style={{color: stats?.sla_breaches > 0 ? 'var(--accent-red)' : 'var(--text-secondary)'}}>
            {stats?.sla_breaches || 0}
          </div>
        </div>
      </div>

      <main>
        <h2 style={{marginBottom: '1.5rem', fontSize: '1.5rem'}}>📥 Pending Queue</h2>
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
              const isUrgent = age > (18 * 60 * 60 * 1000); // 18h+ is urgent

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
                    <button
                      className="btn-approve"
                      onClick={() => handleDecision(req.id, 'APPROVED')}
                    >
                      Approve & Execute
                    </button>
                    <button
                      className="btn-reject"
                      onClick={() => handleDecision(req.id, 'REJECTED')}
                    >
                      Halt Task
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>

      <footer style={{marginTop: '4rem', opacity: 0.3, fontSize: '0.8rem', textAlign: 'center'}}>
        &copy; 2026 Market-Rover Ecosystem | Autonomous Governance Protocol
      </footer>
    </div>
  );
}

export default App;

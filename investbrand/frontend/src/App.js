import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Puzzle from './pages/Puzzle';
import Leaderboard from './pages/Leaderboard';
import Profile from './pages/Profile';
import Vote from './pages/Vote';
import MissionsTab from './components/MissionsTab';
import Duel from './pages/Duel';

function PromoterTracker() {
  const location = useLocation();
  const { user } = useAuth();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const promoterId = params.get('promoter');
    const ref = params.get('ref');

    if (promoterId) {
      // Small delay to ensure session is ready if needed, or just track immediately
      axios.post('/api/puzzles/track-click', {
        promoterId: parseInt(promoterId),
        ref: ref || 'direct'
      }).catch(err => console.error('Failed to track promoter click', err));
    }
  }, [location.search]);

  return null;
}

function PrivateRoute({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/" />;
}

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[InvestBrand ErrorBoundary caught an error]:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ minHeight: '100vh', background: '#030014', color: '#fff', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '20px', fontFamily: 'sans-serif' }}>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: '10px' }}>Something went wrong</h2>
          <p style={{ color: '#94a3b8', marginBottom: '20px', maxWidth: '400px', textAlign: 'center' }}>
            InvestBrand encountered a temporary render glitch. Click below to reload.
          </p>
          <button
            onClick={() => { this.setState({ hasError: false }); window.location.href = '/investbrand'; }}
            style={{ padding: '12px 24px', background: '#6366f1', color: '#fff', border: 'none', borderRadius: '12px', fontWeight: 700, cursor: 'pointer' }}
          >
            Reload InvestBrand
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

const DEFAULT_GOOGLE_CLIENT_ID = '9514347926-lm36bs6ks9o6rl6bs5hac2cj9ptp9q4c.apps.googleusercontent.com';

export default function App() {
  const [googleClientId, setGoogleClientId] = React.useState(process.env.REACT_APP_GOOGLE_CLIENT_ID || DEFAULT_GOOGLE_CLIENT_ID);

  React.useEffect(() => {
    axios.get('/api/auth/config')
      .then(res => {
        if (res.data?.googleClientId) {
          setGoogleClientId(res.data.googleClientId);
        }
      })
      .catch(err => console.warn('Could not load auth config:', err.message));
  }, []);

  const activeClientId = googleClientId || DEFAULT_GOOGLE_CLIENT_ID;

  const appContent = (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter basename={process.env.PUBLIC_URL || '/investbrand'}>
          <PromoterTracker />
          <Navbar googleClientId={activeClientId} />
          <Routes>
            <Route path="/" element={<Home googleClientId={activeClientId} />} />
            <Route path="/play" element={<PrivateRoute><Puzzle /></PrivateRoute>} />
            <Route path="/duel" element={<Duel />} />
            <Route path="/duel/:roomCode" element={<Duel />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="/vote" element={<PrivateRoute><Vote /></PrivateRoute>} />
            <Route path="/missions" element={<PrivateRoute><MissionsTab /></PrivateRoute>} />
            <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );

  return (
    <GoogleOAuthProvider clientId={activeClientId}>
      {appContent}
    </GoogleOAuthProvider>
  );
}

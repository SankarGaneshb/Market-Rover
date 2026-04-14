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

export default function App() {
  const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || '9514347926-lm36bs6ks9o6rl6bs5hac2cj9ptp9q4c.apps.googleusercontent.com';

  if (!process.env.REACT_APP_GOOGLE_CLIENT_ID) {
    console.warn("WARNING: REACT_APP_GOOGLE_CLIENT_ID is undefined. Using fallback ID.");
  }

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthProvider>
        <BrowserRouter>
          <PromoterTracker />
          <Navbar />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/play" element={<PrivateRoute><Puzzle /></PrivateRoute>} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="/vote" element={<PrivateRoute><Vote /></PrivateRoute>} />
            <Route path="/missions" element={<PrivateRoute><MissionsTab /></PrivateRoute>} />
            <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}

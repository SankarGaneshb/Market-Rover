import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../context/AuthContext';
import { Trophy, Play, User, LogOut, TrendingUp, Calendar } from 'lucide-react';

export default function Navbar() {
  const { user, login, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <nav className="bg-slate-900 border-b border-slate-700 px-6 py-3 flex items-center justify-between">
      <Link to="/" className="flex items-center gap-2 text-indigo-400 font-bold text-xl"><TrendingUp size={24} />InvestCraft</Link>
      <div className="flex items-center gap-5">
        <Link to="/play" className="text-slate-300 hover:text-white"><Play size={15} />Play</Link>
        <Link to="/leaderboard" className="text-slate-300 hover:text-white"><Trophy size={15} />Leaderboard</Link>
        <Link to="/vote" className="text-slate-300 hover:text-white flex items-center gap-1"><Calendar size={15} />Vote</Link>
        {user ? (
          <><Link to="/profile" className="text-slate-300 hover:text-white"><User size={15} />{user.name}</Link><button onClick={logout} className="text-slate-400 hover:text-red-400"><LogOut size={16} /></button></>
        ) : (
          <div className="pt-1">
            <GoogleLogin
              onSuccess={async (r) => {
                try {
                  await login(r.credential);
                  navigate('/play');
                } catch (err) {
                  alert(`Login Failed: ${err.message}`);
                }
              }}
              onError={() => alert('Google Script Loading Failed')}
              shape="pill"
              text="signin"
              size="medium"
            />
          </div>
        )}
      </div>
    </nav>
  );
}

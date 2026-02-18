import React from 'react';
import { Link } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';
import { useAuth } from '../context/AuthContext';
import { Trophy, Play, User, LogOut, TrendingUp } from 'lucide-react';

export default function Navbar() {
  const { user, login, logout } = useAuth();
  const g = useGoogleLogin({ onSuccess: (r) => login(r.access_token) });
  return (
    <nav className="bg-slate-900 border-b border-slate-700 px-6 py-3 flex items-center justify-between">
      <Link to="/" className="flex items-center gap-2 text-indigo-400 font-bold text-xl"><TrendingUp size={24}/>InvestCraft</Link>
      <div className="flex items-center gap-5">
        <Link to="/play" className="text-slate-300 hover:text-white"><Play size={15}/>Play</Link>
        <Link to="/leaderboard" className="text-slate-300 hover:text-white"><Trophy size={15}/>Leaderboard</Link>
        {user ? (
          <><Link to="/profile" className="text-slate-300 hover:text-white"><User size={15}/>{user.name}</Link><button onClick={logout} className="text-slate-400 hover:text-red-400"><LogOut size={16}/></button></>
        ) : <button onClick={g} className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg">Sign in</button>}
      </div>
    </nav>
  );
}

#!/bin/bash
set -e
BASE="investcraft/frontend/src"
mkdir -p $BASE/components

cat > $BASE/components/Navbar.jsx << 'HEREDOC'
import React from 'react';
import { Link } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';
import { useAuth } from '../context/AuthContext';
import { Trophy, Play, User, LogOut, TrendingUp } from 'lucide-react';

export default function Navbar() {
  const { user, login, logout } = useAuth();
  const googleLogin = useGoogleLogin({ onSuccess: (r) => login(r.access_token) });
  return (
    <nav className="bg-slate-900 border-b border-slate-700 px-6 py-3 flex items-center justify-between sticky top-0 z-50">
      <Link to="/" className="flex items-center gap-2 text-indigo-400 font-bold text-xl">
        <TrendingUp size={24}/> InvestCraft
      </Link>
      <div className="flex items-center gap-5">
        <Link to="/play" className="flex items-center gap-1 text-slate-300 hover:text-white text-sm"><Play size={15}/>Play</Link>
        <Link to="/leaderboard" className="flex items-center gap-1 text-slate-300 hover:text-white text-sm"><Trophy size={15}/>Leaderboard</Link>
        {user ? (
          <>
            <Link to="/profile" className="flex items-center gap-1 text-slate-300 hover:text-white text-sm"><User size={15}/>{user.name}</Link>
            <button onClick={logout} className="text-slate-400 hover:text-red-400"><LogOut size={16}/></button>
          </>
        ) : (
          <button onClick={() => googleLogin()} className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-1.5 rounded-lg text-sm font-medium">Sign in with Google</button>
        )}
      </div>
    </nav>
  );
}
HEREDOC
echo "✅ Navbar.jsx created"

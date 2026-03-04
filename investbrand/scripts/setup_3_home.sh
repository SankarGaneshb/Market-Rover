#!/bin/bash
set -e
BASE="investcraft/frontend/src"
mkdir -p $BASE/pages

cat > $BASE/pages/Home.jsx << 'HEREDOC'
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Play, Trophy, Zap, TrendingUp } from 'lucide-react';

export default function Home() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const features = [
    { icon: <Play size={22}/>, label: 'Daily Puzzle', desc: 'New logo challenge every day' },
    { icon: <Zap size={22}/>, label: 'Build Streaks', desc: 'Play daily to earn rewards' },
    { icon: <Trophy size={22}/>, label: 'Leaderboard', desc: 'Compete with investors worldwide' },
  ];
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex flex-col items-center justify-center px-4">
      <div className="text-center max-w-2xl w-full">
        <div className="flex items-center justify-center gap-3 mb-4">
          <TrendingUp size={44} className="text-indigo-400"/>
          <h1 className="text-5xl font-black text-white">InvestCraft</h1>
        </div>
        <p className="text-xl text-indigo-300 mb-2">Craft your wealth, one move at a time.</p>
        <p className="text-slate-400 mb-8 text-sm">Solve Nifty 50 brand puzzles. Learn. Compete. Grow.</p>
        <div className="grid grid-cols-3 gap-4 mb-8">
          {features.map((f, i) => (
            <div key={i} className="bg-slate-800 rounded-xl p-4 border border-slate-700">
              <div className="text-indigo-400 mb-2 flex justify-center">{f.icon}</div>
              <div className="text-white font-semibold text-sm">{f.label}</div>
              <div className="text-slate-400 text-xs mt-1">{f.desc}</div>
            </div>
          ))}
        </div>
        <button onClick={() => navigate('/play')}
          className="bg-indigo-600 hover:bg-indigo-500 text-white text-lg font-bold px-10 py-4 rounded-2xl shadow-lg transition">
          {user ? "Today's Puzzle →" : "Play Now →"}
        </button>
        {user && <p className="text-slate-400 text-sm mt-4">🔥 Streak: <span className="text-orange-400 font-bold">{user.streak}</span> · Score: <span className="text-indigo-400 font-bold">{user.score}</span></p>}
      </div>
    </div>
  );
}
HEREDOC
echo "✅ Home.jsx created"

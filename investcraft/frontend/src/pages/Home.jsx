import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Play, Trophy, Zap, TrendingUp } from 'lucide-react';

export default function Home() {
  const { user } = useAuth();
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex items-center justify-center px-4">
      <div className="text-center max-w-2xl">
        <div className="flex items-center justify-center gap-3 mb-4">
          <TrendingUp size={44} className="text-indigo-400"/>
          <h1 className="text-5xl font-black text-white">InvestCraft</h1>
        </div>
        <p className="text-xl text-indigo-300 mb-2">Craft your wealth, one move at a time.</p>
        <p className="text-slate-400 mb-8">Solve Nifty 50 brand puzzles. Learn. Compete.</p>
        <button onClick={() => navigate('/play')} className="bg-indigo-600 hover:bg-indigo-500 text-white text-lg font-bold px-10 py-4 rounded-2xl">
          {user ? "Today's Puzzle →" : "Play Now →"}
        </button>
      </div>
    </div>
  );
}

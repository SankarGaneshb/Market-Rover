import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Trophy, Share2, ChevronLeft, ChevronRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { VIRTUOSO_LEVELS, getVirtuosoLevel } from '../data/virtuoso';
import GlitterBadge from '../components/GlitterBadge';

export default function Leaderboard() {
  const { user } = useAuth();
  const [data, setData] = useState([]);
  const [type, setType] = useState('all-time');
  const [selectedLevel, setSelectedLevel] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLeaderboard();
  }, [type, selectedLevel]);

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const params = { type };
      if (selectedLevel) params.level = selectedLevel;
      const r = await axios.get('/api/leaderboard', { params });
      setData(r.data.leaderboard);
    } catch (err) {
      console.error('Failed to fetch leaderboard', err);
    } finally {
      setLoading(false);
    }
  };

  const shareLeaderboard = () => {
    const url = `${window.location.origin}/leaderboard?promoter=${user?.id || ''}&ref=leaderboard_page`;
    const text = `🎯 Brand to Stock!\nCheck out the Nifty stocks leaderboard. See who's leading the pack!\n\nView here: ${url}`;

    if (navigator.share) {
      navigator.share({ title: 'InvestBrand Leaderboard', text: text, url: url });
    } else {
      navigator.clipboard.writeText(text);
      alert('Leaderboard link copied to clipboard!');
    }
  };

  const userLevel = user ? getVirtuosoLevel(user.streak).name : null;

  return (
    <div className='min-h-screen bg-slate-900 p-4 md:p-6'>
      <div className='max-w-4xl mx-auto'>
        <div className='flex flex-col md:flex-row items-center justify-between gap-4 mb-8'>
          <h1 className='text-white text-3xl font-black flex items-center gap-3'>
            <Trophy className='text-yellow-400' size={32} />
            Leaderboard
          </h1>
          <button
            onClick={shareLeaderboard}
            className='bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-full font-bold flex items-center gap-2 transition-all shadow-lg active:scale-95'
          >
            <Share2 size={18} /> Share
          </button>
        </div>

        {/* Filters */}
        <div className='flex flex-wrap gap-2 mb-6 bg-slate-800/50 p-2 rounded-2xl border border-slate-700'>
          {['all-time', 'weekly', 'daily'].map(t => (
            <button
              key={t}
              onClick={() => { setType(t); setSelectedLevel(null); }}
              className={`px-4 py-2 rounded-xl text-sm font-bold capitalize transition-all ${type === t && !selectedLevel ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-400 hover:text-white'}`}
            >
              {t.replace('-', ' ')}
            </button>
          ))}
        </div>

        {/* Virtuoso Levels - Simple Selection */}
        <div className='mb-8'>
          <div className='text-xs font-black text-slate-500 uppercase tracking-widest mb-3 pl-1'>Leaderboard View</div>
          <div className='flex flex-wrap gap-2'>
            <button
              onClick={() => setSelectedLevel(null)}
              className={`px-4 py-2 rounded-xl text-sm font-bold transition-all border ${!selectedLevel ? 'bg-white text-slate-900 border-white shadow-lg scale-105' : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'}`}
            >
              Global
            </button>
            {user && (() => {
              const level = getVirtuosoLevel(user.streak);
              return (
                <button
                  onClick={() => { setSelectedLevel(level.name); setType('all-time'); }}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all border ${selectedLevel === level.name ? 'bg-white text-slate-900 border-white shadow-lg scale-105' : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-white'}`}
                >
                  {level.image && <img src={level.image} alt='' className='w-4 h-4 object-contain' />}
                  My Rank ({level.name})
                </button>
              );
            })()}
          </div>
        </div>

        {/* Leaderboard Table */}
        <div className='bg-slate-800 rounded-3xl border border-slate-700 shadow-2xl overflow-hidden'>
          {loading ? (
            <div className='p-12 text-center text-slate-500 font-bold'>Loading rankings...</div>
          ) : data.length > 0 ? (
            <div className='divide-y divide-slate-700/50'>
              {data.map((u, i) => {
                const level = getVirtuosoLevel(u.streak);
                return (
                  <div key={u.id} className={`flex items-center gap-4 px-6 py-4 hover:bg-slate-700/30 transition-colors ${user?.id === u.id ? 'bg-indigo-600/10' : ''}`}>
                    <div className='w-8 font-black text-slate-500'>
                      {i === 0 ? <Trophy size={20} className='text-yellow-400' /> : i === 1 ? <Trophy size={20} className='text-slate-300' /> : i === 2 ? <Trophy size={20} className='text-amber-600' /> : `#${i + 1}`}
                    </div>
                    <div className='relative'>
                      <img src={u.avatar_url || `https://ui-avatars.com/api/?name=${u.name}&background=random`} alt={u.name} className='w-12 h-12 rounded-2xl shadow-md border-2 border-slate-700' />
                      {level.image && (
                        <div className='absolute -bottom-1 -right-1 w-5 h-5 bg-slate-900 rounded-full p-0.5 border border-slate-700'>
                          <img src={level.image} alt={level.name} className='w-full h-full object-contain' />
                        </div>
                      )}
                    </div>
                    <div className='flex-1 min-w-0'>
                      <div className='text-white font-bold flex items-center gap-2 truncate'>
                        {u.name}
                        {user?.id === u.id && <span className='text-[10px] bg-indigo-600 text-white px-2 py-0.5 rounded-full'>YOU</span>}
                      </div>
                      <div className={`text-[10px] font-black uppercase tracking-tighter ${level.color}`}>{level.name}</div>
                    </div>
                    <div className='text-right'>
                      <div className='text-indigo-400 font-black text-lg'>{u.score.toLocaleString()}</div>
                      <div className='text-[10px] text-slate-500 font-bold uppercase'>{u.streak}d streak</div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className='p-12 text-center text-slate-500 font-bold'>No players found in this tier yet.</div>
          )}
        </div>
      </div>
    </div>
  );
}

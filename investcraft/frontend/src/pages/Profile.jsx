import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Trophy, Flame } from 'lucide-react';
export default function Profile() {
  const [p, setP] = useState(null);
  useEffect(() => { axios.get('/api/users/me').then(r => setP(r.data)); }, []);
  if (!p) return <div className='flex items-center justify-center h-screen text-white'>Loading...</div>;
  return (
    <div className='min-h-screen bg-slate-900 p-6'><div className='max-w-2xl mx-auto'><div className='bg-slate-800 rounded-2xl p-8 border border-slate-700 text-center'>{p.avatar&&<img src={p.avatar} alt={p.name} className='w-24 h-24 rounded-full mx-auto mb-4'/>}<h1 className='text-white text-3xl font-bold mb-2'>{p.name}</h1><p className='text-slate-400 mb-6'>{p.email}</p><div className='grid grid-cols-3 gap-4'><div className='bg-slate-900 rounded-lg p-4'><Trophy size={24} className='text-indigo-400 mx-auto mb-2'/><div className='text-2xl text-white font-bold'>{p.score}</div><div className='text-slate-400 text-sm'>Score</div></div><div className='bg-slate-900 rounded-lg p-4'><Flame size={24} className='text-orange-400 mx-auto mb-2'/><div className='text-2xl text-white font-bold'>{p.streak}</div><div className='text-slate-400 text-sm'>Streak</div></div><div className='bg-slate-900 rounded-lg p-4'><div className='text-2xl text-white font-bold'>{p.puzzlesCompleted}</div><div className='text-slate-400 text-sm'>Solved</div></div></div></div></div></div>
  );
}

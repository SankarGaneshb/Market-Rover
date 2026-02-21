import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Trophy } from 'lucide-react';
export default function Leaderboard() {
  const [data, setData] = useState([]);
  useEffect(() => { axios.get('/api/leaderboard?type=all-time').then(r => setData(r.data.leaderboard)); }, []);
  return (
    <div className='min-h-screen bg-slate-900 p-6'><div className='max-w-2xl mx-auto'><h1 className='text-white text-3xl font-bold mb-6 text-center'>Leaderboard</h1><div className='bg-slate-800 rounded-xl border border-slate-700'>{data.map((u,i)=>(<div key={u.id} className='flex items-center gap-4 px-6 py-4 border-b border-slate-700 last:border-0'><div className='w-8'>{i===0?<Trophy size={18} className='text-yellow-400'/>:'#'+(i+1)}</div>{u.avatar_url&&<img src={u.avatar_url} alt={u.name} className='w-10 h-10 rounded-full'/>}<div className='flex-1'><div className='text-white font-medium'>{u.name}</div></div><div className='text-indigo-400 font-bold'>{u.score}</div></div>))}</div></div></div>
  );
}

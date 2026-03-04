#!/bin/bash
set -e
BASE="investcraft/frontend/src/pages"
mkdir -p $BASE

cat > $BASE/Leaderboard.jsx << 'HEREDOC'
import React,{useState,useEffect}from'react';
import axios from'axios';
import{Trophy,Medal,Flame}from'lucide-react';
const TABS=['all-time','weekly','daily'];
const medal=i=>i===0?<Trophy size={18} className="text-yellow-400"/>:i===1?<Medal size={18} className="text-slate-300"/>:i===2?<Medal size={18} className="text-amber-600"/>:<span className="text-slate-500 w-5 text-center text-sm">{i+1}</span>;
export default function Leaderboard(){
  const[data,setData]=useState([]);
  const[tab,setTab]=useState('all-time');
  const[loading,setLoading]=useState(true);
  useEffect(()=>{
    setLoading(true);
    axios.get(`/api/leaderboard?type=${tab}`).then(r=>setData(r.data.leaderboard)).finally(()=>setLoading(false));
  },[tab]);
  return(
    <div className="min-h-screen bg-slate-900 px-4 py-10 max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-8">
        <Trophy size={32} className="text-yellow-400"/>
        <h1 className="text-white text-3xl font-black">Leaderboard</h1>
      </div>
      <div className="flex gap-2 mb-6">
        {TABS.map(t=>(
          <button key={t} onClick={()=>setTab(t)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium capitalize transition ${tab===t?'bg-indigo-600 text-white':'bg-slate-800 text-slate-400 hover:text-white'}`}>
            {t}
          </button>
        ))}
      </div>
      {loading?(
        <div className="text-slate-400 text-center py-20">Loading...</div>
      ):(
        <div className="space-y-3">
          {data.map((u,i)=>(
            <div key={u.id} className={`flex items-center gap-4 p-4 rounded-xl border ${i===0?'border-yellow-500 bg-yellow-900/10':i===1?'border-slate-500 bg-slate-800/50':i===2?'border-amber-700 bg-amber-900/10':'border-slate-700 bg-slate-800/30'}`}>
              <div className="flex items-center justify-center w-8">{medal(i)}</div>
              {u.avatar_url&&<img src={u.avatar_url} alt="" className="w-9 h-9 rounded-full"/>}
              <div className="flex-1">
                <p className="text-white font-semibold text-sm">{u.name}</p>
                {u.streak>0&&<p className="text-orange-400 text-xs flex items-center gap-1"><Flame size={11}/>{u.streak} day streak</p>}
              </div>
              <span className="text-indigo-400 font-bold">{u.score?.toLocaleString()} pts</span>
            </div>
          ))}
          {data.length===0&&<p className="text-slate-500 text-center py-10">No data yet. Be the first!</p>}
        </div>
      )}
    </div>
  );
}
HEREDOC
echo "✅ Leaderboard.jsx created"

#!/bin/bash
set -e
BASE="investcraft/frontend/src/pages"
mkdir -p $BASE

cat > $BASE/Puzzle.jsx << 'HEREDOC'
import React,{useState,useEffect,useCallback}from'react';
import axios from'axios';
import{Clock,Lightbulb,RotateCcw,CheckCircle}from'lucide-react';
const G=4,S=320,C=S/G;
const shuf=a=>{const b=[...a];for(let i=b.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[b[i],b[j]]=[b[j],b[i]];}return b;};
const fmt=s=>`${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;
export default function Puzzle(){
  const[puzzle,set0]=useState(null);
  const[pieces,set1]=useState([]);
  const[sel,setSel]=useState(null);
  const[moves,setM]=useState(0);
  const[time,setT]=useState(0);
  const[solved,setSolved]=useState(false);
  const[hint,setHint]=useState(false);
  const[score,setScore]=useState(0);
  useEffect(()=>{axios.get('/api/puzzles/daily').then(r=>{set0(r.data);set1(shuf([...Array(G*G)].map((_,i)=>({id:i,correct:i}))));});},[]);
  useEffect(()=>{if(solved||!puzzle)return;const t=setInterval(()=>setT(s=>s+1),1000);return()=>clearInterval(t);},[solved,puzzle]);
  const ok=useCallback(p=>p.every((x,i)=>x.correct===i),[]);
  const click=idx=>{
    if(solved)return;
    if(sel===null){setSel(idx);return;}
    if(sel===idx){setSel(null);return;}
    const n=[...pieces];[n[sel],n[idx]]=[n[idx],n[sel]];
    const m=moves+1;setM(m);set1(n);setSel(null);
    if(ok(n)){const s=Math.max(100,1000-m*10-time);setScore(s);setSolved(true);axios.post(`/api/puzzles/${puzzle.id}/complete`,{score:s,movesUsed:m,timeTaken:time}).catch(()=>{});}
  };
  const reset=()=>{set1(shuf([...Array(G*G)].map((_,i)=>({id:i,correct:i}))));setM(0);setT(0);setSolved(false);setSel(null);};
  if(!puzzle)return<div className="flex items-center justify-center h-screen text-white">Loading...</div>;
  return(
    <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center p-6">
      <h2 className="text-white text-2xl font-bold mb-1">Today's Puzzle</h2>
      <p className="text-slate-400 text-sm mb-5">Sector: <span className="text-indigo-400">{puzzle.sector}</span> · {'⭐'.repeat(puzzle.difficulty)}</p>
      <div className="flex gap-6 mb-5 text-slate-300 text-sm">
        <span className="flex items-center gap-1"><Clock size={14}/>{fmt(time)}</span>
        <span>Moves:{moves}</span>
        <button onClick={()=>setHint(v=>!v)} className="text-yellow-400 flex items-center gap-1"><Lightbulb size={14}/>Hint</button>
        <button onClick={reset} className="flex items-center gap-1 hover:text-white"><RotateCcw size={14}/>Reset</button>
      </div>
      {hint&&<p className="text-yellow-300 mb-4 text-sm border border-yellow-700 px-4 py-2 rounded-lg">{puzzle.hint}</p>}
      {solved?(
        <div className="text-center bg-slate-800 rounded-2xl p-10 border border-green-500">
          <CheckCircle size={60} className="text-green-400 mx-auto mb-4"/>
          <h3 className="text-white text-3xl font-black">{puzzle.company_name}</h3>
          <p className="text-slate-400 text-sm">({puzzle.ticker})</p>
          <p className="text-3xl text-indigo-400 font-bold mt-4">+{score} pts</p>
          <button onClick={reset} className="mt-6 bg-indigo-600 text-white px-6 py-2 rounded-lg text-sm">Play Again</button>
        </div>
      ):(
        <div style={{width:S,height:S}} className="relative border-2 border-slate-600 rounded-xl overflow-hidden">
          {pieces.map((p,i)=>{
            const r=Math.floor(p.correct/G),c=p.correct%G;
            return<div key={p.id} onClick={()=>click(i)} style={{position:'absolute',left:(i%G)*C,top:Math.floor(i/G)*C,width:C,height:C,backgroundImage:`url(${puzzle.logo_url})`,backgroundSize:`${S}px ${S}px`,backgroundPosition:`-${c*C}px -${r*C}px`,border:sel===i?'3px solid #6366f1':'1px solid rgba(255,255,255,0.1)',cursor:'pointer'}}/>;
          })}
        </div>
      )}
    </div>
  );
}
HEREDOC
echo "✅ Puzzle.jsx created"

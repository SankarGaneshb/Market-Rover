import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Clock, CheckCircle } from 'lucide-react';
const G=4,S=320,C=S/G;
const shuffle=a=>{const x=[...a];for(let i=x.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[x[i],x[j]]=[x[j],x[i]];}return x;};
export default function Puzzle() {
  const [p,setP]=useState(null);const [pc,setPc]=useState([]);const [sel,setSel]=useState(null);const [mv,setMv]=useState(0);
  const [t,setT]=useState(0);const [done,setDone]=useState(false);const [sc,setSc]=useState(0);
  useEffect(()=>{axios.get('/api/puzzles/daily').then(r=>{setP(r.data);setPc(shuffle([...Array(G*G)].map((_,i)=>({id:i,c:i}))));});},[]);
  useEffect(()=>{if(done||!p)return;const x=setInterval(()=>setT(s=>s+1),1000);return()=>clearInterval(x);},[done,p]);
  const isSolved=a=>a.every((x,i)=>x.c===i);
  const click=i=>{if(done)return;if(sel===null){setSel(i);return;}if(sel===i){setSel(null);return;}const n=[...pc];[n[sel],n[i]]=[n[i],n[sel]];const m=mv+1;setMv(m);setPc(n);setSel(null);if(isSolved(n)){const s=Math.max(100,1000-m*10-t);setSc(s);setDone(true);axios.post('/api/puzzles/'+p.id+'/complete',{score:s,movesUsed:m,timeTaken:t}).catch(()=>{});}};
  if(!p)return <div className='flex items-center justify-center h-screen text-white'>Loading...</div>;
  return(<div className='min-h-screen bg-slate-900 flex flex-col items-center justify-center p-6'><h2 className='text-white text-2xl font-bold mb-5'>{p.sector}</h2>{done?<div className='text-center bg-slate-800 rounded-2xl p-10 border border-green-500'><CheckCircle size={60} className='text-green-400 mx-auto mb-4'/><h3 className='text-white text-3xl font-bold'>{p.company_name}</h3><p className='text-3xl text-indigo-400 font-bold mt-5'>+{sc}</p></div>:<div style={{width:S,height:S}} className='relative border-2 border-slate-600 rounded-xl overflow-hidden'>{pc.map((piece,idx)=>{const row=Math.floor(piece.c/G),col=piece.c%G;return(<div key={piece.id} onClick={()=>click(idx)} style={{position:'absolute',left:(idx%G)*C,top:Math.floor(idx/G)*C,width:C,height:C,backgroundImage:'url('+p.logo_url+')',backgroundSize:S+'px '+S+'px',backgroundPosition:'-'+(col*C)+'px -'+(row*C)+'px',border:sel===idx?'3px solid #6366f1':'1px solid rgba(255,255,255,0.1)',cursor:'pointer'}}/>);})}</div>}</div>);
}

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Trophy, Flame, CheckCircle, Target, TrendingUp, Award, Star, Info } from 'lucide-react';
import { VIRTUOSO_LEVELS, getVirtuosoLevel, getNextVirtuosoLevel } from '../data/virtuoso';
import GlitterBadge from '../components/GlitterBadge';

export default function Profile() {
  const [p, setP] = useState(null);

  useEffect(() => {
    axios.get('/api/users/me')
      .then(r => setP(r.data))
      .catch(err => console.error('Failed to fetch profile:', err));
  }, []);

  if (!p) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-pulse text-indigo-400 font-bold flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
          Loading Profile...
        </div>
      </div>
    );
  }

  const currentLevel = getVirtuosoLevel(p.streak);
  const nextLevel = getNextVirtuosoLevel(p.streak);

  return (
    <div className="w-full bg-[#030014] overflow-hidden flex flex-col p-2 lg:p-4 relative text-white" style={{ height: "calc(100vh - 72px)" }}>
      {/* Animated Ultra-Vibrant Mesh Background - SUPERCHARGED & DEEP */}
      <div className="absolute inset-0 z-0 opacity-50 pointer-events-none transform scale-110">
        <div className="absolute top-[-20%] left-[-10%] w-[80vw] h-[80vw] rounded-full bg-indigo-600/30 blur-[150px] mix-blend-screen animate-blob" />
        <div className="absolute top-[30%] right-[-10%] w-[70vw] h-[70vw] rounded-full bg-fuchsia-600/20 blur-[150px] mix-blend-screen animate-blob animation-delay-2000" />
        <div className="absolute bottom-[-30%] left-[20%] w-[90vw] h-[90vw] rounded-full bg-cyan-600/20 blur-[150px] mix-blend-screen animate-blob animation-delay-4000" />
      </div>

      <div className="max-w-[1600px] mx-auto w-full flex flex-col h-full gap-4 relative z-10">
        {/* COMPACT PILOT HUD */}
        <div className="flex-shrink-0 bg-[#0a0c16]/80 backdrop-blur-3xl rounded-[2rem] p-3 lg:p-4 shadow-[0_20px_40px_-10px_rgba(0,0,0,1),inset_0_1px_1px_rgba(255,255,255,0.2)] border-t border-l border-white/20 border-b border-r border-black/80 flex flex-col md:flex-row items-center justify-between gap-4 h-auto md:h-[12vh] min-h-[90px] relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 via-transparent to-cyan-500/10 opacity-50 pointer-events-none" />

          <div className="flex items-center gap-4 relative z-10 w-full md:w-auto">
            <div className="relative flex-shrink-0">
              {p.avatar ? (
                <div className="relative">
                  <div className="absolute inset-0 bg-cyan-400 rounded-2xl blur-lg opacity-40 animate-pulse" />
                  <img src={p.avatar} alt={p.name} className="w-14 h-14 md:w-16 md:h-16 rounded-2xl shadow-[0_5px_15px_rgba(0,0,0,0.8)] border border-white/30 p-0.5 relative z-10 bg-slate-900 object-cover" />
                </div>
              ) : (
                <div className="w-14 h-14 md:w-16 md:h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-xl font-black text-white shadow-lg">
                  {p.name?.[0]}
                </div>
              )}
            </div>
            <div className="flex flex-col justify-center flex-1 min-w-0">
              <h1 className="text-white text-xl md:text-2xl font-black truncate tracking-tighter drop-shadow-md">{p.name}</h1>
              <p className="text-cyan-200/60 font-bold text-[10px] md:text-xs truncate tracking-wider">{p.email}</p>
            </div>
          </div>

          <div className="flex items-center gap-2 md:gap-4 relative z-10 w-full md:w-auto overflow-x-auto no-scrollbar pb-1 md:pb-0 hide-scroll">
            <StatCard icon={<Flame className="text-orange-400 drop-shadow-[0_0_8px_rgba(251,146,60,1)]" size={14} />} value={p.streak} label="Streak" unit="d" />
            <StatCard icon={<CheckCircle className="text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,1)]" size={14} />} value={p.puzzlesCompleted} label="Solved" />
            <StatCard icon={<Trophy className="text-yellow-400 drop-shadow-[0_0_8px_rgba(250,204,21,1)]" size={14} />} value={p.score} label="Total" />
            <div className="bg-[#0f1219]/40 px-3 lg:px-4 py-2 rounded-2xl flex items-center gap-3 border border-white/10 shadow-[0_10px_30px_rgba(0,0,0,0.5),inset_0_1px_1px_rgba(255,255,255,0.05)] backdrop-blur-md flex-shrink-0 group/rank transition-all hover:bg-[#0f1219]/60">
              <div className="flex-shrink-0 transition-transform duration-500 group-hover/rank:scale-110">
                <GlitterBadge size="small" icon={currentLevel.icon} name={currentLevel.name} levelConfig={currentLevel} />
              </div>
              <div className="flex flex-col justify-center min-w-0 pr-1">
                <div className="flex flex-col -gap-1">
                  <span className="text-[12px] lg:text-[14px] font-black text-white uppercase tracking-tighter leading-tight drop-shadow-md whitespace-nowrap">
                    {currentLevel.name.split(' ')[0]}
                  </span>
                  <span className="text-[7px] lg:text-[8px] font-black text-cyan-400 uppercase tracking-[0.3em] leading-none mb-1">
                    VIRTUOSO
                  </span>
                </div>
                {nextLevel && (
                  <div className="mt-1 flex flex-col gap-0.5">
                    <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden border border-white/5">
                      <div
                        className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.5)] transition-all duration-1000"
                        style={{ width: `${Math.min(100, (p.streak / nextLevel.minDays) * 100)}%` }}
                      />
                    </div>
                    <span className="text-[6px] lg:text-[7px] text-white/30 font-bold uppercase tracking-wider whitespace-nowrap">
                      {nextLevel.minDays - p.streak} DAYS TO {nextLevel.name.split(' ')[0]}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* MAJESTIC 7-COLUMN HERO CARD ROADMAP */}
        <div className="flex-1 min-h-0 bg-[#0a0c16]/50 backdrop-blur-3xl rounded-[2.5rem] p-4 lg:p-6 lg:pb-8 shadow-[20px_20px_60px_-15px_rgba(0,0,0,0.8),inset_0_1px_1px_rgba(255,255,255,0.2)] border-t border-l border-white/20 border-b border-r border-black/80 relative overflow-hidden flex flex-col">
          <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-cyan-400/80 to-transparent shadow-[0_0_30px_rgba(34,211,238,1)]" />

          <div className="flex items-center justify-between mb-4 flex-shrink-0 relative z-10">
            <h2 className="text-2xl md:text-3xl font-black text-white flex items-center gap-3 drop-shadow-[0_4px_10px_rgba(0,0,0,0.8)] tracking-tight uppercase">
              <TrendingUp className="text-cyan-400 drop-shadow-[0_0_15px_rgba(34,211,238,1)] animate-pulse" size={28} /> Mastery Path
            </h2>
            <div className="px-5 py-2 rounded-xl bg-[#0a0c16]/80 border-t border-l border-white/20 border-b border-r border-black/80 text-cyan-400 text-[10px] md:text-[11px] font-black uppercase tracking-[0.3em] shadow-[5px_5px_15px_rgba(0,0,0,0.5),inset_0_1px_1px_rgba(255,255,255,0.1)]">
              Unlock by Streak
            </div>
          </div>

          <div className="flex-1 overflow-x-auto overflow-y-hidden hide-scroll hide-scrollbar w-full relative z-10 pb-4 lg:pb-0 h-full">
            <div className="flex lg:grid lg:grid-cols-7 gap-3 lg:gap-4 h-full min-w-max lg:min-w-0 pt-2 lg:pt-4">
              {VIRTUOSO_LEVELS.map((level, idx) => {
                const isLocked = p.streak < level.minDays;
                const isCurrent = currentLevel.name === level.name;

                return (
                  <div
                    key={idx}
                    className={`relative w-[280px] lg:w-auto h-full rounded-3xl transition-all duration-700 overflow-hidden group/hero flex flex-col justify-between ${isLocked
                      ? 'bg-[#050608]/90 border-t border-l border-white/5 border-b-2 border-r-2 border-black shadow-[15px_15px_30px_-10px_rgba(0,0,0,0.9)] opacity-90'
                      : `bg-[#0f1219]/90 border-t-2 border-l-2 border-white/30 border-b-2 border-r-2 border-black/80 shadow-[20px_20px_50px_-10px_rgba(0,0,0,0.9),inset_0_2px_4px_rgba(255,255,255,0.2)] hover:-translate-y-4 hover:scale-[1.03] hover:bg-[#151923] hover:border-white/50 hover:shadow-[30px_40px_80px_-20px_rgba(0,0,0,1),0_0_80px_${level.accent}33] z-10 hover:z-30 cursor-pointer`
                      } ${isCurrent ? `ring-2 ring-[${level.accent}] ring-offset-4 ring-offset-[#0a0c16] shadow-[20px_30px_70px_rgba(0,0,0,1),0_0_100px_${level.accent}44] -translate-y-2 lg:-translate-y-3 z-20` : ''}`}
                  >
                    {/* Deep Cinematic Spotlight */}
                    <div
                      className={`absolute -top-1/4 -right-1/4 w-[150%] h-[150%] blur-[100px] rounded-full opacity-0 group-hover/hero:opacity-60 transition-opacity duration-1000 mix-blend-screen pointer-events-none`}
                      style={{ backgroundColor: level.accent }}
                    />

                    {isCurrent && (
                      <div className="absolute top-4 right-4 bg-white text-black text-[9px] font-black px-3 py-1.5 rounded-full shadow-[0_5px_15px_rgba(255,255,255,0.8)] uppercase tracking-[0.2em] z-30 animate-pulse border border-black/10">
                        Current
                      </div>
                    )}

                    {/* Massive Display Area */}
                    <div className="flex-1 flex flex-col items-center justify-center relative z-20 w-full px-2 pt-8 pb-4 group-hover/hero:scale-[1.1] transition-transform duration-700 ease-out h-[60%] lg:h-[70%]">
                      <div className="relative w-full h-full flex items-center justify-center mb-4 drop-shadow-[0_20px_40px_rgba(0,0,0,0.9)]">
                        <div
                          className="absolute inset-x-0 inset-y-10 blur-3xl opacity-60 mix-blend-screen"
                          style={{ background: `radial-gradient(circle, ${level.accent}, transparent 70%)` }}
                        />

                        {level.image ? (
                          <img
                            src={level.image}
                            alt={level.name}
                            className={`w-full h-full object-contain relative z-20 transform transition-all duration-700 ${isLocked ? 'saturate-0 brightness-50 contrast-125 mix-blend-luminosity' : 'group-hover/hero:brightness-125 group-hover/hero:drop-shadow-[0_0_30px_rgba(255,255,255,0.8)]'}`}
                            style={!isLocked ? { filter: `drop-shadow(0 20px 30px rgba(0,0,0,0.8)) drop-shadow(0 0 20px ${level.accent}88)` } : { filter: `drop-shadow(0 15px 20px rgba(0,0,0,1))` }}
                          />
                        ) : (
                          <div className={`w-28 h-28 ${level.color} relative z-20`}>
                            <svg viewBox="0 0 24 24" className="w-full h-full fill-current drop-shadow-[0_15px_25px_rgba(0,0,0,0.9)]">
                              <path d={level.icon} />
                            </svg>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-col items-center w-full mt-auto flex-shrink-0">
                        <h3 className={`font-black text-2xl lg:text-3xl xl:text-4xl tracking-tighter text-center leading-none drop-shadow-[0_5px_10px_rgba(0,0,0,1)] transition-colors duration-500 mb-2 ${isLocked ? 'text-slate-600' : 'text-white'}`}>
                          {level.name.split(' ')[0]}
                        </h3>
                        <div className={`text-[9px] lg:text-[11px] font-black uppercase tracking-[0.3em] ${isLocked ? 'text-white/10' : 'text-cyan-400/80'}`}>
                          VIRTUOSO
                        </div>
                      </div>
                    </div>

                    {/* Bottom Info Bar - Fills bottom */}
                    <div className="relative z-20 w-full p-4 flex flex-col items-center bg-black/40 backdrop-blur-md border-t border-white/5 flex-shrink-0">
                      <div className="text-[9px] lg:text-[10px] font-black uppercase text-indigo-200/50 tracking-[0.3em] mb-2">
                        {level.minDays} Days Req
                      </div>
                      {isLocked ? (
                        <div className="w-full text-center text-[10px] font-black text-white/40 bg-black/60 border border-white/5 py-2.5 rounded-xl shadow-[inset_0_2px_4px_rgba(0,0,0,1)] tracking-widest uppercase truncate px-2">
                          {level.minDays - p.streak} Days Left
                        </div>
                      ) : (
                        <div className="w-full text-center text-[10px] font-black text-[#00ff9f] bg-[#00ff9f]/5 border border-[#00ff9f]/30 py-2.5 rounded-xl shadow-[0_5px_15px_rgba(0,255,159,0.1),inset_0_1px_1px_rgba(255,255,255,0.1)] tracking-widest uppercase">
                          Unlocked
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      <style dangerouslySetInnerHTML={{
        __html: `
          /* GUARANTEED ZERO SCROLLBAR: Force layout strictly visually */
          * { -ms-overflow-style: none; scrollbar-width: none; }
          *::-webkit-scrollbar { display: none !important; }
          body, html { overflow: hidden !important; height: 100vh !important; margin: 0; padding: 0; }
          
          /* Utility hide scroll for inner flex containers */
          .hide-scroll {
            -ms-overflow-style: none; 
            scrollbar-width: none; 
          }
          .hide-scroll::-webkit-scrollbar { 
            display: none !important; 
          }
          
          /* Animated Mesh Gradient Blobs */
          @keyframes blob {
            0% { transform: translate(0px, 0px) scale(1); }
            33% { transform: translate(30px, -50px) scale(1.1); }
            66% { transform: translate(-20px, 20px) scale(0.9); }
            100% { transform: translate(0px, 0px) scale(1); }
          }
          .animate-blob {
            animation: blob 15s infinite alternate ease-in-out;
          }
          .animation-delay-2000 { animation-delay: 2s; }
          .animation-delay-4000 { animation-delay: 4s; }
        `}} />
    </div>
  );

}

function StatCard({ icon, value, label, unit }) {
  return (
    <div className="flex items-center gap-2.5 bg-white/5 px-3 py-2.5 rounded-2xl border border-white/5 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)] transition-colors hover:bg-white/10">
      <div className="p-1.5 bg-white/10 rounded-lg flex-shrink-0 shadow-lg">{icon}</div>
      <div className="text-left min-w-0">
        <div className="text-white text-base font-black leading-none whitespace-nowrap drop-shadow-md">
          {value}{unit && <span className="text-[9px] ml-0.5 opacity-50 uppercase">{unit}</span>}
        </div>
        <div className="text-indigo-200/60 text-[9px] font-black uppercase tracking-tighter mt-0.5">{label}</div>
      </div>
    </div>
  );
}
